from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from src.rag.parsed_store import parsed_dir, read_parsed_documents
from src.rag.pdf_parser import parse_pdf


def load_documents(data_dir: Path):
    documents = []
    non_pdf_paths = []
    parsed = read_parsed_documents(data_dir)
    parsed_root = parsed_dir(data_dir)

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or parsed_root in path.parents:
            continue
        if path.suffix.lower() == ".pdf":
            stored = parsed.get(path.relative_to(data_dir).as_posix())
            documents.extend(stored if stored is not None else parse_pdf(path))
        else:
            non_pdf_paths.append(path)

    if non_pdf_paths:
        documents.extend(
            SimpleDirectoryReader(
                input_files=[str(path) for path in non_pdf_paths]
            ).load_data()
        )

    return documents
