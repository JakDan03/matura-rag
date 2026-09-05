from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class AppSettings:
    data_dir: Path = ROOT_DIR / "data"
    storage_dir: Path = ROOT_DIR / "storage"
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"
    openai_embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    default_temperature: float = 0.2

    def index_dir(self, embedding_mode: str) -> Path:
        directory_name = "openai" if embedding_mode == "openai" else "local"
        model_name = (
            self.openai_embedding_model
            if directory_name == "openai"
            else self.local_embedding_model.split("/")[-1]
        )
        return self.storage_dir / "indexes" / directory_name / model_name


settings = AppSettings()
