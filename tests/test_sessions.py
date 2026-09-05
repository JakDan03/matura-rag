from src.storage.session_repository import SessionRepository


def test_session_messages_round_trip(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    conversation_id = repository.create_conversation()

    repository.add_message(
        conversation_id,
        "assistant",
        "Wynik to 4.",
        [{"file": "wzory.pdf", "page": "4"}],
    )

    assert repository.get_messages(conversation_id) == [
        {
            "role": "assistant",
            "content": "Wynik to 4.",
            "sources": [{"file": "wzory.pdf", "page": "4"}],
        }
    ]


def test_session_can_be_deleted(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    conversation_id = repository.create_conversation()
    repository.add_message(conversation_id, "user", "Ile to 2 + 2?")

    repository.delete_conversation(conversation_id)

    assert repository.list_conversations() == []
