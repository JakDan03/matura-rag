from pathlib import Path

from src.rag.pdf_parser import document_type_for, export_parsed_documents, parse_pdf


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