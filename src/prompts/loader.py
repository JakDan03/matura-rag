import json
from pathlib import Path


class PromptLoader:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        with (prompts_dir / "roles.json").open(encoding="utf-8") as file:
            self.roles = json.load(file)

    def role_choices(self) -> dict[str, str]:
        return {key: value["label"] for key, value in self.roles.items()}

    def load_role(self, role_name: str) -> str:
        role = self.roles[role_name]
        return (self.prompts_dir / role["file"]).read_text(encoding="utf-8").strip()

    def build_system_prompt(self, role_name: str, student_context: str = "") -> str:
        base_prompt = """Jesteś profesjonalnym tutorem i egzaminatorem CKE z matematyki.
Odpowiadaj wyłącznie na podstawie dostarczonych materiałów: Karty Wzorów, Informatorów CKE i Zasad Oceniania.
Jeśli nie ma odpowiedzi w materiałach, powiedz to wprost i nie wymyślaj źródeł.
Podając wzór, wskaż jego dział z Karty Wzorów CKE.
Gdy oceniasz zadanie, stosuj oficjalne kryteria punktowania CKE.
Formatuj wzory matematyczne jako LaTeX między znakami $...$.
"""
        parts = [base_prompt, self.load_role(role_name)]
        if student_context.strip():
            parts.append(f"Dodatkowy kontekst ucznia:\n{student_context.strip()}")
        return "\n\n".join(parts)
