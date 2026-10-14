import argparse

from ayurassist.application.conversation_manager import ConversationManager
from ayurassist.cli.interface import TerminalChat
from ayurassist.config import load_settings
from ayurassist.llm.offline_demo_model import OfflineDemoModel
from ayurassist.llm.openai_client import OpenAIChatModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AyurAssist terminal chat.")
    parser.add_argument(
        "--offline-demo",
        action="store_true",
        help="Run without OpenAI for a deterministic walkthrough demo.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings()
    if args.offline_demo:
        model = OfflineDemoModel()
    else:
        model = OpenAIChatModel(settings.model, settings.openai_api_key)
    chat = TerminalChat(ConversationManager(settings.data_dir, model))
    chat.run()


if __name__ == "__main__":
    main()
