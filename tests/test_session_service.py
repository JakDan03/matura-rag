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
    repository.add_message(first_id, "user", "Pierwsze pytanie")
    second_id = service.create_new()
    repository.delete_conversation(second_id)

    assert service.ensure_current(second_id) == first_id


def test_new_chat_reuses_the_only_empty_conversation(tmp_path):
    service = SessionService(SessionRepository(tmp_path / "sessions.sqlite3"))

    first_id = service.create_new()
    second_id = service.create_new()

    assert second_id == first_id
    assert len(service.list_conversations()) == 1


def test_chat_name_is_manual_and_survives_messages(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    service = SessionService(repository)
    conversation_id = service.create_new()

    service.rename(conversation_id, "  Geometria - powtórka  ")
    repository.add_message(conversation_id, "user", "Ile wynosi pole koła?")

    assert service.list_conversations() == [(conversation_id, "Geometria - powtórka")]


def test_chat_name_cannot_be_empty(tmp_path):
    service = SessionService(SessionRepository(tmp_path / "sessions.sqlite3"))
    conversation_id = service.create_new()

    try:
        service.rename(conversation_id, "   ")
    except ValueError as error:
        assert str(error) == "Nazwa rozmowy nie może być pusta."
    else:
        raise AssertionError("Pusta nazwa powinna zostać odrzucona")


def test_existing_empty_conversations_are_consolidated(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    first_id = repository.create_conversation()
    second_id = repository.create_conversation()
    service = SessionService(repository)

    current_id = service.ensure_current(second_id)

    assert current_id == second_id
    assert repository.list_empty_conversations() == [second_id]
    assert repository.list_conversations() == [(second_id, "Nowa rozmowa")]


def test_new_chat_removes_stale_empty_chat_when_current_has_messages(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    service = SessionService(repository)
    current_id = service.create_new()
    repository.add_message(current_id, "user", "Aktualne pytanie")
    stale_empty_id = service.create_new(current_id)

    new_id = service.create_new(current_id)

    assert new_id != current_id
    assert new_id != stale_empty_id
    assert repository.list_empty_conversations() == [new_id]
