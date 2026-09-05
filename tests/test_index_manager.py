import json

from config.settings import AppSettings
from src.rag.index_manager import IndexManager


def test_index_manager_detects_source_changes(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source_file = data_dir / "notes.txt"
    source_file.write_text("wersja 1", encoding="utf-8")

    app_settings = AppSettings(data_dir=data_dir, storage_dir=tmp_path / "storage")
    manager = IndexManager(app_settings, "local")
    manager.index_dir.mkdir(parents=True)
    manager.metadata_path.write_text(
        json.dumps({"source_hash": manager._source_hash()}), encoding="utf-8"
    )
    (manager.index_dir / "docstore.json").write_text("{}", encoding="utf-8")

    assert manager.is_current()

    source_file.write_text("wersja 2", encoding="utf-8")

    assert not manager.is_current()
