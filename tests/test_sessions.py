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
            "visualization": {},
        }
    ]


def test_session_can_be_deleted(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    conversation_id = repository.create_conversation()
    repository.add_message(conversation_id, "user", "Ile to 2 + 2?")

    repository.delete_conversation(conversation_id)

    assert repository.list_conversations() == []


def test_history_lists_only_non_empty_conversations(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    empty_id = repository.create_conversation()
    saved_id = repository.create_conversation("Geometria")
    repository.add_message(saved_id, "user", "Pytanie")

    assert repository.list_non_empty_conversations() == [(saved_id, "Geometria")]
    assert empty_id not in [conversation_id for conversation_id, _ in repository.list_non_empty_conversations()]


def test_visualization_is_persisted_with_message(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    conversation_id = repository.create_conversation()
    visualization = {"type": "circle", "radius": 1.0}

    repository.add_message(conversation_id, "assistant", "Wygenerowano okrąg.", visualization=visualization)

    assert repository.get_messages(conversation_id)[0]["visualization"] == visualization


def test_first_user_message_sets_short_chat_title(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    conversation_id = repository.create_conversation()

    repository.add_message(
        conversation_id,
        "user",
        "  Jak obliczyć pole koła?\nPotrzebuję krótkiego wyjaśnienia.  ",
    )
    repository.add_message(conversation_id, "assistant", "Odpowiedź")

    title = repository.list_conversations()[0][1]
    assert title == "Jak obliczyć pole koła? Potrzebuję krótkiego wyjaśnienia."


def test_first_user_message_title_is_limited_and_manual_name_wins(tmp_path):
    repository = SessionRepository(tmp_path / "sessions.sqlite3")
    auto_named_id = repository.create_conversation()
    manual_named_id = repository.create_conversation()
    repository.rename_conversation(manual_named_id, "Moja geometria")

    repository.add_message(auto_named_id, "user", "x" * 100)
    repository.add_message(manual_named_id, "user", "Pierwsze pytanie")

    titles = dict(repository.list_conversations())
    assert titles[auto_named_id] == "x" * 60
    assert titles[manual_named_id] == "Moja geometria"
