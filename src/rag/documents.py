from pathlib import Path

from llama_index.core import SimpleDirectoryReader


def load_documents(data_dir: Path):
    return SimpleDirectoryReader(input_dir=str(data_dir), recursive=True).load_data()
