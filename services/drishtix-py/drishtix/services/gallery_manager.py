"""
DrishtiX v4.0 — In-Memory Gallery Manager.

Maintains the active watchlist embeddings in a contiguous NumPy matrix for
sub-millisecond SIMD vectorized cosine matching against incoming faces.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from drishtix.core.constants import DEFAULT_MATCH_THRESHOLD, SFACE_EMBEDDING_DIM
from drishtix.core.enums import TargetCategory
from drishtix.core.signals import signal_bus
from drishtix.dao.embedding_dao import EmbeddingDAO
from drishtix.dao.session import get_session
from drishtix.dao.target_dao import TargetDAO
from drishtix.models.face_embedding import FaceEmbedding
from drishtix.models.target_registry import TargetRegistry
from drishtix.utils.vector_math import batch_cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class TargetProfile:
    """Lightweight in-memory profile of a registered watchlist target."""

    target_id: int
    full_name: str
    category: str
    case_number: Optional[str]
    description: Optional[str]
    profile_image_path: Optional[str]


@dataclass
class MatchResult:
    """Result of a gallery match lookup."""

    target: TargetProfile
    confidence: float
    embedding_id: int


class GalleryManager:
    """
    In-memory vectorized gallery of target embeddings.

    Maintains:
    1. `_matrix`: (N, 128) float32 NumPy array containing all registered embeddings.
    2. `_target_ids`: List of target_ids corresponding to each row in `_matrix`.
    3. `_embedding_ids`: List of embedding_ids corresponding to each row.
    4. `_targets`: Dict[target_id, TargetProfile] for quick profile lookup.
    """

    _instance: Optional["GalleryManager"] = None

    def __init__(self, match_threshold: float = DEFAULT_MATCH_THRESHOLD) -> None:
        self.match_threshold = float(match_threshold)
        self._matrix: np.ndarray = np.empty((0, SFACE_EMBEDDING_DIM), dtype=np.float32)
        self._target_ids: List[int] = []
        self._embedding_ids: List[int] = []
        self._targets: Dict[int, TargetProfile] = {}

    @classmethod
    def get_instance(cls) -> "GalleryManager":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = GalleryManager()
        return cls._instance

    def set_match_threshold(self, threshold: float) -> None:
        """Update match threshold."""
        self.match_threshold = float(threshold)

    def reload_gallery(self) -> int:
        """
        Reload all active targets and embeddings from the SQLite database.

        Returns:
            Number of active embeddings loaded.
        """
        logger.info("Reloading watchlist gallery from database...")
        with get_session() as session:
            targets = TargetDAO.get_all(session, active_only=True)
            active_ids = {t.target_id for t in targets}

            new_targets: Dict[int, TargetProfile] = {}
            for t in targets:
                new_targets[t.target_id] = TargetProfile(
                    target_id=t.target_id,
                    full_name=t.full_name,
                    category=t.category,
                    case_number=t.case_number,
                    description=t.description,
                    profile_image_path=t.profile_image_path,
                )

            embeddings = EmbeddingDAO.get_all_active_embeddings(session)

            vectors: List[np.ndarray] = []
            target_ids: List[int] = []
            embedding_ids: List[int] = []

            for emb in embeddings:
                if emb.target_id in active_ids:
                    v = emb.get_vector()
                    if v.shape == (SFACE_EMBEDDING_DIM,):
                        vectors.append(v)
                        target_ids.append(emb.target_id)
                        embedding_ids.append(emb.embedding_id)

            if vectors:
                self._matrix = np.vstack(vectors).astype(np.float32)
            else:
                self._matrix = np.empty((0, SFACE_EMBEDDING_DIM), dtype=np.float32)

            self._target_ids = target_ids
            self._embedding_ids = embedding_ids
            self._targets = new_targets

            count = len(vectors)
            logger.info("Gallery reloaded: %d embeddings across %d targets", count, len(new_targets))
            signal_bus.gallery_reloaded.emit(len(new_targets))
            return count

    def match_embedding(
        self,
        query_vector: np.ndarray,
        threshold_override: Optional[float] = None,
    ) -> Optional[MatchResult]:
        """
        Search the gallery for the best match for the query vector.

        Uses vectorized SIMD batch cosine similarity for ~0.1ms search times.

        Args:
            query_vector: 128-dimensional query embedding.
            threshold_override: Optional custom threshold to override default.

        Returns:
            MatchResult if similarity >= threshold, else None.
        """
        if self._matrix.size == 0 or query_vector is None:
            return None

        threshold = threshold_override if threshold_override is not None else self.match_threshold

        # Compute batch similarities against all gallery vectors
        similarities = batch_cosine_similarity(query_vector, self._matrix)
        if len(similarities) == 0:
            return None

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            target_id = self._target_ids[best_idx]
            embedding_id = self._embedding_ids[best_idx]
            profile = self._targets.get(target_id)

            if profile is not None:
                return MatchResult(
                    target=profile,
                    confidence=best_score,
                    embedding_id=embedding_id,
                )

        return None

    def get_target_count(self) -> int:
        """Return total active targets in memory."""
        return len(self._targets)

    def get_embedding_count(self) -> int:
        """Return total active embedding vectors in memory."""
        return len(self._target_ids)
