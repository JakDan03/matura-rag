from src.services.session_service import SessionService
from src.storage.session_repository import SessionRepository


def test_application_session_flow_creates_and_switches_conversations(tmp_path):
    service = SessionService(SessionRepository(tmp_path / "sessions.sqlite3"))

    first_id = service.ensure_current()
    service.repository.add_message(first_id, "user", "Pytanie z pierwszej rozmowy")
    second_id = service.create_new()
    service.repository.add_message(second_id, "user", "Pytanie z drugiej rozmowy")

    assert second_id != first_id
    assert service.ensure_current(first_id) == first_id
    assert service.load_messages(first_id)[0]["content"] == "Pytanie z pierwszej rozmowy"
    assert service.ensure_current(second_id) == second_id
    assert service.load_messages(second_id)[0]["content"] == "Pytanie z drugiej rozmowy"


def test_deleted_current_conversation_falls_back_to_existing_one(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    service = SessionService(repository)
    first_id = service.create_new()
    second_id = service.create_new()
    repository.delete_conversation(second_id)

    assert service.ensure_current(second_id) == first_id
