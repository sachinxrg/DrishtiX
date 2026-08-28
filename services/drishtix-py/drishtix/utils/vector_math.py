"""
DrishtiX v4.0 — Vector mathematics utilities.

High-performance vector operations for SFace 128-dimensional embeddings.
Replaces Java's VectorMathUtil with NumPy-accelerated SIMD calculations.
"""

import numpy as np


def normalize_l2(vector: np.ndarray) -> np.ndarray:
    """
    Perform L2 normalization on a vector.

    Args:
        vector: Input numpy array (e.g. shape (128,)).

    Returns:
        L2 normalized vector with unit length.
    """
    norm = np.linalg.norm(vector)
    if norm == 0 or np.isnan(norm):
        return vector
    return vector / norm


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D embedding vectors.

    Args:
        v1: First embedding vector (128-dim).
        v2: Second embedding vector (128-dim).

    Returns:
        Cosine similarity score between -1.0 and 1.0 (typically 0.0 to 1.0).
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def batch_cosine_similarity(query: np.ndarray, gallery_matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarities of a query vector against all rows in a matrix.

    Vectorized using matrix-vector multiplication for ultra-fast scanning
    (e.g., matching a face against 10,000 targets in < 1ms).

    Args:
        query: 1D vector of shape (D,) (e.g., 128).
        gallery_matrix: 2D matrix of shape (N, D) where each row is an embedding.

    Returns:
        1D array of shape (N,) with cosine similarity scores.
    """
    if gallery_matrix.size == 0 or query.size == 0:
        return np.array([], dtype=np.float32)

    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return np.zeros(gallery_matrix.shape[0], dtype=np.float32)

    norm_query = query / query_norm

    # Calculate row-wise norms of gallery_matrix
    row_norms = np.linalg.norm(gallery_matrix, axis=1)
    # Avoid divide-by-zero
    row_norms = np.where(row_norms == 0, 1e-10, row_norms)

    # Dot product divided by row norms
    sims = np.dot(gallery_matrix, norm_query) / row_norms
    return sims
