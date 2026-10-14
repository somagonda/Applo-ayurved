from ayurassist.application.conversation_manager import ConversationManager


class TerminalChat:
    def __init__(self, conversation_manager: ConversationManager) -> None:
        self.conversation_manager = conversation_manager

    def run(self) -> None:
        print(self.conversation_manager.start_message())
        while not self.conversation_manager.session.ended:
            user_text = input("You: ").strip()
            if user_text.lower() in {"exit", "quit"}:
                print("AyuAssist: Thanks for chatting. Goodbye.")
                break
            reply = self.conversation_manager.handle_user_message(user_text)
            print(f"AyuAssist: {reply}")
