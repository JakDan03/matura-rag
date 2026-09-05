from __future__ import annotations

from src.storage.session_repository import SessionRepository


class SessionService:
    def __init__(self, repository: SessionRepository):
        self.repository = repository

    def ensure_current(self, conversation_id: int | None = None) -> int:
        self._consolidate_empty_conversations(conversation_id)
        conversations = self.repository.list_conversations()
        available_ids = {item_id for item_id, _ in conversations}
        if conversation_id in available_ids:
            return conversation_id
        if conversations:
            return conversations[0][0]
        return self.repository.create_conversation()

    def create_new(self, current_conversation_id: int | None = None) -> int:
        self._consolidate_empty_conversations(current_conversation_id)
        empty_conversations = self.repository.list_empty_conversations()
        if current_conversation_id in empty_conversations:
            return current_conversation_id
        if current_conversation_id is None and empty_conversations:
            return empty_conversations[0]
        for conversation_id in empty_conversations:
            self.repository.delete_conversation(conversation_id)
        return self.repository.create_conversation()

    def _consolidate_empty_conversations(self, preferred_id: int | None = None):
        empty_conversations = self.repository.list_empty_conversations()
        if len(empty_conversations) < 2:
            return
        keep_id = preferred_id if preferred_id in empty_conversations else empty_conversations[0]
        for conversation_id in empty_conversations:
            if conversation_id != keep_id:
                self.repository.delete_conversation(conversation_id)

    def list_conversations(self) -> list[tuple[int, str]]:
        return self.repository.list_conversations()

    def list_non_empty_conversations(self) -> list[tuple[int, str]]:
        return self.repository.list_non_empty_conversations()

    def load_messages(self, conversation_id: int) -> list[dict]:
        return self.repository.get_messages(conversation_id)

    def rename(self, conversation_id: int, title: str):
        self.repository.rename_conversation(conversation_id, title)
