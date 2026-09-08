import re

from llama_index.core.postprocessor.types import BaseNodePostprocessor


_STOPWORDS = {
    "ale", "czy", "dla", "jak", "jaki", "jakie", "jest", "mam", "matura",
    "matematyki", "może", "nie", "podaj", "poziom", "przez", "przy", "tego",
    "to", "z", "za", "oraz", "zadan", "zadanie", "zadania",
}


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[\wąćęłńóśźż]{3,}", text.lower())
        if token.lower() not in _STOPWORDS
    }


class MetadataLexicalReranker(BaseNodePostprocessor):
    top_n: int = 6

    def __init__(self, top_n: int = 6, **kwargs):
        if top_n < 1:
            raise ValueError("top_n musi być większe od zera.")
        super().__init__(top_n=top_n, **kwargs)

    def _postprocess_nodes(self, nodes, query_bundle=None):
        query = getattr(query_bundle, "query_str", "") if query_bundle else ""
        query_tokens = _tokens(query)
        query_lower = query.lower()
        requirements_query = bool(
            {"wymagania", "obowiązują", "zakres"} & query_tokens
        )
        official_exam_query = any(
            phrase in query_lower
            for phrase in ("z matury", "z oficjalnej matury", "oficjalne zadanie", "zadanie maturalne")
        )
        informator_query = "informator" in query_lower
        ranked = []
        for node_with_score in nodes:
            metadata = node_with_score.node.metadata
            content = node_with_score.node.get_content()
            searchable = " ".join(
                [content, metadata.get("file_name", ""), metadata.get("section", "")]
            )
            overlap = len(query_tokens & _tokens(searchable))
            bonus = self._metadata_bonus(query_tokens, metadata)
            vector_score = node_with_score.score or 0.0
            ranked.append((overlap + bonus + vector_score * 0.1, node_with_score))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if requirements_query:
            requirement_nodes = [
                node for _, node in ranked
                if node.node.metadata.get("document_type") == "requirements"
            ]
            if requirement_nodes:
                return requirement_nodes
        if official_exam_query:
            exam_nodes = [
                node for _, node in ranked
                if node.node.metadata.get("source_kind") == "official_exam"
                or node.node.metadata.get("document_type") == "exam_paper"
            ]
            return exam_nodes[: self.top_n]
        if informator_query:
            guide_nodes = [
                node for _, node in ranked
                if node.node.metadata.get("source_kind") == "informator"
                or node.node.metadata.get("document_type") == "exam_guide"
            ]
            return guide_nodes[: self.top_n]
        return [node for _, node in ranked[: self.top_n]]

    @staticmethod
    def _metadata_bonus(query_tokens: set[str], metadata: dict) -> float:
        document_type = metadata.get("document_type", "")
        level = metadata.get("level", "")
        bonus = 0.0

        if {"wymagania", "obowiązują", "zakres"} & query_tokens:
            bonus += 3.0 if document_type == "requirements" else -1.0
        if {"wzory", "wzór", "dostępne"} & query_tokens:
            bonus += 3.0 if document_type == "formula_sheet" else 0.0
        if {"arkusz", "konkretne", "oficjalne"} & query_tokens:
            bonus += 2.0 if document_type == "exam_paper" else 0.0
        if {"matury", "maturę", "oficjalnej"} & query_tokens:
            bonus += 4.0 if document_type == "exam_paper" else -2.0
        if {"punktacja", "ocena", "klucz", "punkty"} & query_tokens:
            bonus += 2.0 if document_type == "scoring_guide" else 0.0
        if "rozszerzonej" in query_tokens or "rozszerzony" in query_tokens:
            bonus += 3.0 if "rozszerzony" in level else -1.0
        if "podstawowej" in query_tokens or "podstawowy" in query_tokens:
            bonus += 3.0 if "podstawowy" in level else -1.0
        return bonus