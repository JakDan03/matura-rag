from __future__ import annotations

from src.storage.session_repository import SessionRepository


class SessionService:
    def __init__(self, repository: SessionRepository):
        self.repository = repository

    def ensure_current(self, conversation_id: int | None = None) -> int:
        conversations = self.repository.list_conversations()
        available_ids = {item_id for item_id, _ in conversations}
        if conversation_id in available_ids:
            return conversation_id
        if conversations:
            return conversations[0][0]
        return self.repository.create_conversation()

    def create_new(self) -> int:
        return self.repository.create_conversation()

    def list_conversations(self) -> list[tuple[int, str]]:
        return self.repository.list_conversations()

    def load_messages(self, conversation_id: int) -> list[dict]:
        return self.repository.get_messages(conversation_id)
