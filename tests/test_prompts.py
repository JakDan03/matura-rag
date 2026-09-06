from config.settings import settings
from src.prompts.loader import PromptLoader


def test_prompt_roles_are_loaded():
    loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

    assert set(loader.role_choices()) == {"tutor", "examiner"}
    prompt = loader.build_system_prompt("tutor")
    assert "CKE" in prompt
    assert "data/wymagania/" in prompt
    assert "Rzeczywiste arkusze" in prompt


def test_student_context_is_injected():
    loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

    prompt = loader.build_system_prompt("tutor", "Poziom podstawowy")

    assert "Poziom podstawowy" in prompt
