from types import SimpleNamespace

from src.rag.reranker import MetadataLexicalReranker


def _node(text, document_type, level, score=0.9):
    return SimpleNamespace(
        node=SimpleNamespace(
            metadata={"document_type": document_type, "level": level, "section": ""},
            get_content=lambda: text,
        ),
        score=score,
    )


def test_reranker_prefers_requested_level_and_document_type():
    nodes = [
        _node("funkcja kwadratowa z parametrem", "scoring_guide", "podstawowy"),
        _node("funkcja kwadratowa z parametrem", "exam_paper", "rozszerzony"),
    ]

    result = MetadataLexicalReranker(top_n=1).postprocess_nodes(
        nodes,
        query_str="Podaj konkretne zadanie z funkcji kwadratowej z parametrem z matury rozszerzonej",
    )

    assert result[0].node.metadata["document_type"] == "exam_paper"
    assert result[0].node.metadata["level"] == "rozszerzony"


def test_reranker_prefers_requirements_for_requirements_question():
    nodes = [
        _node("wymagania dla funkcji", "exam_paper", "rozszerzony"),
        _node("wymagania dla funkcji", "requirements", "podstawowy, rozszerzony"),
    ]

    result = MetadataLexicalReranker(top_n=1).postprocess_nodes(
        nodes,
        query_str="Jakie wymagania obowiązują na maturze rozszerzonej?",
    )

    assert result[0].node.metadata["document_type"] == "requirements"


def test_requirements_query_keeps_all_requirement_nodes():
    nodes = [
        _node("wymagania dla funkcji", "requirements", "rozszerzony"),
        _node("wymagania dla ciągów", "requirements", "podstawowy"),
        _node("zadanie z matury", "exam_paper", "rozszerzony"),
    ]

    result = MetadataLexicalReranker(top_n=1).postprocess_nodes(
        nodes,
        query_str="Jakie wymagania obowiązują na maturze rozszerzonej?",
    )

    assert len(result) == 2
    assert all(node.node.metadata["document_type"] == "requirements" for node in result)


def test_matura_query_prefers_exam_paper_over_informator():
    nodes = [
        _node("funkcja kwadratowa z parametrem", "exam_guide", "rozszerzony"),
        _node("funkcja kwadratowa z parametrem", "exam_paper", "rozszerzony"),
    ]

    result = MetadataLexicalReranker(top_n=1).postprocess_nodes(
        nodes,
        query_str="Podaj zadanie z matury rozszerzonej",
    )

    assert result[0].node.metadata["document_type"] == "exam_paper"


def test_official_exam_query_excludes_informator_and_other_sources():
    nodes = [
        _node("zadanie z funkcji", "exam_guide", "rozszerzony"),
        _node("zadanie z funkcji", "exam_paper", "rozszerzony"),
        _node("wymagania funkcji", "requirements", "rozszerzony"),
    ]
    for item in nodes:
        item.node.metadata["source_kind"] = {
            "exam_guide": "informator",
            "exam_paper": "official_exam",
            "requirements": "requirements",
        }[item.node.metadata["document_type"]]

    result = MetadataLexicalReranker(top_n=6).postprocess_nodes(
        nodes,
        query_str="Podaj zadanie z oficjalnej matury rozszerzonej",
    )

    assert len(result) == 1
    assert result[0].node.metadata["source_kind"] == "official_exam"