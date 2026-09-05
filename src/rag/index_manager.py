import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage

from src.rag.documents import load_documents
from src.rag.models import configure_models
from src.rag.pdf_parser import PARSER_VERSION


class IndexManager:
    def __init__(self, app_settings, embedding_mode: str):
        self.app_settings = app_settings
        self.embedding_mode = embedding_mode
        self.index_dir = app_settings.index_dir(embedding_mode)
        self.metadata_path = self.index_dir / "index_metadata.json"

    def _source_hash(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(self.app_settings.data_dir.rglob("*")):
            if path.is_file():
                digest.update(str(path.relative_to(self.app_settings.data_dir)).encode())
                digest.update(path.read_bytes())
        return digest.hexdigest()

    def exists(self) -> bool:
        return (self.index_dir / "docstore.json").exists()

    def is_current(self) -> bool:
        if not self.exists() or not self.metadata_path.exists():
            return False
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return (
            metadata.get("source_hash") == self._source_hash()
            and metadata.get("parser_version") == PARSER_VERSION
        )

    def build(self):
        configure_models(self.app_settings, self.embedding_mode)
        documents = load_documents(self.app_settings.data_dir)
        index = VectorStoreIndex.from_documents(documents)
        self.index_dir.parent.mkdir(parents=True, exist_ok=True)
        temporary_dir = Path(
            tempfile.mkdtemp(prefix=f".{self.index_dir.name}-", dir=self.index_dir.parent)
        )
        backup_dir = self.index_dir.parent / f".{self.index_dir.name}-backup-{uuid.uuid4().hex}"
        try:
            index.storage_context.persist(persist_dir=str(temporary_dir))
            (temporary_dir / "index_metadata.json").write_text(
                json.dumps(
                    {
                        "embedding_mode": self.embedding_mode,
                        "source_hash": self._source_hash(),
                        "document_count": len(documents),
                        "parser_version": PARSER_VERSION,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            if self.index_dir.exists():
                os.replace(self.index_dir, backup_dir)
            os.replace(temporary_dir, self.index_dir)
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        except Exception:
            if temporary_dir.exists():
                shutil.rmtree(temporary_dir)
            if backup_dir.exists() and not self.index_dir.exists():
                os.replace(backup_dir, self.index_dir)
            raise
        return index

    def load(self):
        configure_models(self.app_settings, self.embedding_mode)
        storage_context = StorageContext.from_defaults(persist_dir=str(self.index_dir))
        return load_index_from_storage(storage_context)
