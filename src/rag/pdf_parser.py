import re
import json
from pathlib import Path

from llama_index.core import Document
from pypdf import PdfReader


PARSER_VERSION = "task-documents-v5"

_REQUIREMENTS_SECTION = re.compile(
    r"^[IVX]+\.\s+.+$|^Twierdzenia, dowody – zakres (?:podstawowy|rozszerzony):$",
    re.IGNORECASE,
)
_REQUIREMENTS_DOMAIN = re.compile(r"^([IVX]+)\.\s+(.+?)\.$")
_REQUIREMENTS_BASIC = re.compile(r"^Zakres podstawowy\.\s*Uczeń\b", re.IGNORECASE)
_REQUIREMENTS_ADVANCED = re.compile(
    r"^Zakres rozszerzony\.\s*Uczeń(?:\s+spełnia wymagania określone dla zakresu podstawowego,\s*a)?",
    re.IGNORECASE,
)
_MONTH_ALIASES = {
    "styczeń": "styczeń",
    "styczen": "styczeń",
    "luty": "luty",
    "marzec": "marzec",
    "kwiecień": "kwiecień",
    "kwiecien": "kwiecień",
    "maj": "maj",
    "czerwiec": "czerwiec",
    "lipiec": "lipiec",
    "sierpień": "sierpień",
    "sierpien": "sierpień",
    "wrzesień": "wrzesień",
    "wrzesien": "wrzesień",
    "październik": "październik",
    "pazdziernik": "październik",
    "listopad": "listopad",
    "grudzień": "grudzień",
    "grudzien": "grudzień",
}
_MONTH_PATTERN = re.compile(
    r"(" + "|".join(sorted(_MONTH_ALIASES, key=len, reverse=True)) + r")",
    re.IGNORECASE,
)
_TASK_HEADING = re.compile(
    r"^Zadanie\s+(\d+(?:\.\d+)?)\.?\s*(?:\(([^)]*)\))?",
    re.IGNORECASE,
)


def _requirements_sections(lines: list[str]) -> list[str]:
    sections = []
    for line in lines:
        normalized = " ".join(line.split())
        if _REQUIREMENTS_SECTION.match(normalized) and normalized not in sections:
            sections.append(normalized)
    return sections


def _requirements_lines(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    lines = []
    for page in reader.pages:
        text = _clean_page_text(page.extract_text() or "")
        for line in text.splitlines():
            normalized = " ".join(line.split())
            if not normalized or normalized.isdigit():
                continue
            if normalized.startswith("Dziennik Ustaw"):
                continue
            if normalized.upper() == "INFORMATYKA":
                return lines
            lines.append(normalized)
    return lines


def _requirements_documents(path: Path) -> list[Document]:
    lines = _requirements_lines(path)
    domain_positions = []
    math_start = None
    for index, line in enumerate(lines):
        match = _REQUIREMENTS_DOMAIN.match(line)
        if not match:
            continue
        if match.group(1) == "I" and match.group(2) == "Liczby rzeczywiste":
            math_start = index
        if math_start is not None and index >= math_start:
            domain_positions.append((index, match.group(1), match.group(2)))

    documents = []
    general_text = "\n".join(lines[: math_start or len(lines)]).strip()
    if general_text:
        documents.append(
            Document(
                text=general_text,
                metadata={
                    "file_name": path.name,
                    "file_path": str(path),
                    "document_type": "requirements",
                    "source_kind": "requirements",
                    "section": "Cele kształcenia – wymagania ogólne",
                    "section_id": "general",
                    "level": "podstawowy, rozszerzony",
                    "levels": "podstawowy, rozszerzony",
                    "parser_version": PARSER_VERSION,
                    "provenance_confirmed": True,
                },
            )
        )

    for position, (start, section_id, section_name) in enumerate(domain_positions):
        end = (
            domain_positions[position + 1][0]
            if position + 1 < len(domain_positions)
            else len(lines)
        )
        section_lines = lines[start:end]
        basic_index = next(
            (index for index, line in enumerate(section_lines) if _REQUIREMENTS_BASIC.match(line)),
            None,
        )
        advanced_index = next(
            (index for index, line in enumerate(section_lines) if _REQUIREMENTS_ADVANCED.match(line)),
            None,
        )
        if basic_index is None:
            continue

        blocks = [("podstawowy", basic_index, advanced_index or len(section_lines))]
        if advanced_index is not None:
            blocks.append(("rozszerzony", advanced_index, len(section_lines)))

        for level, block_start, block_end in blocks:
            block_text = "\n".join(section_lines[block_start:block_end]).strip()
            if not block_text:
                continue
            documents.append(
                Document(
                    text=f"Dział {section_id}. {section_name}.\nPoziom: {level}\n{block_text}",
                    metadata={
                        "file_name": path.name,
                        "file_path": str(path),
                        "document_type": "requirements",
                        "source_kind": "requirements",
                        "section": f"{section_id}. {section_name}.",
                        "section_id": section_id,
                        "section_name": section_name,
                        "level": level,
                        "levels": level,
                        "parser_version": PARSER_VERSION,
                        "provenance_confirmed": True,
                    },
                )
            )

    return documents


def document_type_for(path: Path) -> str:
    name = path.name.lower()
    directories = {part.lower() for part in path.parts}
    if "karta_wzorow" in directories:
        return "formula_sheet"
    if "wymagania" in directories:
        return "requirements"
    if "klucze" in directories or "ocenian" in name or "scoring" in name:
        return "scoring_guide"
    if "arkusze" in directories:
        return "exam_paper"
    if "informatory" in directories:
        return "exam_guide"
    if "wzor" in name or "formula" in name:
        return "formula_sheet"
    if "informator" in name:
        return "exam_guide"
    if "ocenian" in name or "scoring" in name:
        return "scoring_guide"
    return "pdf"


def _source_metadata(path: Path, text: str) -> dict:
    directories = {part.lower() for part in path.parts}
    metadata = {}
    if "podstawowa" in directories:
        metadata["level"] = "podstawowy"
    elif "rozszerzona" in directories:
        metadata["level"] = "rozszerzony"

    year_match = re.search(r"20\d{2}", path.stem)
    if year_match:
        metadata["year"] = int(year_match.group())

    month_match = _MONTH_PATTERN.search(path.stem)
    if month_match:
        metadata["month"] = _MONTH_ALIASES[month_match.group(1).lower()]
    for term in ("probna", "poprawkowa", "dodatkowa"):
        if term in path.stem.lower():
            metadata["term"] = term
            break

    metadata["source_group_id"] = re.sub(
        r"-odpowiedzi$", "", path.stem, flags=re.IGNORECASE
    )
    metadata["source_kind"] = {
        "exam_paper": "official_exam",
        "exam_guide": "informator",
        "scoring_guide": "scoring_guide",
        "requirements": "requirements",
        "formula_sheet": "formula_sheet",
    }.get(document_type_for(path), "other")
    return metadata


def _source_header(metadata: dict) -> str:
    fields = [
        f"plik={metadata['file_name']}",
        f"typ={metadata['document_type']}",
    ]
    for key in ("level", "year", "month", "term", "task_id", "section"):
        if metadata.get(key):
            fields.append(f"{key}={metadata[key]}")
    return "[ŹRÓDŁO: " + "; ".join(fields) + "]"


def _task_documents(path: Path, document_type: str) -> list[Document]:
    reader = PdfReader(str(path))
    source_metadata = _source_metadata(path, "")
    tasks = []
    current = None
    parent_context = None
    preamble = []

    def flush():
        if current is None:
            return
        task_id, parent_task_id, points, lines, pages = current
        text = "\n".join(lines).strip()
        if not text:
            return
        metadata = {
            "file_name": path.name,
            "file_path": str(path),
            "document_type": document_type,
            "task_id": task_id,
            "parent_task_id": parent_task_id or "",
            "task_group_id": parent_task_id or task_id.split(".")[0],
            "points": points or "",
            "page_number": pages[0],
            "page_numbers": pages,
            "page_label": ", ".join(str(page) for page in pages),
            "parser_version": PARSER_VERSION,
            **source_metadata,
        }
        metadata["provenance_confirmed"] = bool(
            metadata.get("source_group_id") and metadata.get("task_id")
        )
        tasks.append(
            Document(
                text=f"{_source_header(metadata)}\n{text}",
                metadata=metadata,
            )
        )

    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_page_text(page.extract_text() or "")
        if not text:
            continue
        page_lines = text.splitlines()
        for line in page_lines:
            match = _TASK_HEADING.match(line)
            if match:
                task_id = match.group(1)
                is_subtask = "." in task_id
                if is_subtask and current is not None:
                    current_id = current[0]
                    if "." not in current_id and task_id.startswith(current_id + "."):
                        parent_context = (current_id, current[3][:], current[4][:])
                    else:
                        flush()
                elif not is_subtask:
                    flush()
                    parent_context = None
                else:
                    flush()

                inherited_lines = parent_context[1][:] if parent_context else []
                inherited_pages = parent_context[2][:] if parent_context else []
                current = [
                    task_id,
                    parent_context[0] if parent_context else "",
                    match.group(2),
                    inherited_lines + [line],
                    sorted(set(inherited_pages + [page_number])),
                ]
                continue
            if current is not None:
                current[3].append(line)
                if page_number not in current[4]:
                    current[4].append(page_number)
            elif document_type == "scoring_guide":
                preamble.append(line)
    flush()

    if document_type == "scoring_guide" and preamble:
        metadata = {
            "file_name": path.name,
            "file_path": str(path),
            "document_type": document_type,
            "section": "Uwagi ogólne",
            "page_number": 1,
            "page_numbers": [1],
            "page_label": "1",
            "parser_version": PARSER_VERSION,
            **source_metadata,
            "provenance_confirmed": False,
        }
        tasks.insert(
            0,
            Document(
                text=f"{_source_header(metadata)}\n" + "\n".join(preamble),
                metadata=metadata,
            ),
        )
    return tasks


def _is_heading(line: str) -> bool:
    normalized = " ".join(line.split())
    if not normalized or len(normalized) > 100:
        return False
    if re.match(r"^(SPIS TREŚCI|WSTĘP|WPROWADZENIE|ZAŁĄCZNIK)\b", normalized, re.IGNORECASE):
        return True
    if re.match(r"^\d+(?:\.\d+)*[.)]?\s+[A-ZĄĆĘŁŃÓŚŹŻ0-9]", normalized):
        return True
    letters = [character for character in normalized if character.isalpha()]
    return bool(letters) and len(letters) >= 4 and all(
        character.isupper() for character in letters
    )


def _clean_page_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse_pdf(path: Path) -> list[Document]:
    if document_type_for(path) == "requirements":
        return _requirements_documents(path)

    document_type = document_type_for(path)
    if document_type in {"exam_paper", "scoring_guide"}:
        return _task_documents(path, document_type)

    reader = PdfReader(str(path))
    documents = []
    current_section = None
    document_type = document_type_for(path)

    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_page_text(page.extract_text() or "")
        if not text:
            continue

        page_lines = text.splitlines()
        for line in page_lines:
            if _is_heading(line):
                current_section = line
                break

        metadata = {
            "file_name": path.name,
            "file_path": str(path),
            "page_number": page_number,
            "page_label": str(page_number),
            "document_type": document_type,
            "section": current_section or "",
            "parser_version": PARSER_VERSION,
        }
        metadata.update(_source_metadata(path, text))
        document_text = f"{_source_header(metadata)}\n{text}"
        documents.append(
            Document(
                text=document_text,
                metadata=metadata,
            )
        )

    return documents


def export_parsed_documents(data_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for path in sorted(data_dir.rglob("*.pdf")):
        for index, document in enumerate(parse_pdf(path), start=1):
            page_number = document.metadata.get("page_number")
            task_id = document.metadata.get("task_id")
            if task_id:
                safe_task_id = task_id.replace(".", "_")
                output_name = f"{path.stem}__task_{safe_task_id}.txt"
            else:
                output_name = f"{path.stem}__page_{page_number or index:04d}.txt"
            output_path = output_dir / output_name
            output_path.write_text(document.text, encoding="utf-8")
            manifest.append(
                {
                    "output_file": output_name,
                    "source": document.metadata,
                }
            )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path
