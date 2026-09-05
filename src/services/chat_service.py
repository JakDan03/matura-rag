from llama_index.core import Settings
from llama_index.core.postprocessor import SimilarityPostprocessor

from src.rag.metrics import measure_retrieval


class ChatService:
    def __init__(
        self,
        index,
        system_prompt: str,
        retrieval_top_k: int = 2,
        similarity_cutoff: float = 0.2,
        llm=None,
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
        self.llm = llm

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

    def explain_math(self, question: str, verified_result: str) -> str:
        # TODO: Replace the plain string contract with a generic SolutionResponse:
        # task_type, method, interpretation, steps, result, visualizations, sources.
        # Method-specific details (delta, geometry, derivatives, probability, etc.)
        # should live in typed payloads inside that common response.
        # The LLM should explain and format the verified tool result, while
        # deterministic tools such as SymPy remain responsible for validation.
        prompt = f"""Jesteś nauczycielem matematyki przygotowującym rozwiązanie dla ucznia.
Rozwiąż zadanie krok po kroku i używaj LaTeX między znakami $...$.
Jeżeli użytkownik prosi o deltę (delta), pokaż metodę delty: wskaż a, b, c, oblicz deltę,
wyznacz pierwiastki i podaj odpowiedź końcową.
Nie pomijaj rachunków. Nie twórz fikcyjnych danych.

Treść zadania użytkownika:
{question}

Wynik zweryfikowany przez SymPy:
{verified_result}

Zwróć wyłącznie gotowe, czytelne rozwiązanie dla ucznia.
"""
        response = (self.llm or Settings.llm).complete(prompt)
        return str(response)
