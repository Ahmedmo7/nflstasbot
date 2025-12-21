import anyio
import chainlit as cl
from typing import Any
import logging
from pathlib import Path

from backend.agent import agent
from backend.charts import get_qb_epa_vs_cpoe, plot_qb_epa_vs_cpoe

# configure logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@cl.on_message
async def main(message: Any):
    # Extract text from Chainlit message object
    if hasattr(message, "content") and isinstance(message.content, str):
        question = message.content
    elif hasattr(message, "text") and isinstance(message.text, str):
        question = message.text
    else:
        question = str(message)

    logger.info("Received message: %s", question)
    lower_q = question.lower().strip()

    # ---------------------------------------------------------------------
    # SPECIAL HANDLER: EPA per play vs CPOE scatter chart
    #
    # Trigger if:
    #   - the message mentions both "epa" and "cpoe"
    #   - AND some chart-y word like "chart", "plot", "scatter", "graph", "visual", "viz"
    # OR explicitly contains "epa vs cpoe"
    # ---------------------------------------------------------------------
    chart_keywords = ["chart", "plot", "scatter", "graph", "visual", "viz"]
    wants_chart = any(word in lower_q for word in chart_keywords)

    if ("epa vs cpoe" in lower_q) or ("epa" in lower_q and "cpoe" in lower_q and wants_chart):
        # Simple season extraction: look for a 4-digit year in the text.
        season = 2023
        for year in range(2010, 2031):
            if str(year) in lower_q:
                season = year
                break

        await cl.Message(
            content=f"**Creating EPA per play vs CPOE scatter for {season}...**"
        ).send()

        # Fetch data (run_query inside) in a worker thread
        try:
            points = await anyio.to_thread.run_sync(
                get_qb_epa_vs_cpoe,
                season,
                200,  # min_dropbacks
            )
        except Exception as e:
            logger.exception("Error while fetching chart data: %s", e)
            await cl.Message(
                content=(
                    "There was an error fetching data for the chart. "
                    "Check the server logs for details."
                )
            ).send()
            return

        if not points:
            await cl.Message(
                content=f"No QB data found for season {season} with the current filters."
            ).send()
            return

        # Render chart to PNG (also in a worker thread)
        img_path = Path("charts") / f"epa_vs_cpoe_{season}.png"
        try:
            await anyio.to_thread.run_sync(
                plot_qb_epa_vs_cpoe,
                points,
                season,
                img_path,
            )
        except Exception as e:
            logger.exception("Error while plotting chart: %s", e)
            await cl.Message(
                content=(
                    "There was an error generating the chart image. "
                    "Check the server logs for details."
                )
            ).send()
            return

        # Send chart image
        await cl.Image(
            path=str(img_path),
            name=f"EPA vs CPOE {season}",
        ).send()

        # Show a compact table under the chart (first 15 rows)
        preview = points[:15]
        if preview:
            table_md = _rows_to_markdown_table(preview)
            await cl.Message(
                content=f"**Underlying data (first {len(preview)} rows):**\n\n{table_md}"
            ).send()

        # We handled this message fully; don't fall through to the agent.
        return

    # ---------------------------------------------------------------------
    # DEFAULT PATH: conversational agent + NFL stats tool
    # ---------------------------------------------------------------------
    # Run the conversational agent (which will decide whether to call the
    # nfl stats tool). We run in a thread to avoid blocking the event loop.
    assistant_text, tool_result = await anyio.to_thread.run_sync(
        agent.run,
        question,
    )

    # Sanitize assistant output and send as Markdown
    assistant_clean = _sanitize_assistant_text(assistant_text)
    await cl.Message(content=assistant_clean).send()

    # Only display structured results if the tool returned them
    if tool_result:
        rows = tool_result.get("rows", [])
        sql = (tool_result.get("sql", "") or "").strip()

        if rows:
            table_md = _rows_to_markdown_table(rows)
            await cl.Message(content="**Results**\n\n" + table_md).send()
        else:
            await cl.Message(
                content="**Results**\n\n_No rows returned for this query._"
            ).send()

        # Do not render SQL to the user. The agent will provide a human-friendly
        # summary and season-level analysis instead.


@cl.on_chat_start
async def start():
    """Send an initial explanatory message and suggested prompts when a chat starts."""
    intro = (
        "### NFL Stats Assistant\n\n"
        "I convert natural-language NFL QB and WR questions into DuckDB SQL, "
        "run the queries against your local NFL warehouse, and summarize the results.\n\n"
        "Ask about season-level efficiency, game logs, or QB–WR connections. "
        "You can also request charts like **EPA vs CPOE**."
    )

    suggestions = [
        "Top 3 QBs by EPA per play in 2022 (min 200 dropbacks)",
        "Which QBs had the highest success rate in 2020 (min 500 dropbacks)?",
        "Average EPA per play by team in 2023",
        "Show me passing yards leaders for 2021",
        "Show me an EPA vs CPOE scatter for 2023",
    ]

    # Send intro
    await cl.Message(content=intro).send()

    # Render suggested prompts as a bullet list
    bullets = "\n".join([f"- {s}" for s in suggestions])
    await cl.Message(content="**Suggested prompts**\n\n" + bullets).send()


def _sanitize_assistant_text(text: str) -> str:
    """Remove common leading role headings and empty lines from model output."""
    if not text:
        return ""
    lines = [l for l in text.splitlines()]
    while lines and (
        not lines[0].strip()
        or lines[0].strip().lower() in ("assistant", "results")
    ):
        lines.pop(0)
    return "\n".join(lines).strip()


def _rows_to_markdown_table(rows: list[dict]) -> str:
    """Render rows as a Markdown table."""
    if not rows:
        return "_No data_"

    headers = list(rows[0].keys())
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    body_lines = []
    for r in rows:
        vals = [str(r.get(h, "")) for h in headers]
        body_lines.append("| " + " | ".join(vals) + " |")

    return "\n".join([header_line, sep_line] + body_lines)
