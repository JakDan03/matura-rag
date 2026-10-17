from llama_index.core import Document

from config.settings import AppSettings
from src.rag.documents import load_documents
from src.rag.index_manager import IndexManager
from src.rag.parsed_store import (
    export_pdf,
    parsed_dir,
    read_parsed_documents,
    update_manifest,
)


def _task(task_id, text="Zadanie"):
    return Document(
        text=text,
        metadata={"task_id": task_id, "document_type": "exam_paper", "year": 2026},
    )


def _pdf(tmp_path, relative="podstawowa/arkusze/matura.pdf"):
    data_dir = tmp_path / "data"
    pdf_path = data_dir / relative
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF")
    return data_dir, pdf_path


def test_parsed_store_round_trips_text_and_metadata(tmp_path):
    data_dir, pdf_path = _pdf(tmp_path)
    entries = export_pdf(data_dir, pdf_path, [_task("1", "Treść 1"), _task("12.3")])
    update_manifest(data_dir, {"podstawowa/arkusze/matura.pdf": entries})

    documents = read_parsed_documents(data_dir)["podstawowa/arkusze/matura.pdf"]

    assert (parsed_dir(data_dir) / "podstawowa/arkusze/matura/task_12.3.txt").exists()
    assert [d.get_content() for d in documents] == ["Treść 1", "Zadanie"]
    assert documents[0].metadata["year"] == 2026
    assert documents[0].metadata["file_path"] == str(data_dir / "podstawowa/arkusze/matura.pdf")


def test_export_keeps_manual_corrections_unless_forced(tmp_path):
    data_dir, pdf_path = _pdf(tmp_path)
    export_pdf(data_dir, pdf_path, [_task("1", "z parsera")])
    task_file = parsed_dir(data_dir) / "podstawowa/arkusze/matura/task_1.txt"
    task_file.write_text("poprawione ręcznie", encoding="utf-8")

    export_pdf(data_dir, pdf_path, [_task("1", "z parsera")])
    assert task_file.read_text(encoding="utf-8") == "poprawione ręcznie"

    export_pdf(data_dir, pdf_path, [_task("1", "z parsera")], overwrite=True)
    assert task_file.read_text(encoding="utf-8") == "z parsera"


def test_repeated_task_ids_get_numbered_files_and_keep_order(tmp_path):
    data_dir, pdf_path = _pdf(tmp_path)
    relative = "podstawowa/arkusze/matura.pdf"
    entries = export_pdf(
        data_dir, pdf_path, [_task("5", "opis"), _task("6"), _task("5", "schemat")]
    )
    update_manifest(data_dir, {relative: entries})

    assert [entry["file"] for entry in entries] == ["task_5.txt", "task_6.txt", "task_5__2.txt"]
    documents = read_parsed_documents(data_dir)[relative]
    assert [d.get_content() for d in documents] == ["opis", "Zadanie", "schemat"]


def test_load_documents_prefers_parsed_text_and_parses_other_pdfs(monkeypatch, tmp_path):
    data_dir, stored_pdf = _pdf(tmp_path)
    other_pdf = data_dir / "podstawowa/arkusze/nowy.pdf"
    other_pdf.write_bytes(b"%PDF")
    entries = export_pdf(data_dir, stored_pdf, [_task("1", "zapisane")])
    update_manifest(data_dir, {"podstawowa/arkusze/matura.pdf": entries})
    parsed_pdfs = []

    def fake_parse_pdf(path):
        parsed_pdfs.append(path.name)
        return [_task("9", "świeżo sparsowane")]

    monkeypatch.setattr("src.rag.documents.parse_pdf", fake_parse_pdf)

    documents = load_documents(data_dir)

    assert sorted(d.get_content() for d in documents) == ["zapisane", "świeżo sparsowane"]
    assert parsed_pdfs == ["nowy.pdf"]


def test_index_hash_ignores_manual_corrections_in_parsed_dir(tmp_path):
    data_dir, pdf_path = _pdf(tmp_path)
    manager = IndexManager(
        AppSettings(data_dir=data_dir, storage_dir=tmp_path / "storage"), "local"
    )
    before = manager._source_hash()

    export_pdf(data_dir, pdf_path, [_task("1")])
    update_manifest(data_dir, {"podstawowa/arkusze/matura.pdf": []})

    assert manager._source_hash() == before
