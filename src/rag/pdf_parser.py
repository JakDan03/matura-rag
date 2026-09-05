import re
from pathlib import Path

from llama_index.core import Document
from pypdf import PdfReader


PARSER_VERSION = "pdf-pages-v1"


def document_type_for(path: Path) -> str:
    name = path.name.lower()
    if "wzor" in name or "formula" in name:
        return "formula_sheet"
    if "informator" in name:
        return "exam_guide"
    if "ocenian" in name or "scoring" in name:
        return "scoring_guide"
    return "pdf"


def _is_heading(line: str) -> bool:
    normalized = " ".join(line.split())
    if not normalized or len(normalized) > 100:
        return False
    if re.match(r"^(SPIS TREŚCI|WSTĘP|WPROWADZENIE|ZAŁĄCZNIK)\b", normalized, re.IGNORECASE):
        return True
    if re.match(r"^\d+(?:\.\d+)*[.)]?\s+[A-ZĄĆĘŁŃÓŚŹŻ0-9]", normalized):
        return True
    letters = [character for character in normalized if character.isalpha()]
    return bool(letters) and len(letters) >= 4 and all(
        character.isupper() for character in letters
    )


def _clean_page_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse_pdf(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    documents = []
    current_section = None
    document_type = document_type_for(path)

    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_page_text(page.extract_text() or "")
        if not text:
            continue

        page_lines = text.splitlines()
        for line in page_lines:
            if _is_heading(line):
                current_section = line
                break

        documents.append(
            Document(
                text=text,
                metadata={
                    "file_name": path.name,
                    "file_path": str(path),
                    "page_number": page_number,
                    "page_label": str(page_number),
                    "document_type": document_type,
                    "section": current_section or "",
                    "parser_version": PARSER_VERSION,
                },
            )
        )

    return documents
