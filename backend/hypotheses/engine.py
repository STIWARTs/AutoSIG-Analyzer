from __future__ import annotations

from backend.types import Hypothesis


def build_hypotheses(probabilities: dict[str, float], top_k: int = 2) -> list[Hypothesis]:
    """Rank only MVP configurations from the trained model's probability vector."""
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:top_k]
    return [Hypothesis(rank=index + 1, modulation=modulation, interleaving="Block",
                       fec="Convolutional / Viterbi", score=float(score))
            for index, (modulation, score) in enumerate(ranked)]
