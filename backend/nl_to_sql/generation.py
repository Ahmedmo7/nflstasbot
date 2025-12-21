# backend/nl_to_sql/generation.py

from typing import Dict, Any, List
import logging
import re

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.db_queries import run_query
from backend.rag.retriever import get_relevant_docs

LLM_MODEL_FOR_SQL = "gpt-4.1-mini"

logger = logging.getLogger(__name__)


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


def _get_table_columns(table_names: List[str]) -> Dict[str, List[str]]:
    """Return a mapping table_name -> list of column names from DuckDB."""
    cols: Dict[str, List[str]] = {}
    for t in table_names:
        try:
            q = (
                "SELECT column_name "
                "FROM information_schema.columns "
                f"WHERE table_name = '{t}' "
                "ORDER BY ordinal_position;"
            )
            df = run_query(q)
            cols[t] = [r[0] for r in df.values.tolist()]
        except Exception:
            cols[t] = []
    return cols


def _qualify_sql(sql: str, schemas: Dict[str, List[str]]) -> tuple[str, list[tuple[str, str]]]:
    """Attempt to qualify unqualified column names using table aliases found in the SQL.

    Returns (new_sql, applied_qualifications) where applied_qualifications is list of (col, alias).
    """
    if not sql:
        return sql, []

    # Find table aliases from FROM/JOIN clauses: e.g. "qb_wr_season_stats qws"
    alias_map: Dict[str, str] = {}
    SQL_KEYWORDS_LOCAL = {
        "select",
        "from",
        "where",
        "and",
        "or",
        "order",
        "by",
        "group",
        "limit",
        "asc",
        "desc",
        "as",
        "join",
        "on",
        "inner",
        "left",
        "right",
        "full",
        "union",
        "all",
    }
    for m in re.finditer(
        r"\b(from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(?:as\s+)?([a-zA-Z_][a-zA-Z0-9_]*))?",
        sql,
        flags=re.IGNORECASE,
    ):
        table = m.group(2)
        alias = m.group(3)
        if not alias:
            continue
        if alias.lower() in SQL_KEYWORDS_LOCAL:
            # False positive like 'WHERE' captured as alias; skip
            continue
        alias_map[alias] = table

    if not alias_map:
        return sql, []

    # Build reverse map: table -> list of aliases
    table_aliases: Dict[str, List[str]] = {}
    for alias, table in alias_map.items():
        table_aliases.setdefault(table.lower(), []).append(alias)

    # Helper: check which referenced tables contain a column
    def tables_with_col(col: str) -> list[str]:
        found: list[str] = []
        for t, cols in schemas.items():
            if col.lower() in {c.lower() for c in cols}:
                # if table appears in alias_map (or is referenced), include
                if any(a for a, tt in alias_map.items() if tt.lower() == t.lower()):
                    found.append(t)
        return found

    applied: list[tuple[str, str]] = []
    new_sql = sql

    # Find simple unqualified identifiers that look like columns (ignore ones preceded by a dot)
    for m in re.finditer(r"(?<!\.)\b([a-zA-Z_][a-zA-Z0-9_]*)\b", sql):
        ident = m.group(1)
        lower_ident = ident.lower()
        # Skip SQL keywords and aliases
        if lower_ident in {
            "select",
            "from",
            "where",
            "and",
            "or",
            "order",
            "by",
            "group",
            "limit",
            "asc",
            "desc",
            "as",
            "join",
            "on",
            "inner",
            "left",
            "right",
            "full",
            "union",
            "all",
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "case",
            "when",
            "then",
            "else",
            "end",
            "cast",
            "using",
            "between",
            "in",
            "exists",
            "not",
            "null",
            "true",
            "false",
        }:
            continue
        # Skip if this ident is a known alias
        if ident in alias_map:
            continue

        # Check tables that have this column
        found_tables = tables_with_col(ident)
        if not found_tables:
            continue
        # Determine which alias to use: prefer first alias for the first matching table
        chosen_alias = None
        for t in found_tables:
            for a, tt in alias_map.items():
                if tt.lower() == t.lower():
                    chosen_alias = a
                    break
            if chosen_alias:
                break

        if not chosen_alias:
            continue

        # Replace unqualified occurrences of ident with alias.ident (but avoid already qualified)
        new_sql = re.sub(rf"(?<!\.)\b{ident}\b", f"{chosen_alias}.{ident}", new_sql)
        applied.append((ident, chosen_alias))

    return new_sql, applied


def generate_sql_from_question(question: str) -> str:
    """
    Use RAG + LLM to turn a natural language question into a DuckDB SQL query
    over the NFL stats warehouse.

    Available tables and their grains:

    1) qb_season_stats
       - One row per QB per season per team.

    2) wr_season_stats
       - One row per WR per season per team.

    3) qb_wr_season_stats
       - One row per QB-WR pair per season per team.

    4) qb_game_stats
       - One row per QB per game.

    5) wr_game_stats
       - One row per WR per game.

    6) qb_wr_game_stats
       - One row per QB-WR pair per game.
    """
    load_dotenv()

    logger.info("generate_sql_from_question called")
    logger.debug("question: %s", question)

    # 1) Retrieve relevant RAG docs to ground the LLM in schema/metrics
    docs = get_relevant_docs(question, k=6)
    context_chunks: list[str] = []
    for d in docs:
        logger.debug(
            "RAG doc used: filename=%s category=%s",
            d.metadata.get("filename"),
            d.metadata.get("category"),
        )
        context_chunks.append(
            f"Source: {d.metadata.get('filename')} (category={d.metadata.get('category')})\n"
            f"{d.page_content}"
        )
    context_text = "\n\n---\n\n".join(context_chunks)

    # 2) System prompt: define the world and tables very precisely
    system_prompt = (
        "You are an assistant that writes valid DuckDB SQL queries for an NFL stats warehouse.\n\n"
        "You have EXACTLY the following tables:\n\n"
        "1) qb_season_stats  -- one row per quarterback per season per team\n"
        "   Typical columns include: season, season_type, player_id, player_name, team, position, "
        "   dropbacks, attempts, completions, passing_yards, passing_tds, interceptions, "
        "   epa_total, epa_per_play, success_plays, success_rate, total_air_yards, "
        "   total_yac_yards, avg_air_yards, avg_yac_per_completion, air_epa_total, "
        "   yac_epa_total, air_epa_per_play, yac_epa_per_play, first_down_passes, "
        "   explosive_passes, third_down_attempts, third_down_conversions, "
        "   third_down_conversion_rate, red_zone_targets, red_zone_pass_tds.\n\n"
        "2) wr_season_stats  -- one row per receiver per season per team\n"
        "   Typical columns include: season, season_type, player_id, player_name, team, targets, "
        "   receptions, receiving_yards, receiving_tds, epa_total, epa_per_target, "
        "   success_plays, success_rate, total_air_yards, total_yac_yards, avg_air_yards, "
        "   avg_yac_per_reception, first_downs, explosive_plays, red_zone_targets, "
        "   red_zone_tds.\n\n"
        "3) qb_wr_season_stats  -- one row per QB-WR pair per season per team\n"
        "   Typical columns include: season, season_type, team, qb_id, qb_name, wr_id, wr_name, "
        "   targets, receptions, receiving_yards, receiving_tds, epa_total, "
        "   epa_per_target, success_plays, success_rate, total_air_yards, total_yac_yards, "
        "   avg_air_yards, avg_yac_per_reception, first_downs, explosive_plays, "
        "   red_zone_targets, red_zone_tds.\n\n"
        "4) qb_game_stats  -- one row per QB per game\n"
        "   Typical columns include: season, season_type, game_id, week, game_date, team, opponent_team, "
        "   qb_id, qb_name, dropbacks, attempts, completions, passing_yards, passing_tds, "
        "   interceptions, epa_total, epa_per_play, success_plays, success_rate, "
        "   total_air_yards, total_yac_yards, avg_air_yards, avg_yac_per_completion, "
        "   air_epa_total, yac_epa_total, air_epa_per_play, yac_epa_per_play, "
        "   first_down_passes, explosive_passes, third_down_attempts, "
        "   third_down_conversions, third_down_conversion_rate, red_zone_targets, "
        "   red_zone_pass_tds.\n\n"
        "5) wr_game_stats  -- one row per WR per game\n"
        "   Typical columns include: season, season_type, game_id, week, game_date, team, opponent_team, "
        "   player_id, player_name, targets, receptions, receiving_yards, "
        "   receiving_tds, epa_total, epa_per_target, success_plays, success_rate, "
        "   total_air_yards, total_yac_yards, avg_air_yards, avg_yac_per_reception, "
        "   first_downs, explosive_plays, red_zone_targets, red_zone_tds.\n\n"
        "6) qb_wr_game_stats  -- one row per QB-WR pair per game\n"
        "   Typical columns include: season, season_type, game_id, week, game_date, team, opponent_team, "
        "   qb_id, qb_name, wr_id, wr_name, targets, receptions, receiving_yards, "
        "   receiving_tds, epa_total, epa_per_target, success_plays, success_rate, "
        "   total_air_yards, total_yac_yards, avg_air_yards, avg_yac_per_reception, "
        "   first_downs, explosive_plays, red_zone_targets, red_zone_tds.\n\n"
        "The column season_type typically distinguishes regular season ('REG') vs playoffs ('POST'). "
        "Use it when the user explicitly refers to playoffs / regular season.\n\n"
        "You MUST NOT invent any other tables or columns. Only use columns that are either "
        "listed above or clearly documented in the context docs.\n\n"
        "Grain guidance:\n"
        "- For season-level questions about QBs, use qb_season_stats.\n"
        "- For season-level questions about WRs, use wr_season_stats.\n"
        "- For season-level questions about QB-WR duos, use qb_wr_season_stats.\n"
        "- For per-game 'game log' type questions for QBs, use qb_game_stats.\n"
        "- For per-game 'game log' type questions for WRs, use wr_game_stats.\n"
        "- For per-game questions about QB-WR duos in specific games, use qb_wr_game_stats.\n\n"
        "You may join tables when necessary, but only on sensible keys like (season, team), "
        "(season, player_id), or (season, qb_id, wr_id) and similar. Prefer staying within a "
        "single table when that table directly answers the question.\n\n"
        "IMPORTANT: The user does NOT want to see internal player IDs (player_id, qb_id, wr_id) "
        "in the final SELECT, unless they explicitly ask for IDs. Prefer using player_name, "
        "qb_name, wr_name, team, opponent_team, season, week, game_date, and metrics.\n\n"
        "Always answer by returning ONLY the SQL query, with no explanation or commentary."
    )

    # 3) Include exact schemas from the DB
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

    # 4) User prompt
    user_prompt = f"""
        Documentation (schema, metrics, examples):
        {context_text}

        Exact table schemas (from DuckDB):
        {schema_text}

        User question:
        \"\"\"{question}\"\"\"

        Important rules for writing SQL:
        - Use ONLY the tables listed in the system prompt: qb_season_stats, wr_season_stats,
          qb_wr_season_stats, qb_game_stats, wr_game_stats, qb_wr_game_stats.
        - Use ONLY columns that actually exist in those tables (as described in the docs above).
        - Choose the table whose grain matches the question:
          * Season-level summaries -> *_season_stats tables.
          * Per-game logs or 'game log' phrasing -> *_game_stats tables.
          * QB–WR relationship / connection -> qb_wr_* tables.
        - For leaderboards or 'top X' questions, filter out extreme small-sample cases when appropriate:
          * For QB season stats, consider requiring dropbacks >= 200 (unless user specifies otherwise).
          * For WR / QB–WR season stats, consider requiring targets >= 50 (unless user specifies otherwise).
        - Prefer explicit column lists rather than SELECT * when practical.
        - Prefer using player_name / qb_name / wr_name (and team/opponent_team) rather than IDs in SELECT.
          Do NOT include player_id, qb_id, or wr_id in the SELECT list unless the user explicitly asks for IDs.
        - Use WHERE clauses to filter by season, season_type, team, player_name (or qb_name, wr_name),
          opponent_team, etc. Use season_type = 'REG' for regular season, 'POST' for playoffs when relevant.
        - Use ORDER BY and LIMIT when ranking (e.g., highest epa_per_play or epa_per_target).
        - If the question mentions 'game logs', return multiple rows (per game) sorted by date or week.
        - Never include any natural-language explanation in the output; return ONLY the SQL.
        """

    llm = ChatOpenAI(model=LLM_MODEL_FOR_SQL, temperature=0.0)

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    raw_text = response.content
    logger.debug("Raw LLM SQL response: %s", raw_text)

    sql = _strip_sql_from_response(raw_text)
    logger.info("Generated SQL: %s", sql)

    return sql
