import pytest

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
    assert index.arguments["similarity_top_k"] == 2
    assert index.arguments["node_postprocessors"][0].similarity_cutoff == 0.2
    assert service.ask("Pytanie")["answer"] == "Odpowiedź"


def test_chat_service_rejects_invalid_retrieval_configuration():
    with pytest.raises(ValueError):
        ChatService(FakeIndex(), "Prompt", retrieval_top_k=0)

    with pytest.raises(ValueError):
        ChatService(FakeIndex(), "Prompt", similarity_cutoff=1.1)