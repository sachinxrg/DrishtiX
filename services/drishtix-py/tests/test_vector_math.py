"""Unit tests for vector mathematics and SIMD cosine similarity."""

import numpy as np
from drishtix.utils.vector_math import (
    batch_cosine_similarity,
    cosine_similarity,
    normalize_l2,
)


def test_normalize_l2():
    vec = np.array([3.0, 4.0, 0.0], dtype=np.float32)
    normed = normalize_l2(vec)
    assert np.isclose(np.linalg.norm(normed), 1.0)
    assert np.allclose(normed, np.array([0.6, 0.8, 0.0], dtype=np.float32))


def test_cosine_similarity_identical():
    vec = np.random.randn(128).astype(np.float32)
    score = cosine_similarity(vec, vec)
    assert np.isclose(score, 1.0, atol=1e-5)


def test_cosine_similarity_orthogonal():
    v1 = np.zeros(128, dtype=np.float32)
    v2 = np.zeros(128, dtype=np.float32)
    v1[0] = 1.0
    v2[1] = 1.0
    score = cosine_similarity(v1, v2)
    assert np.isclose(score, 0.0, atol=1e-5)


def test_batch_cosine_similarity():
    # 10 gallery targets of 128 dimensions
    gallery = np.random.randn(10, 128).astype(np.float32)
    # Normalize gallery
    for i in range(10):
        gallery[i] = normalize_l2(gallery[i])

    # Query is identical to row 3
    query = gallery[3].copy()
    sims = batch_cosine_similarity(query, gallery)

    assert len(sims) == 10
    assert np.isclose(sims[3], 1.0, atol=1e-5)
    best_match_idx = np.argmax(sims)
    assert best_match_idx == 3
