from src.services.chat_service import ChatService


class FakeChatEngine:
    def chat(self, _question):
        return type("Response", (), {"response": "Odpowiedź", "source_nodes": []})()


class FakeIndex:
    def __init__(self):
        self.arguments = None

    def as_chat_engine(self, **kwargs):
        self.arguments = kwargs
        return FakeChatEngine()


def test_chat_service_uses_prompt_compatible_engine():
    index = FakeIndex()

    service = ChatService(index, "Zasady CKE")

    assert index.arguments["chat_mode"] == "condense_plus_context"
    assert index.arguments["system_prompt"] == "Zasady CKE"
    assert service.ask("Pytanie")["answer"] == "Odpowiedź"