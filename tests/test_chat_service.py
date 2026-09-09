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
    assert index.arguments["similarity_top_k"] == 150
    assert index.arguments["node_postprocessors"][0].top_n == 6
    assert service.ask("Pytanie")["answer"] == "Odpowiedź"


def test_chat_service_exposes_source_provenance_to_response():
    class SourceNode:
        score = 0.8
        node = type(
            "Node",
            (),
            {
                "metadata": {
                    "file_name": "arkusz.pdf",
                    "page_label": "12, 13",
                    "document_type": "exam_paper",
                    "task_id": "12.1",
                    "task_group_id": "12",
                    "source_group_id": "arkusz-2026",
                    "provenance_confirmed": True,
                },
                "get_content": lambda self: (
                    "[ŹRÓDŁO: plik=arkusz.pdf; typ=exam_paper; strony=12, 13; "
                    "task_id=12.1] Treść zadania."
                ),
            },
        )()

    class SourceEngine:
        def chat(self, _question):
            return type(
                "Response",
                (),
                {"response": "Wskazówka", "source_nodes": [SourceNode()]},
            )()

    class SourceIndex(FakeIndex):
        def as_chat_engine(self, **kwargs):
            self.arguments = kwargs
            return SourceEngine()

    result = ChatService(SourceIndex(), "Rola").ask("Pomóż")

    assert result["sources"] == [
        {
            "file": "arkusz.pdf",
            "page": "12, 13",
            "score": 0.8,
            "document_type": "exam_paper",
            "level": None,
            "year": None,
            "month": None,
            "term": None,
            "task_id": "12.1",
            "parent_task_id": None,
            "task_group_id": "12",
            "page_numbers": None,
            "source_group_id": "arkusz-2026",
            "provenance_confirmed": True,
        }
    ]


def test_chat_service_rejects_invalid_retrieval_configuration():
    with pytest.raises(ValueError):
        ChatService(FakeIndex(), "Prompt", retrieval_top_k=0)



def test_chat_service_returns_retrieval_metrics():
    service = ChatService(FakeIndex(), "Prompt")

    result = service.ask("Pytanie")

    assert result["retrieval_metrics"]["node_count"] == 0


def test_chat_service_uses_llm_to_explain_verified_math(monkeypatch):
    class FakeLLM:
        def complete(self, prompt):
            assert "Instrukcje wybranej roli" in prompt
            assert "Wynik zweryfikowany przez SymPy" in prompt
            assert "delta" in prompt.lower()
            return "Kroki rozwiązania: $\\Delta = 0$, więc $x = 1$."

    service = ChatService(
        FakeIndex(), "Instrukcje wybranej roli", llm=FakeLLM()
    )

    answer = service.explain_math(
        "Rozwiąż równanie x^2 - 2x + 1 = 0 metodą delty",
        "Rozwiązania: $1$",
    )

    assert "\\Delta" in answer