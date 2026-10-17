from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence


class LocalEmbeddingService:
    """Lightweight deterministic & semantic embedding generator.
    
    Produces normalized 128-dimensional dense vectors using character n-gram hashing
    and term weighting. Ensures fast execution without external dependencies.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        tokens = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.dimension
        if not tokens:
            return vec

        for tok in tokens:
            # Hash token and sub-grams to distribute across dimensions
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            vec[idx] += 1.0

            # Bigram influence
            for i in range(len(tok) - 2):
                gram = tok[i : i + 3]
                h_gram = int(hashlib.sha256(gram.encode("utf-8")).hexdigest(), 16)
                vec[h_gram % self.dimension] += 0.5

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)
