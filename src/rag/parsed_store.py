from __future__ import annotations

import json
from pathlib import Path

from llama_index.core import Document

from src.rag.pdf_parser import PARSER_VERSION

PARSED_DIR_NAME = "parsed"
MANIFEST_NAME = "manifest.json"


def parsed_dir(data_dir: Path) -> Path:
    return data_dir / PARSED_DIR_NAME


def _document_directory(data_dir: Path, relative_pdf: str) -> Path:
    return parsed_dir(data_dir) / Path(relative_pdf).with_suffix("")


def _document_file_name(document: Document, index: int) -> str:
    task_id = document.metadata.get("task_id")
    return f"task_{task_id}.txt" if task_id else f"doc_{index:04d}.txt"


def export_pdf(
    data_dir: Path,
    pdf_path: Path,
    documents: list[Document],
    overwrite: bool = False,
) -> list[dict]:
    """Writes one text file per document; existing files hold manual corrections."""

    relative_pdf = pdf_path.relative_to(data_dir).as_posix()
    directory = _document_directory(data_dir, relative_pdf)
    directory.mkdir(parents=True, exist_ok=True)

    entries = []
    occurrences: dict[str, int] = {}
    for index, document in enumerate(documents, start=1):
        name = _document_file_name(document, index)
        occurrences[name] = occurrences.get(name, 0) + 1
        if occurrences[name] > 1:
            # Scoring guides repeat a task: full description first, point scheme later.
            name = f"{name.removesuffix('.txt')}__{occurrences[name]}.txt"
        file_path = directory / name
        if overwrite or not file_path.exists():
            file_path.write_text(document.get_content(), encoding="utf-8", newline="\n")
        metadata = dict(document.metadata)
        metadata["file_path"] = relative_pdf
        entries.append({"file": name, "metadata": metadata})
    return entries


def update_manifest(data_dir: Path, entries: dict[str, list[dict]]) -> None:
    root = parsed_dir(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / MANIFEST_NAME
    pdfs = {}
    if manifest_path.exists():
        pdfs = json.loads(manifest_path.read_text(encoding="utf-8"))["pdfs"]
    pdfs.update(entries)
    manifest = {"parser_version": PARSER_VERSION, "pdfs": dict(sorted(pdfs.items()))}
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1),
        encoding="utf-8",
        newline="\n",
    )


def read_parsed_documents(data_dir: Path) -> dict[str, list[Document]]:
    """Returns stored documents keyed by the PDF path relative to data_dir."""

    manifest_path = parsed_dir(data_dir) / MANIFEST_NAME
    if not manifest_path.exists():
        return {}
    pdfs = json.loads(manifest_path.read_text(encoding="utf-8"))["pdfs"]

    result = {}
    for relative_pdf, entries in pdfs.items():
        directory = _document_directory(data_dir, relative_pdf)
        documents = []
        for entry in entries:
            metadata = dict(entry["metadata"])
            metadata["file_path"] = str(data_dir / relative_pdf)
            text = (directory / entry["file"]).read_text(encoding="utf-8")
            documents.append(Document(text=text, metadata=metadata))
        result[relative_pdf] = documents
    return result
