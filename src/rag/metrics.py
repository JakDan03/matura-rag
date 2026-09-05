from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    node_count: int
    context_characters: int
    context_tokens_estimate: int
    score_min: float | None
    score_max: float | None
    score_average: float | None

    def as_dict(self) -> dict:
        return {
            "node_count": self.node_count,
            "context_characters": self.context_characters,
            "context_tokens_estimate": self.context_tokens_estimate,
            "score_min": self.score_min,
            "score_max": self.score_max,
            "score_average": self.score_average,
        }


def measure_retrieval(source_nodes) -> RetrievalMetrics:
    context_characters = sum(
        len(source_node.node.get_content()) for source_node in source_nodes
    )
    scores = [
        float(source_node.score)
        for source_node in source_nodes
        if source_node.score is not None
    ]
    return RetrievalMetrics(
        node_count=len(source_nodes),
        context_characters=context_characters,
        context_tokens_estimate=max(0, round(context_characters / 4)),
        score_min=min(scores) if scores else None,
        score_max=max(scores) if scores else None,
        score_average=sum(scores) / len(scores) if scores else None,
    )
