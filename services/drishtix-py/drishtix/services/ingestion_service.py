"""
DrishtiX v4.0 — Target Ingestion Service.

Periodically pulls target registries from public law enforcement feeds
(e.g., FBI Most Wanted API, local law enforcement repositories), downloads
facial images, runs YuNet/SFace embedding extraction, and updates the local
database gallery automatically.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import cv2
import httpx
import numpy as np

from drishtix.core.constants import GALLERY_DIR
from drishtix.core.enums import TargetCategory
from drishtix.dao.embedding_dao import EmbeddingDAO
from drishtix.dao.session import get_session
from drishtix.dao.target_dao import TargetDAO
from drishtix.models.target_image import TargetImage
from drishtix.models.target_registry import TargetRegistry
from drishtix.services.face_detection import FaceDetectionService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.gallery_manager import GalleryManager

logger = logging.getLogger(__name__)


class IngestionService:
    """Synchronizes target registries from external REST APIs and directories."""

    def __init__(
        self,
        detector: Optional[FaceDetectionService] = None,
        recognizer: Optional[FaceRecognitionService] = None,
    ) -> None:
        self.detector = detector or FaceDetectionService()
        self.recognizer = recognizer or FaceRecognitionService()
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    async def ingest_fbi_wanted_async(self, max_items: int = 10) -> int:
        """
        Fetch top wanted individuals from FBI Wanted API, detect faces,
        extract embeddings, and save to SQLite.
        """
        url = "https://api.fbi.gov/wanted/v1/list"
        ingested_count = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params={"pageSize": max_items})
                if resp.status_code != 200:
                    logger.warning("FBI API responded with status %d", resp.status_code)
                    return 0

                data = resp.json()
                items = data.get("items", [])

                for item in items:
                    title = item.get("title")
                    images = item.get("images", [])
                    if not title or not images:
                        continue

                    # Select first valid image URL
                    img_url = images[0].get("original") or images[0].get("large")
                    if not img_url:
                        continue

                    # Download image bytes
                    img_resp = await client.get(img_url)
                    if img_resp.status_code != 200:
                        continue

                    img_arr = np.frombuffer(img_resp.content, dtype=np.uint8)
                    cv_img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                    if cv_img is None:
                        continue

                    # Run YuNet face detection
                    detections = self.detector.detect_faces(cv_img)
                    if not detections:
                        continue

                    # Save image locally
                    sanitized_name = "".join(c for c in title if c.isalnum() or c in (" ", "_")).rstrip()
                    local_filename = f"fbi_{sanitized_name[:20].replace(' ', '_')}_{int(asyncio.get_event_loop().time())}.jpg"
                    local_path = GALLERY_DIR / local_filename
                    cv2.imwrite(str(local_path), cv_img)

                    # Extract SFace embedding for best detection
                    best_det = max(detections, key=lambda d: d.confidence)
                    embedding = self.recognizer.extract_embedding(cv_img, best_det.raw_row)

                    if embedding is not None:
                        with get_session() as session:
                            # Create Target
                            target = TargetRegistry(
                                full_name=title,
                                category=TargetCategory.CRIMINAL.value,
                                case_number=f"FBI-{item.get('uid', 'UNK')[:8].upper()}",
                                description=item.get("description") or item.get("caution"),
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

                            ingested_count += 1
                            logger.info("Ingested FBI Target: '%s'", title)

            if ingested_count > 0:
                GalleryManager.get_instance().reload_gallery()

            return ingested_count
        except Exception as e:
            logger.error("FBI Ingestion failed: %s", e)
            return ingested_count
