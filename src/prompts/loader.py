import json
from pathlib import Path


class PromptLoader:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        with (prompts_dir / "roles.json").open(encoding="utf-8") as file:
            self.roles = json.load(file)
        with (prompts_dir / "source_catalog.json").open(encoding="utf-8") as file:
            self.source_catalog = json.load(file)

    def role_choices(self) -> dict[str, str]:
        return {key: value["label"] for key, value in self.roles.items()}

    def load_role(self, role_name: str) -> str:
        role = self.roles[role_name]
        return (self.prompts_dir / role["file"]).read_text(encoding="utf-8").strip()

    def load_prompt(self, file_name: str) -> str:
        return (self.prompts_dir / file_name).read_text(encoding="utf-8").strip()

    def build_system_prompt(self, role_name: str, student_context: str = "") -> str:
        catalog = json.dumps(self.source_catalog, ensure_ascii=False, indent=2)
        base_prompt = self.load_prompt("base.md") + "\n" + catalog
        parts = [base_prompt, self.load_role(role_name)]
        if student_context.strip():
            parts.append(f"Dodatkowy kontekst ucznia:\n{student_context.strip()}")
        return "\n\n".join(parts)
