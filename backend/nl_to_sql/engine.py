# backend/nl_to_sql/engine.py

from typing import Dict, Any
import logging

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.db_queries import run_query
from .generation import generate_sql_from_question, _get_table_columns
from .explanation import explain_results

logger = logging.getLogger(__name__)

# You can tweak this if you want a different model for repair
LLM_MODEL_FOR_REPAIR = "gpt-4.1-mini"


def _strip_sql_from_response(text: str) -> str:
    text = text.strip()

    # Try ```sql ... ``` fenced code block
    lower = text.lower()
    if "```sql" in lower:
        start = lower.find("```sql")
        if start != -1:
            start = text.find("```sql") + len("```sql")
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

    # Generic ``` ... ``` with optional "sql"
    if text.startswith("```"):
        stripped = text.strip("`")
        if stripped.lower().startswith("sql"):
            stripped = stripped[3:]
        return stripped.strip()

    return text


def repair_sql(question: str, bad_sql: str, error_message: str) -> str:
    """
    Ask the LLM to *fix* a broken DuckDB SQL query, given the original
    question, the bad SQL, the error message, and the real DB schemas.
    """
    load_dotenv()

    # Get actual schemas so the model sees the truth
    table_names = [
        "qb_season_stats",
        "wr_season_stats",
        "qb_wr_season_stats",
        "qb_game_stats",
        "wr_game_stats",
        "qb_wr_game_stats",
    ]
    schemas = _get_table_columns(table_names)
    schema_chunks: list[str] = []
    for t in table_names:
        cols = schemas.get(t, [])
        schema_chunks.append(f"{t}: {', '.join(cols) if cols else '(no columns found)'}")
    schema_text = "\n".join(schema_chunks)

    system_prompt = (
        "You are a DuckDB SQL repair assistant for an NFL stats warehouse.\n\n"
        "You will be given:\n"
        "- the original natural-language question\n"
        "- the broken SQL query you previously wrote\n"
        "- the DuckDB error message\n"
        "- the exact schemas of the available tables\n\n"
        "Your job is to return a NEW SQL query that:\n"
        "- fixes the error\n"
        "- uses ONLY the existing tables and columns\n"
        "- still answers the user's original question as best as possible\n"
        "- does NOT include any explanation, just the SQL.\n\n"
        "Available tables (do not invent others):\n"
        "  qb_season_stats, wr_season_stats, qb_wr_season_stats,\n"
        "  qb_game_stats, wr_game_stats, qb_wr_game_stats.\n\n"
        "Avoid over-complicated correlated subqueries if they cause alias issues; "
        "window functions (e.g. AVG(...) OVER (PARTITION BY ...)) are often simpler."
    )

    user_prompt = f"""
        Original user question:
        \"\"\"{question}\"\"\"

        Broken SQL:
        ```sql
        {bad_sql}
        ```

        DuckDB error message:
        \"\"\"{error_message}\"\"\"

        Exact table schemas (from DuckDB):
        {schema_text}

        Instructions:

        - Return ONLY a single corrected SQL query.
        - Use only existing columns from the schemas above.
        - It is OK to rewrite the query to use a window function instead of a correlated subquery
        if that reduces alias problems.
        - Do NOT include any natural-language explanation.
        """

    llm = ChatOpenAI(model=LLM_MODEL_FOR_REPAIR, temperature=0.0)

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    text = response.content.strip()
    return _strip_sql_from_response(text)


def answer_question(question: str) -> Dict[str, Any]:
    logger.info("answer_question called")
    logger.debug("question: %s", question)

    # 1) Let the LLM generate SQL
    sql = generate_sql_from_question(question)
    logger.info("Initial SQL: %s", sql)

    # 2) Try to execute it
    try:
        df = run_query(sql)
        logger.info(
            "SQL executed successfully. Rows: %d, Columns: %d",
            df.shape[0],
            df.shape[1],
        )
        logger.debug("Columns returned: %s", list(df.columns))
    except Exception as e:
        logger.exception("Error executing SQL; attempting LLM repair. Error: %s", e)
        # 3) Ask the LLM to repair the SQL using the error message
        repaired_sql = repair_sql(question, sql, str(e))
        logger.info("Repaired SQL: %s", repaired_sql)

        # 4) Try executing repaired SQL
        df = run_query(repaired_sql)
        logger.info(
            "Repaired SQL executed successfully. Rows: %d, Columns: %d",
            df.shape[0],
            df.shape[1],
        )
        logger.debug("Columns returned (repaired): %s", list(df.columns))
        sql = repaired_sql  # use the working SQL in the final answer

    # 5) Hide internal player ID columns from the user-facing output
    id_columns_to_hide = [
        c for c in df.columns if c in {"player_id", "qb_id", "wr_id"}
    ]
    if id_columns_to_hide:
        logger.info("Hiding ID columns from output: %s", id_columns_to_hide)
        df = df.drop(columns=id_columns_to_hide)

    # 6) Convert rows + round floats
    rows = df.to_dict(orient="records")

    formatted_rows: list[Dict[str, Any]] = []
    for r in rows:
        new_r: Dict[str, Any] = {}
        for k, v in r.items():
            try:
                if isinstance(v, float):
                    new_r[k] = round(v, 3)
                else:
                    new_r[k] = v
            except Exception:
                new_r[k] = v
        formatted_rows.append(new_r)

    logger.debug(
        "First formatted row (if any): %s",
        formatted_rows[0] if formatted_rows else None,
    )

    # 7) Explanation
    explanation = explain_results(question, sql, formatted_rows)

    logger.info("answer_question completed: rows=%d", len(formatted_rows))

    return {
        "question": question,
        "sql": sql,
        "rows": formatted_rows,
        "explanation": explanation,
    }
