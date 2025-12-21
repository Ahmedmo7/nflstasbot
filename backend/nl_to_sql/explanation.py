# backend/nl_to_sql/explanation.py

import json
from typing import Dict, Any
import logging

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

LLM_MODEL_FOR_EXPLANATION = "gpt-4.1"

logger = logging.getLogger(__name__)


def explain_results(question: str, sql: str, rows: list[Dict[str, Any]]) -> str:
    """
    Turn the raw rows + SQL back into a human explanation.

    This is table-agnostic: it can explain QB season stats, WR stats,
    QB-WR connection stats, or game logs.
    """
    load_dotenv()

    llm = ChatOpenAI(model=LLM_MODEL_FOR_EXPLANATION, temperature=0.1)
    rows_json = json.dumps(rows, indent=2)

    system_prompt = (
        "You are an NFL analytics assistant. You explain query results clearly.\n"
        "You understand quarterback, wide receiver, and QB–WR duo stats, including "
        "EPA per play/target, success rate, air yards (aDOT), YAC, red-zone usage, "
        "and game logs.\n"
        "You should not invent numbers that are not present in the rows, but you may "
        "summarize trends and relative comparisons."
    )

    user_prompt = f"""
        User asked:
        {question}

        SQL:
        ```sql
        {sql}
        ```

        Query Results (JSON array of rows):
        {rows_json}

        Instructions:

        Summarize the findings in 2–6 sentences.

        Mention seasons, teams, and players explicitly when relevant.

        Call out key efficiency metrics (EPA per play / target, success rate) and volume (dropbacks, targets)
        if they are present.

        If this looks like a game-log query, highlight notable single games or patterns across games.

        Mention sample-size constraints if obvious (e.g., very few targets/dropbacks).

        If there are no rows, explain that and suggest why (e.g., filter too strict or season not in data).
        """

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    explanation = response.content.strip()
    logger.debug("Explanation LLM output: %s", explanation)

    return explanation
    