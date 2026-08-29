"""
DrishtiX v4.0 — In-Memory Gallery Manager.

Maintains the active watchlist embeddings in a contiguous NumPy matrix for
sub-millisecond SIMD vectorized cosine matching against incoming faces.
Dynamically accommodates both 128-D (SFace) and 512-D (InsightFace ArcFace) vectors.

Thread Safety:
    - Singleton accessor is guarded by a threading.Lock.
    - reload_gallery() uses an atomic-swap pattern: new state is built in local
      variables, then all four attributes are reassigned in a single statement.
      Python's GIL guarantees attribute assignment is atomic for simple names,
      so concurrent match_embedding() readers see either the old or new state,
      never a partially-updated mix.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from drishtix.core.constants import DEFAULT_MATCH_THRESHOLD
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
    estimated_age: Optional[int] = None
    gender: Optional[str] = None


@dataclass
class MatchResult:
    """Result of a gallery match lookup."""

    target: TargetProfile
    confidence: float
    embedding_id: int
    matched_dim: int = 128


class GalleryManager:
    """
    In-memory vectorized gallery of target embeddings.

    Maintains:
    1. `_matrix`: (N, D) float32 NumPy array containing active embeddings (D=128 or D=512).
    2. `_target_ids`: List of target_ids corresponding to each row in `_matrix`.
    3. `_embedding_ids`: List of embedding_ids corresponding to each row.
    4. `_targets`: Dict[target_id, TargetProfile] for quick profile lookup.
    """

    _instance: Optional["GalleryManager"] = None
    _singleton_lock = threading.Lock()

    def __init__(self, match_threshold: float = DEFAULT_MATCH_THRESHOLD) -> None:
        self.match_threshold = float(match_threshold)
        self._matrix: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self._target_ids: List[int] = []
        self._embedding_ids: List[int] = []
        self._targets: Dict[int, TargetProfile] = {}

    @classmethod
    def get_instance(cls) -> "GalleryManager":
        """Thread-safe singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = GalleryManager()
            return cls._instance

    def set_match_threshold(self, threshold: float) -> None:
        """Update match threshold."""
        self.match_threshold = float(threshold)

    def reload_gallery(self, target_dim: Optional[int] = None) -> int:
        """
        Reload all active targets and embeddings from the SQLite database.

        Multi-face Template Averaging (F6):
            When a target has N embeddings, they are L2-averaged into a single
            centroid vector. This produces a more robust template than any
            individual image, reducing false negatives from pose/lighting
            variation. The gallery matrix then has one row per target (not
            one row per image), which also speeds up matching.

        Uses atomic swap: new state is built in local variables and then
        assigned in a single compound statement. Concurrent match_embedding()
        calls will see either the old or new state, never a mix.

        Returns:
            Number of active target templates loaded.
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

            # Group embeddings by target_id for multi-face averaging (F6)
            from collections import defaultdict
            target_vectors: Dict[int, List[np.ndarray]] = defaultdict(list)
            target_embedding_ids: Dict[int, int] = {}  # Keep first embedding_id per target

            for emb in embeddings:
                if emb.target_id in active_ids:
                    v = emb.get_vector()
                    dim = v.shape[0] if v.ndim == 1 else 0
                    if dim in (128, 512):
                        if target_dim is None or dim == target_dim:
                            target_vectors[emb.target_id].append(v)
                            if emb.target_id not in target_embedding_ids:
                                target_embedding_ids[emb.target_id] = emb.embedding_id

            # Build averaged centroid vectors — one per target
            vectors: List[np.ndarray] = []
            target_ids: List[int] = []
            embedding_ids: List[int] = []

            for tid, vecs in target_vectors.items():
                if len(vecs) == 1:
                    centroid = vecs[0]
                else:
                    # Average all embeddings for this target, then re-normalize
                    stacked = np.vstack(vecs).astype(np.float32)
                    centroid = stacked.mean(axis=0)
                    norm = np.linalg.norm(centroid)
                    if norm > 1e-12:
                        centroid = centroid / norm
                    centroid = centroid.astype(np.float32)
                    logger.debug(
                        "Target %d: averaged %d embeddings into centroid template",
                        tid, len(vecs),
                    )

                vectors.append(centroid)
                target_ids.append(tid)
                embedding_ids.append(target_embedding_ids[tid])

            # Build new state in local variables
            if vectors:
                first_dim = vectors[0].shape[0]
                valid_vectors = [v for v in vectors if v.shape[0] == first_dim]
                if len(valid_vectors) < len(vectors):
                    logger.warning("Filtered mixed embedding dimensions to match predominant (%d-D)", first_dim)
                new_matrix = np.vstack(valid_vectors).astype(np.float32)
                new_target_ids = [target_ids[i] for i, v in enumerate(vectors) if v.shape[0] == first_dim]
                new_embedding_ids = [embedding_ids[i] for i, v in enumerate(vectors) if v.shape[0] == first_dim]
            else:
                new_matrix = np.empty((0, 0), dtype=np.float32)
                new_target_ids = []
                new_embedding_ids = []

            # Atomic swap — Python's GIL makes tuple assignment atomic, so
            # concurrent readers in match_embedding() see either old or new state.
            self._matrix, self._target_ids, self._embedding_ids, self._targets = (
                new_matrix, new_target_ids, new_embedding_ids, new_targets
            )

            count = len(new_target_ids)
            total_embeddings = sum(len(v) for v in target_vectors.values())
            logger.info(
                "Gallery reloaded: %d targets (%d raw embeddings → %d centroid templates)",
                len(new_targets), total_embeddings, count,
            )

            # Audit trail for gallery reload
            try:
                from drishtix.dao.audit_dao import AuditDAO
                AuditDAO.log_action(
                    session=session,
                    action="GALLERY_RELOADED",
                    entity_type="GalleryManager",
                    details=f"Loaded {count} centroid templates from {total_embeddings} embeddings across {len(new_targets)} targets",
                )
            except Exception as e:
                logger.debug("Failed to write gallery reload audit entry: %s", e)

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
            query_vector: 128-D or 512-D query embedding.
            threshold_override: Optional custom threshold to override default.

        Returns:
            MatchResult if similarity >= threshold, else None.
        """
        if self._matrix.size == 0 or query_vector is None:
            return None

        # Check dimension alignment
        q_dim = query_vector.shape[0] if query_vector.ndim == 1 else 0
        if self._matrix.ndim != 2 or self._matrix.shape[1] != q_dim:
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
                    matched_dim=q_dim,
                )

        return None

    def get_target_count(self) -> int:
        """Return total active targets in memory."""
        return len(self._targets)

    def get_embedding_count(self) -> int:
        """Return total active embedding vectors in memory."""
        return len(self._target_ids)
