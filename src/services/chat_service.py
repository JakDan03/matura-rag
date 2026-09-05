class ChatService:
    def __init__(self, index, system_prompt: str):
        self.engine = index.as_chat_engine(
            chat_mode="condense_question",
            system_prompt=system_prompt,
            verbose=True,
        )

    def ask(self, question: str) -> dict:
        response = self.engine.chat(question)
        sources = []
        for source_node in getattr(response, "source_nodes", []):
            metadata = source_node.node.metadata
            sources.append(
                {
                    "file": metadata.get("file_name", "Nieznany dokument"),
                    "page": metadata.get("page_label") or metadata.get("page_number"),
                }
            )
        return {"answer": response.response, "sources": sources}
