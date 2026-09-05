from types import SimpleNamespace

import pytest

from src.rag.metrics import measure_retrieval


def test_retrieval_metrics_measure_context_and_scores():
    nodes = [
        SimpleNamespace(node=SimpleNamespace(get_content=lambda: "abcd"), score=0.8),
        SimpleNamespace(node=SimpleNamespace(get_content=lambda: "efghij"), score=0.4),
    ]

    metrics = measure_retrieval(nodes)

    assert metrics.node_count == 2
    assert metrics.context_characters == 10
    assert metrics.context_tokens_estimate == 2
    assert metrics.score_min == 0.4
    assert metrics.score_max == 0.8
    assert metrics.score_average == pytest.approx(0.6)


def test_retrieval_metrics_support_empty_context():
    metrics = measure_retrieval([])

    assert metrics.as_dict() == {
        "node_count": 0,
        "context_characters": 0,
        "context_tokens_estimate": 0,
        "score_min": None,
        "score_max": None,
        "score_average": None,
    }
