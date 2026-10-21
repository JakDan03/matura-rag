from src.services.tool_response_service import (
    ToolResponseService,
    normalize_latex,
    source_records,
)
from src.tools.contracts import ToolResult, ToolStatus


class FakeLLM:
    def __init__(self):
        self.prompt = ""

    def complete(self, prompt):
        self.prompt = prompt
        return "Gotowa odpowiedź"


def test_presenter_returns_non_ok_messages_without_llm_call():
    llm = FakeLLM()
    result = ToolResult(
        status=ToolStatus.NOT_FOUND,
        message="Nie mam zadań z 2015 roku.",
    )

    answer = ToolResponseService(llm).present("Daj zadanie", result)

    assert answer == "Nie mam zadań z 2015 roku."
    assert llm.prompt == ""


def test_presenter_requests_task_cleanup_without_rewriting_or_solving_it():
    llm = FakeLLM()
    result = ToolResult(
        status=ToolStatus.OK,
        data={
            "origin": "official_exam_task",
            "content": (
                "[ŹRÓDŁO: ...]\nZadanie 1.\n[tu powinien być rysunek]\n"
                "Wskazówka: skorzystaj z twierdzenia.\nA) ...\nE) ...\nBrudnopis"
            ),
            "metadata": {"file_name": "arkusz.pdf", "task_id": "1"},
        },
        random_selection=True,
    )

    answer = ToolResponseService(llm).present("Daj zadanie", result)

    assert answer.startswith(
        "Typ materiału: autentyczne zadanie z arkusza CKE. Losowy wybór"
    )
    assert answer.endswith("Gotowa odpowiedź")
    assert "Jesteś redaktorem tekstu zadań" in llm.prompt
    assert "usunąć techniczny nagłówek" in llm.prompt
    assert "uporządkować wzory, ułamki i współrzędne" in llm.prompt
    assert "poprawnym LaTeX-u" in llm.prompt
    assert r"\binom{n}{k}" in llm.prompt
    assert r"\overrightarrow{AM}" in llm.prompt
    assert "niezależnie od ich liczby i oznaczeń" in llm.prompt
    assert "adnotacją o brakującej grafice" in llm.prompt
    assert "Zachowaj wskazówki, które występują w źródle" in llm.prompt
    assert "pozostaje niejednoznaczny" in llm.prompt
    assert "Nie rozwiązuj go" in llm.prompt
    assert "Brudnopis" in llm.prompt
    assert "Rola tutora" not in llm.prompt


def test_source_records_keep_task_and_page_provenance():
    result = ToolResult(
        status=ToolStatus.OK,
        data={"content": "Treść"},
        provenance=(
            {
                "file_name": "arkusz.pdf",
                "page_label": "12, 13",
                "document_type": "exam_paper",
                "task_id": "12.1",
                "source_group_id": "maj-2026",
                "provenance_confirmed": True,
            },
        ),
    )

    sources = source_records(result)

    assert sources[0]["file"] == "arkusz.pdf"
    assert sources[0]["page"] == "12, 13"
    assert sources[0]["task_id"] == "12.1"
    assert sources[0]["provenance_confirmed"] is True


def test_normalize_latex_wraps_common_llm_math_delimiters():
    text = r"Liczba ( \sqrt{25} \cdot 8 ) jest równa."

    assert normalize_latex(text) == r"Liczba $ \sqrt{25} \cdot 8 $ jest równa."
