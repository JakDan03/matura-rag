import json

from config.settings import AppSettings
from src.rag.index_manager import IndexManager
from src.rag.pdf_parser import PARSER_VERSION


def test_index_manager_detects_source_changes(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source_file = data_dir / "notes.txt"
    source_file.write_text("wersja 1", encoding="utf-8")

    app_settings = AppSettings(data_dir=data_dir, storage_dir=tmp_path / "storage")
    manager = IndexManager(app_settings, "local")
    manager.index_dir.mkdir(parents=True)
    manager.metadata_path.write_text(
        json.dumps(
            {
                "source_hash": manager._source_hash(),
                "parser_version": PARSER_VERSION,
            }
        ),
        encoding="utf-8",
    )
    (manager.index_dir / "docstore.json").write_text("{}", encoding="utf-8")

    assert manager.is_current()

    source_file.write_text("wersja 2", encoding="utf-8")

    assert not manager.is_current()


def test_build_replaces_index_atomically(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "notes.txt").write_text("nowe dane", encoding="utf-8")
    app_settings = AppSettings(data_dir=data_dir, storage_dir=tmp_path / "storage")
    manager = IndexManager(app_settings, "local")
    manager.index_dir.mkdir(parents=True)
    (manager.index_dir / "docstore.json").write_text("stara wersja", encoding="utf-8")

    class FakeStorageContext:
        def persist(self, persist_dir):
            path = __import__("pathlib").Path(persist_dir)
            (path / "docstore.json").write_text("nowa wersja", encoding="utf-8")

    class FakeIndex:
        storage_context = FakeStorageContext()

    monkeypatch.setattr("src.rag.index_manager.configure_models", lambda *_: None)
    monkeypatch.setattr("src.rag.index_manager.load_documents", lambda *_: ["document"])
    monkeypatch.setattr(
        "src.rag.index_manager.VectorStoreIndex.from_documents",
        lambda *_: FakeIndex(),
    )

    manager.build()

    assert (manager.index_dir / "docstore.json").read_text(encoding="utf-8") == "nowa wersja"
    assert manager.metadata_path.exists()
    assert not list(manager.index_dir.parent.glob(f".{manager.index_dir.name}-*"))
