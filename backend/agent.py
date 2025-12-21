from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import logging 
from backend.nl_to_sql import answer_question


class ConversationalNFLAgent:
    """A small conversational orchestrator that uses an LLM to decide when
    to call the `answer_question` tool and to produce natural-language
    summaries. This avoids tight coupling to LangChain agent internals while
    keeping the interaction conversational and stateful.
    
    Behavior:
    - The LLM may request a tool call by emitting a single-line command
      starting with `CALL_TOOL:` followed by the question to pass to the
      tool. Example: `CALL_TOOL: Top 3 QBs by EPA per play in 2022`.
    - The orchestrator will call `answer_question`, then pass the JSON
      result back to the LLM as `TOOL_RESULT: <json>` and ask it to
      produce a natural-language reply.
    - Conversation memory is kept in `self.history` (list of dicts with
      `role` and `content`).
    """

    def __init__(self, model: str = "gpt-4.1-mini", temperature: float = 0.5):
        load_dotenv()
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.history: List[Dict[str, str]] = []
        self.logger = logging.getLogger(__name__)

    def reset(self) -> None:
        """Clear conversation history."""
        self.history = []

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        system = (
            "You are a helpful NFL analytics assistant. When you need to fetch "
            "data from the stats database, request it by emitting a single line "
            "starting with `CALL_TOOL:` followed by the exact natural-language "
            "question to run (e.g. `CALL_TOOL: Top 3 QBs by EPA per play in 2022`). "
            "After you receive the tool output, continue the conversation and "
            "produce a concise, user-friendly explanation. When summarizing tool "
            "results, do NOT include raw SQL or raw JSON. Instead produce a "
            "short human-friendly summary followed by a brief season-level analysis: "
            "mention player-season context, notable trends, comparisons to peers, "
            "and any sample-size caveats. If appropriate, offer a suggested follow-up "
            "question the user could ask. Keep the tone conversational and helpful."
        )

        messages = [{"role": "system", "content": system}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_input})
        return messages

    def _parse_call(self, text: str) -> Optional[str]:
        """If model asks to call the tool, returns the tool question, else None."""
        text = text.strip()
        for line in text.splitlines():
            if line.strip().upper().startswith("CALL_TOOL:"):
                return line.split("CALL_TOOL:", 1)[1].strip()
        return None

    def run(self, user_input: str, max_tool_calls: int = 2) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Process a user message.

        Returns a tuple (assistant_text, tool_result_or_None).
        """
        # Prepare initial messages
        messages = self._build_messages(user_input)

        tool_result: Optional[Dict[str, Any]] = None

        self.logger.info("Agent run: user_input=%s", user_input)
        for _ in range(max_tool_calls + 1):
            # Ask the LLM what to do
            resp = self.llm.invoke(messages)
            content = resp.content.strip()
            self.logger.debug("LLM content: %s", content)

            # Check if LLM asked to call the tool
            tool_q = self._parse_call(content)
            if tool_q:
                # Call the existing answer_question tool
                result = answer_question(tool_q)
                tool_result = result
                self.logger.info("Tool called: question=%s, rows=%d", tool_q, len(result.get("rows", [])))

                # Append the assistant's tool-calling intent and the tool result
                messages.append({"role": "assistant", "content": content})
                # Insert the tool result as assistant content so the model can see it
                messages.append({"role": "assistant", "content": "TOOL_RESULT: " + json.dumps(result)})

                # Now ask the model (as a user) to summarize the tool output for the end user
                messages.append({"role": "user", "content": "Please summarize the tool output for the user."})
                continue

            # No tool call requested — treat this as final assistant text
            assistant_text = content

            # Save turn to memory
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": assistant_text})
            self.logger.info("Agent reply produced; returning. tool_used=%s", bool(tool_result))

            return assistant_text, tool_result

        # If we exit loop without producing an assistant text, return fallback
        fallback = "Sorry, I couldn't fetch results right now."
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": fallback})
        return fallback, tool_result


# Singleton agent instance used by the Chainlit app
agent = ConversationalNFLAgent(model="gpt-4.1-mini", temperature=0.0)
