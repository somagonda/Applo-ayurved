from __future__ import annotations

from ayurassist.agents.base_agent import Agent
from ayurassist.tools.toolbox import BookingToolbox, ToolSpec


class OpenAIChatModel:
    def __init__(self, model: str, api_key: str | None) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def reply(self, agent: Agent, history: list[dict], toolbox: BookingToolbox) -> str:
        specs = toolbox.specs_for_current_agent()
        if not specs:
            return "This session is complete."
        messages = [{"role": "system", "content": agent.system_prompt}] + history
        tool_schemas = []
        for spec in specs:
            tool_schemas.append(self._schema(spec))

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_schemas,
                tool_choice={"type": "function", "function": {"name": specs[0].name}},
            )
        except Exception as error:
            return self._friendly_error_message(error)
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or ""

        tool_calls = []
        for call in message.tool_calls:
            tool_calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
            )

        history.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls,
            }
        )

        for call in message.tool_calls:
            argument = self._latest_user_text(history)
            result = toolbox.call(call.function.name, str(argument))
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": result.message,
                }
            )
        return history[-1]["content"]

    def _latest_user_text(self, history: list[dict]) -> str:
        for message in reversed(history):
            if message.get("role") == "user":
                return str(message.get("content", ""))
        return ""

    def _friendly_error_message(self, error: Exception) -> str:
        error_name = error.__class__.__name__

        if error_name == "AuthenticationError":
            return (
                "OpenAI authentication failed. Please check OPENAI_API_KEY in .env, "
                "or run: uv run ayuvaid --offline-demo"
            )

        if error_name == "RateLimitError":
            return "AyuAssist is busy right now. Please try again later."

        if error_name == "APIConnectionError":
            return "AyuAssist is unable to connect right now. Please try again later."

        return "AyuAssist is unavailable right now. Please try again later."

    def _schema(self, spec: ToolSpec) -> dict:
        return {
            "type": "function",
            "function": {
                "name": spec.name,
                "description": spec.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        spec.argument_name: {
                            "type": "string",
                            "description": spec.argument_description,
                        }
                    },
                    "required": [spec.argument_name],
                    "additionalProperties": False,
                },
            },
        }
