from pathlib import Path

from src.rag.pdf_parser import (
    _source_metadata,
    document_type_for,
    export_parsed_documents,
    parse_pdf,
)


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    def __init__(self, _path):
        self.pages = [
            FakePage("GEOMETRIA\nPole koła: pi r kwadrat"),
            FakePage("1. Zadanie 1\nOblicz pole figury."),
        ]


def test_pdf_parser_preserves_page_and_section_metadata(monkeypatch, tmp_path):
    pdf_path = tmp_path / "wybrane_wzory_matematyczne.pdf"
    pdf_path.touch()
    monkeypatch.setattr("src.rag.pdf_parser.PdfReader", FakeReader)

    documents = parse_pdf(pdf_path)

    assert len(documents) == 2
    assert documents[0].metadata["file_name"] == "wybrane_wzory_matematyczne.pdf"
    assert documents[0].metadata["page_number"] == 1
    assert documents[0].metadata["document_type"] == "formula_sheet"
    assert documents[0].text.startswith("[ŹRÓDŁO:")
    assert documents[0].metadata["section"] == "GEOMETRIA"
    assert documents[1].metadata["page_number"] == 2
    assert documents[1].metadata["section"] == "1. Zadanie 1"


def test_document_type_falls_back_to_pdf():
    assert document_type_for(Path("material.pdf")) == "pdf"


def test_document_type_uses_data_folder_structure():
    assert document_type_for(Path("data/wymagania/aktualne.pdf")) == "requirements"
    assert document_type_for(Path("data/karta_wzorow/aktualna.pdf")) == "formula_sheet"
    assert document_type_for(Path("data/podstawowa/arkusze/2025.pdf")) == "exam_paper"
    assert document_type_for(Path("data/rozszerzona/klucze/2025.pdf")) == "scoring_guide"


def test_source_metadata_supports_all_polish_months_and_ascii_aliases():
    expected_months = {
        "styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec",
        "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień",
    }

    for month in expected_months:
        assert _source_metadata(Path(f"matematyka-2026-{month}.pdf"), "")["month"] == month

    assert _source_metadata(Path("matematyka-2026-sierpien.pdf"), "")["month"] == "sierpień"
    assert _source_metadata(Path("matematyka-2026-pazdziernik.pdf"), "")["month"] == "październik"


def test_current_requirements_pdf_is_readable_and_has_sections():
    requirements_path = Path("data/wymagania/DU_programowej_2024-326-341.pdf")

    documents = parse_pdf(requirements_path)
    content = "\n".join(document.text for document in documents).lower()
    levels = {document.metadata["level"] for document in documents}
    sections = {
        document.metadata["section_id"]
        for document in documents
        if document.metadata["section_id"] != "general"
    }

    assert len(documents) >= 20
    assert len(content) > 25_000
    assert "funkcje" in content
    assert "prawdopodobieństwo" in content
    assert "informatyka" not in content
    assert levels == {"podstawowy", "rozszerzony", "podstawowy, rozszerzony"}
    assert {"I", "II", "V", "XIII"}.issubset(sections)
    assert any(
        document.metadata["section_id"] == "II"
        and document.metadata["level"] == "podstawowy"
        and "wzory skróconego mnożenia" in document.text.lower()
        for document in documents
    )
    assert any(
        document.metadata["section_id"] == "II"
        and document.metadata["level"] == "rozszerzony"
        for document in documents
    )


def test_export_writes_pages_and_manifest(monkeypatch, tmp_path):
    source_dir = tmp_path / "data"
    source_dir.mkdir()
    pdf_path = source_dir / "wzory.pdf"
    pdf_path.touch()
    monkeypatch.setattr("src.rag.pdf_parser.PdfReader", FakeReader)

    manifest_path = export_parsed_documents(source_dir, tmp_path / "parsed")

    assert (manifest_path.parent / "wzory__page_0001.txt").exists()
    assert (manifest_path.parent / "wzory__page_0002.txt").exists()
    assert len(__import__("json").loads(manifest_path.read_text(encoding="utf-8"))) == 2


def test_real_exam_and_scoring_guide_are_split_into_matching_tasks():
    root = Path("data/rozszerzona")
    exam_path = root / "arkusze/matematyka-2026-maj-matura-rozszerzona.pdf"
    scoring_path = root / "klucze/matematyka-2026-maj-matura-rozszerzona-odpowiedzi.pdf"

    exam_tasks = parse_pdf(exam_path)
    scoring_tasks = parse_pdf(scoring_path)
    exam_by_id = {document.metadata["task_id"]: document for document in exam_tasks}
    scoring_by_id = {
        document.metadata["task_id"]: document
        for document in scoring_tasks
        if document.metadata.get("task_id")
    }

    assert set(exam_by_id) == set(scoring_by_id)
    assert len(exam_by_id) == 13
    assert all(
        exam_by_id[task_id].metadata["source_group_id"]
        == scoring_by_id[task_id].metadata["source_group_id"]
        for task_id in exam_by_id
    )
    assert all("Zadanie " + task_id in document.text for task_id, document in exam_by_id.items())
    assert all(document.metadata["provenance_confirmed"] for document in exam_tasks)
    assert exam_by_id["12.1"].metadata["parent_task_id"] == "12"
    assert exam_by_id["12.2"].metadata["parent_task_id"] == "12"


def test_basic_may_2026_has_thirty_three_leaf_tasks():
    path = Path("data/podstawowa/arkusze/matematyka-2026-maj-matura-podstawowa.pdf")

    documents = parse_pdf(path)

    assert len(documents) == 37
    assert {document.metadata["task_group_id"] for document in documents} == {
        str(number) for number in range(1, 34)
    }
    assert sum(document.metadata["task_id"] == document.metadata["task_group_id"] for document in documents) == 29
    assert {document.metadata["parent_task_id"] for document in documents} >= {"12", "13", "24", "33"}