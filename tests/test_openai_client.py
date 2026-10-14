from ayurassist.agents.base_agent import Agent
from ayurassist.llm.openai_client import OpenAIChatModel
from ayurassist.tools.toolbox import ToolSpec


class AuthenticationError(Exception):
    pass


class FakeCompletions:
    def create(self, **kwargs):
        raise AuthenticationError("expired key")


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self) -> None:
        self.chat = FakeChat()


class FakeToolbox:
    def specs_for_current_agent(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                "find_patient",
                "Find patient.",
                "phone_or_name",
                "Phone number or name.",
            )
        ]


def test_openai_authentication_error_returns_friendly_message() -> None:
    model = OpenAIChatModel.__new__(OpenAIChatModel)
    model.client = FakeClient()
    model.model = "fake-model"
    agent = Agent(name="TestAgent", system_prompt="Use the tool.")
    history = [{"role": "user", "content": "5498767890"}]

    reply = model.reply(agent, history, FakeToolbox())

    assert "OpenAI authentication failed" in reply
    assert "uv run ayuvaid --offline-demo" in reply
