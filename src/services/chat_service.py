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
        prompt = f"""Jesteś nauczycielem matematyki przygotowującym dydaktyczne rozwiązanie zadania.

    Twoim zadaniem jest objaśnić wynik dostarczony przez narzędzie, a nie zastąpić jego walidację.
    Obsługuj różne typy zadań: równania, nierówności, funkcje, geometrię, prawdopodobieństwo,
    ciągi, pochodne i zadania tekstowe. Jeśli narzędzie podało zbyt mało informacji, możesz
    samodzielnie wygenerować brakujące, sprawdzalne kroki, ale nie twórz fikcyjnych danych.

    Zasady:
    - najpierw krótko zinterpretuj treść zadania i określ, co należy wyznaczyć;
    - domyślnie wybierz metodę najczęściej stosowaną w podobnych zadaniach i zasadach oceniania;
    - jeśli uczeń narzucił metodę, zastosuj ją albo wyjaśnij, dlaczego nie można jej zastosować;
    - pokaż sprawdzalne kroki rachunkowe, założenia, dziedzinę i odrzucenie niedozwolonych wyników;
    - przy metodzie delty (delta) wskaż a, b, c, oblicz deltę, wyznacz pierwiastki i podaj odpowiedź;
    - jeśli treść ma więcej niż jedną rozsądną interpretację, rozstrzygnij ją tylko wtedy, gdy
      kontekst jednoznacznie na to pozwala; w przeciwnym razie zadaj uczniowi krótkie pytanie;
    - oznacz zależności spoza karty wzorów, jeśli ich używasz;
    - używaj LaTeX między znakami $...$ i nie ujawniaj surowego toku wewnętrznego rozumowania.

    Treść zadania użytkownika:
    {question}

    Wynik zweryfikowany przez SymPy lub inne narzędzie matematyczne:
    {verified_result}

    Zwróć wyłącznie gotowe, czytelne rozwiązanie dla ucznia z krótkimi nagłówkami:
    Interpretacja, Metoda, Kroki, Wynik.
    """
        response = (self.llm or Settings.llm).complete(prompt)
        return str(response)
