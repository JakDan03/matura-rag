from pathlib import Path

from src.rag.pdf_parser import document_type_for, parse_pdf


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