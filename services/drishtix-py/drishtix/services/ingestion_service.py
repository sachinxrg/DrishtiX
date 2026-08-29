"""
DrishtiX v4.0 — FBI Most Wanted API Ingestion Service.

Performs full paginated synchronization with the FBI Wanted REST API:
  - Downloads all wanted persons with face images (paginated, up to configurable limit).
  - Classifies targets as CRIMINAL or MISSING_PERSON based on FBI poster_classification.
  - Deduplicates by FBI UID stored in case_number field (FBI-<uid>).
  - Detects faces with YuNet, extracts ArcFace/SFace embeddings, and persists to SQLite.
  - Reloads the in-memory GalleryManager after each sync cycle.
  - Designed to be called every hour by the IngestionWorker background timer.
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import List, Optional, Set

import cv2
import httpx
import numpy as np

from drishtix.core.constants import GALLERY_DIR
from drishtix.core.enums import TargetCategory
from drishtix.core.signals import signal_bus
from drishtix.dao.audit_dao import AuditDAO
from drishtix.dao.embedding_dao import EmbeddingDAO
from drishtix.dao.session import get_session
from drishtix.dao.target_dao import TargetDAO
from drishtix.models.target_image import TargetImage
from drishtix.models.target_registry import TargetRegistry
from drishtix.services.face_detection import FaceDetectionService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.gallery_manager import GalleryManager

logger = logging.getLogger(__name__)

# FBI API constants
FBI_API_BASE = "https://api.fbi.gov/wanted/v1/list"
FBI_PAGE_SIZE = 20  # API default page size
FBI_REQUEST_TIMEOUT = 20.0
FBI_IMAGE_TIMEOUT = 15.0

# FBI poster_classification → DrishtiX TargetCategory mapping
_MISSING_CLASSIFICATIONS = {"missing", "kidnap", "kidnapping"}
_CRIMINAL_CLASSIFICATIONS = {
    "default", "ten", "terrorist", "terrorism", "cei",
    "law-enforcement-assistance", "fraudster", "ecap", "cyber",
    "counterintelligence", "vicap", "information",
}


def _classify_fbi_item(item: dict) -> str:
    """Map FBI poster_classification to DrishtiX TargetCategory value."""
    classification = (item.get("poster_classification") or "").lower().strip()
    subjects = [s.lower() for s in (item.get("subjects") or [])]

    # Check for missing/kidnapping keywords
    if classification in _MISSING_CLASSIFICATIONS:
        return TargetCategory.MISSING_PERSON.value
    for subj in subjects:
        if "missing" in subj or "kidnap" in subj:
            return TargetCategory.MISSING_PERSON.value

    # Default to criminal
    return TargetCategory.CRIMINAL.value


def _sanitize_filename(name: str, max_len: int = 40) -> str:
    """Create a filesystem-safe filename from a person's name."""
    cleaned = re.sub(r"[^\w\s-]", "", name)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    return cleaned[:max_len]


def _extract_fbi_uid(item: dict) -> str:
    """Extract the unique FBI identifier from an API item."""
    uid = item.get("uid", "")
    return uid[:12].upper() if uid else ""


class IngestionService:
    """
    Full-featured FBI Most Wanted API synchronization engine.

    Handles paginated fetching, image downloading, face detection,
    embedding extraction, SQLite persistence, and gallery hot-reload.
    """

    def __init__(
        self,
        detector: Optional[FaceDetectionService] = None,
        recognizer: Optional[FaceRecognitionService] = None,
    ) -> None:
        self.detector = detector or FaceDetectionService()
        self.recognizer = recognizer or FaceRecognitionService()
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    def _get_existing_fbi_case_numbers(self) -> Set[str]:
        """Query all existing FBI case numbers to prevent duplicate ingestion."""
        existing = set()
        try:
            with get_session() as session:
                all_targets = TargetDAO.get_all(session)
                for t in all_targets:
                    if t.case_number and t.case_number.startswith("FBI-"):
                        existing.add(t.case_number)
        except Exception as e:
            logger.warning("Failed to query existing FBI targets: %s", e)
        return existing

    async def ingest_fbi_wanted_async(self, max_items: int = 100) -> int:
        """
        Fetch wanted individuals from FBI Wanted API with full pagination,
        detect faces, extract embeddings, and save to SQLite.

        Args:
            max_items: Maximum number of new targets to ingest per sync cycle.

        Returns:
            Number of newly ingested targets.
        """
        ingested_count = 0
        existing_cases = self._get_existing_fbi_case_numbers()
        logger.info(
            "Starting FBI API sync. %d existing FBI targets in database. Max new: %d",
            len(existing_cases), max_items,
        )

        try:
            headers = {
                "User-Agent": "DrishtiX/4.0 (Edge AI Surveillance Platform)",
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(timeout=FBI_REQUEST_TIMEOUT, headers=headers) as client:
                page = 1
                total_available = None

                while ingested_count < max_items:
                    # Fetch page
                    params = {"page": page, "pageSize": FBI_PAGE_SIZE}
                    resp = await client.get(FBI_API_BASE, params=params)

                    if resp.status_code != 200:
                        logger.warning("FBI API responded with status %d on page %d", resp.status_code, page)
                        break

                    data = resp.json()
                    if total_available is None:
                        total_available = data.get("total", 0)
                        logger.info("FBI API reports %d total wanted persons", total_available)

                    items = data.get("items", [])
                    if not items:
                        logger.info("No more items on page %d, stopping pagination", page)
                        break

                    for item in items:
                        if ingested_count >= max_items:
                            break

                        fbi_uid = _extract_fbi_uid(item)
                        if not fbi_uid:
                            continue

                        case_number = f"FBI-{fbi_uid}"

                        # Skip already ingested targets
                        if case_number in existing_cases:
                            continue

                        # Skip captured/recovered
                        status = (item.get("status") or "").lower()
                        if status in ("captured", "recovered", "located"):
                            continue

                        title = item.get("title")
                        images = item.get("images", [])
                        if not title or not images:
                            continue

                        # Classify
                        category = _classify_fbi_item(item)

                        # Try to download and process images (try multiple)
                        processed = False
                        for img_entry in images[:3]:  # Try up to 3 images
                            img_url = img_entry.get("original") or img_entry.get("large")
                            if not img_url:
                                continue

                            try:
                                img_resp = await client.get(img_url, timeout=FBI_IMAGE_TIMEOUT)
                                if img_resp.status_code != 200:
                                    continue

                                img_arr = np.frombuffer(img_resp.content, dtype=np.uint8)
                                cv_img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                                if cv_img is None:
                                    continue

                                # Run face detection
                                detections = self.detector.detect_faces(cv_img)
                                if not detections:
                                    continue

                                # Save image locally
                                safe_name = _sanitize_filename(title)
                                local_filename = f"fbi_{safe_name}_{int(time.time())}.jpg"
                                local_path = GALLERY_DIR / local_filename
                                cv2.imwrite(str(local_path), cv_img)

                                # Extract embedding from best detected face
                                best_det = max(detections, key=lambda d: d.confidence)
                                embedding = self.recognizer.extract_embedding(cv_img, best_det.raw_row)

                                if embedding is not None:
                                    # Build description from available FBI fields
                                    description_parts = []
                                    if item.get("description"):
                                        description_parts.append(item["description"][:200])
                                    if item.get("nationality"):
                                        description_parts.append(f"Nationality: {item['nationality']}")
                                    if item.get("sex"):
                                        description_parts.append(f"Sex: {item['sex']}")
                                    if item.get("race_raw"):
                                        description_parts.append(f"Race: {item['race_raw']}")
                                    if item.get("warning_message"):
                                        description_parts.append(f"⚠ {item['warning_message']}")
                                    desc = " | ".join(description_parts) if description_parts else None

                                    with get_session() as session:
                                        # Create Target
                                        target = TargetRegistry(
                                            full_name=title.title(),
                                            category=category,
                                            case_number=case_number,
                                            description=desc,
                                            profile_image_path=str(local_path.relative_to(Path.cwd())),
                                            is_active=True,
                                        )
                                        TargetDAO.create(session, target)

                                        # Create TargetImage
                                        tgt_img = TargetImage(
                                            target_id=target.target_id,
                                            image_path=str(local_path.relative_to(Path.cwd())),
                                            image_order=0,
                                        )
                                        TargetDAO.add_image(session, tgt_img)

                                        # Create FaceEmbedding
                                        EmbeddingDAO.create(
                                            session=session,
                                            target_id=target.target_id,
                                            vector=embedding,
                                            source_image_id=tgt_img.image_id,
                                        )

                                        AuditDAO.log_action(
                                            session=session,
                                            action="TARGET_INGESTED",
                                            entity_type="TargetRegistry",
                                            entity_id=target.target_id,
                                            details=f"FBI auto-ingested '{title}' ({category}, case={case_number})",
                                        )

                                        ingested_count += 1
                                        existing_cases.add(case_number)
                                        logger.info(
                                            "Ingested FBI Target #%d: '%s' [%s] (Case: %s)",
                                            ingested_count, title, category, case_number,
                                        )

                                    processed = True
                                    break  # Move to next person

                            except httpx.TimeoutException:
                                logger.debug("Image download timeout for %s", title)
                                continue
                            except Exception as img_err:
                                logger.debug("Image processing error for %s: %s", title, img_err)
                                continue

                    # Move to next page
                    page += 1

                    # Respect rate limits
                    await asyncio.sleep(0.5)

                    # Stop if we've exhausted all pages
                    items_seen = (page - 1) * FBI_PAGE_SIZE
                    if total_available and items_seen >= total_available:
                        break

        except Exception as e:
            logger.error("FBI API ingestion failed: %s", e)

        # Hot-reload the in-memory gallery with new embeddings
        if ingested_count > 0:
            gallery = GalleryManager.get_instance()
            loaded = gallery.reload_gallery()
            logger.info(
                "FBI sync complete: %d new targets ingested. Gallery now has %d embeddings.",
                ingested_count, loaded,
            )
            try:
                signal_bus.gallery_reloaded.emit(loaded)
            except Exception:
                pass

        return ingested_count
