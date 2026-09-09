from config.settings import settings
from src.prompts.loader import PromptLoader


def test_prompt_roles_are_loaded():
    loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

    assert set(loader.role_choices()) == {"tutor", "examiner"}
    prompt = loader.build_system_prompt("tutor")
    assert "CKE" in prompt
    assert "data/wymagania/" in prompt
    assert "Rzeczywiste arkusze" in prompt


def test_tutor_prompt_requires_explicit_request_before_full_solution():
    loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

    prompt = loader.build_system_prompt("tutor")

    assert "nie podawaj od razu pełnego rozwiązania" in prompt
    assert "samo wklejenie zadania nie są prośbą o pełne rozwiązanie" in prompt
    assert "Nie traktuj obecności treści zadania w kontekście RAG" in prompt
    assert "Odpowiedź będąca wskazówką nie może zawierać pełnego rachunku" in prompt
    assert "podaj numer strony wskazany w nagłówku" in prompt


def test_prompt_requires_explicit_handling_of_missing_graphics():
    loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

    prompt = loader.build_system_prompt("tutor")

    assert "której treści nie ma w przekazanym kontekście" in prompt
    assert "Nie odtwarzaj z pamięci szczegółów grafiki" in prompt
    assert "Poproś o obraz lub dane odczytane z grafiki" in prompt


def test_student_context_is_injected():
    loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

    prompt = loader.build_system_prompt("tutor", "Poziom podstawowy")

    assert "Poziom podstawowy" in prompt
