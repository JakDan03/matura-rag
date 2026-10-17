"""Parses the PDFs in data/ into data/parsed/ (one text file per task or page).

Existing text files are kept because they hold manual corrections; pass
--force to overwrite them. The manifest is always refreshed.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings  # noqa: E402
from src.rag.parsed_store import export_pdf, parsed_dir, update_manifest  # noqa: E402
from src.rag.pdf_parser import parse_pdf  # noqa: E402


def main() -> None:
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--force", action="store_true", help="overwrite existing text files")
    arguments.add_argument("pdf", nargs="*", help="PDF paths relative to data/ (default: all)")
    options = arguments.parse_args()

    data_dir = settings.data_dir
    parsed_root = parsed_dir(data_dir)
    if options.pdf:
        paths = [data_dir / name for name in options.pdf]
    else:
        paths = sorted(p for p in data_dir.rglob("*.pdf") if parsed_root not in p.parents)

    for number, path in enumerate(paths, start=1):
        relative = path.relative_to(data_dir).as_posix()
        entries = export_pdf(data_dir, path, parse_pdf(path), overwrite=options.force)
        update_manifest(data_dir, {relative: entries})
        print(f"[{number}/{len(paths)}] {relative}: {len(entries)} documents", flush=True)


if __name__ == "__main__":
    main()
