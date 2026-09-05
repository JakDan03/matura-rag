from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from src.rag.pdf_parser import parse_pdf


def load_documents(data_dir: Path):
    documents = []
    non_pdf_paths = []

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".pdf":
            documents.extend(parse_pdf(path))
        else:
            non_pdf_paths.append(path)

    if non_pdf_paths:
        documents.extend(
            SimpleDirectoryReader(
                input_files=[str(path) for path in non_pdf_paths]
            ).load_data()
        )

    return documents
