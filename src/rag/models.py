from __future__ import annotations

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from config.settings import AppSettings


def configure_models(app_settings: AppSettings, embedding_mode: str, temperature: float | None = None) -> None:
    if embedding_mode == "openai":
        Settings.embed_model = OpenAIEmbedding(model=app_settings.openai_embedding_model)
    else:
        Settings.embed_model = HuggingFaceEmbedding(model_name=app_settings.local_embedding_model)

    Settings.llm = OpenAI(
        model=app_settings.llm_model,
        temperature=app_settings.default_temperature if temperature is None else temperature,
    )
