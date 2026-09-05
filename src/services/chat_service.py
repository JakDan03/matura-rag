from llama_index.core.postprocessor import SimilarityPostprocessor

from src.rag.metrics import measure_retrieval


class ChatService:
    def __init__(
        self,
        index,
        system_prompt: str,
        retrieval_top_k: int = 2,
        similarity_cutoff: float = 0.2,
    ):
        if retrieval_top_k < 1:
            raise ValueError("retrieval_top_k musi być większe od zera.")
        if not 0 <= similarity_cutoff <= 1:
            raise ValueError("similarity_cutoff musi być w zakresie od 0 do 1.")
        self.engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            system_prompt=system_prompt,
            similarity_top_k=retrieval_top_k,
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
            ],
            verbose=True,
        )

    def ask(self, question: str) -> dict:
        response = self.engine.chat(question)
        source_nodes = list(getattr(response, "source_nodes", []))
        sources = []
        for source_node in source_nodes:
            metadata = source_node.node.metadata
            sources.append(
                {
                    "file": metadata.get("file_name", "Nieznany dokument"),
                    "page": metadata.get("page_label") or metadata.get("page_number"),
                    "score": source_node.score,
                }
            )
        return {
            "answer": response.response,
            "sources": sources,
            "retrieval_metrics": measure_retrieval(source_nodes).as_dict(),
        }
