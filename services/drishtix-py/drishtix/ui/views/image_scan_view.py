"""
DrishtiX v5.0 — Static Image Scan View.

High-density multi-target face detection and recognition for static crowd photos.
Can identify 40+ individuals simultaneously in forensic imagery.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from drishtix.services.alert_service import AlertService
from drishtix.services.face_detection import FaceDetectionService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.gallery_manager import GalleryManager, MatchResult
from drishtix.ui.icons import render_svg_icon
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Spacing
from drishtix.ui.widgets.alert_card import AlertCard
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard
from drishtix.ui.widgets.pill_badge import PillBadge, PillStatus
from drishtix.ui.widgets.section_header import SectionHeader
from drishtix.ui.widgets.video_label import VideoLabel
from drishtix.utils.image_utils import draw_tactical_bbox, mat_to_qpixmap

logger = logging.getLogger(__name__)


class ImageScanView(QWidget):
    """Forensic static crowd image scanning view."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.detector = FaceDetectionService()
        self.recognizer = FaceRecognitionService()
        self.gallery = GalleryManager.get_instance()
        self.alert_service = AlertService.get_instance()

        self._loaded_image: Optional[np.ndarray] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # ─── Top Control Toolbar ─────────────────────────────────────
        header = SectionHeader(
            "FORENSIC CROWD IMAGE SCANNER",
            "Deep neural multi-face identification and demographic analysis",
            icon="scanner",
        )

        self.lbl_status = PillBadge("Awaiting forensic image", PillStatus.NEUTRAL)
        header.add_action(self.lbl_status)

        btn_load = QPushButton("Select Image...")
        btn_load.setIcon(render_svg_icon("camera", size=14))
        btn_load.clicked.connect(self._select_image)
        header.add_action(btn_load)

        self.btn_scan = QPushButton("Run Deep Scan")
        self.btn_scan.setIcon(render_svg_icon("zap", normal_color=Color.WHITE, size=14))
        apply_class(self.btn_scan, "btn-primary")
        self.btn_scan.setEnabled(False)
        self.btn_scan.clicked.connect(self._run_scan)
        header.add_action(self.btn_scan)

        layout.addWidget(header)

        # ─── Progress Bar ────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # ─── Center: Image View Surface in GlassCard ────────────────
        image_card = GlassCard(variant=CardVariant.GLASS)
        image_card.set_accessible_info("Image Scan Surface", "High-density crowd image display")
        image_card_layout = image_card.content_layout()
        image_card_layout.setContentsMargins(10, 10, 10, 10)
        self.image_label = VideoLabel()
        image_card_layout.addWidget(self.image_label)
        layout.addWidget(image_card, stretch=3)

        # ─── Bottom: Identified Matches Container ────────────────────
        matches_frame = GlassCard(variant=CardVariant.GLASS)
        matches_frame.setFixedHeight(160)
        matches_layout = matches_frame.content_layout()
        matches_layout.setContentsMargins(12, 10, 12, 10)
        matches_layout.setSpacing(6)

        lbl_matches_hdr = QLabel("IDENTIFIED TARGETS IN IMAGE")
        apply_class(lbl_matches_hdr, "type-caption")
        lbl_matches_hdr.setStyleSheet(f"font-weight: 700; color: {Color.TEXT_MUTED}; letter-spacing: 0.5px;")
        matches_layout.addWidget(lbl_matches_hdr)

        self.scroll_matches = QScrollArea()
        self.scroll_matches.setWidgetResizable(True)

        self.matches_container = QWidget()
        self.matches_layout = QHBoxLayout(self.matches_container)
        self.matches_layout.setContentsMargins(0, 0, 0, 0)
        self.matches_layout.setSpacing(10)
        self.matches_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.lbl_no_matches = QLabel("No targets identified in current image")
        apply_class(self.lbl_no_matches, "empty-state-message")
        self.matches_layout.addWidget(self.lbl_no_matches)

        self.scroll_matches.setWidget(self.matches_container)
        matches_layout.addWidget(self.scroll_matches)

        layout.addWidget(matches_frame, stretch=1)

    def _select_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Crowd Image to Analyze",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if file_path:
            cv_img = cv2.imread(file_path)
            if cv_img is not None:
                self._loaded_image = cv_img
                self.image_label.set_frame(mat_to_qpixmap(cv_img))
                self.btn_scan.setEnabled(True)
                self.lbl_status.set_text(f"Ready: {Path(file_path).name} ({cv_img.shape[1]}×{cv_img.shape[0]})")
                self.lbl_status.set_status(PillStatus.SAFE)
                self._clear_matches()
            else:
                logger.warning("Could not decode selected image: %s", file_path)
                self.lbl_status.set_text(f"Could not read {Path(file_path).name}")
                self.lbl_status.set_status(PillStatus.CRITICAL)

    def _clear_matches(self) -> None:
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.lbl_no_matches = QLabel("Click 'Run Deep Scan' to analyze faces")
        apply_class(self.lbl_no_matches, "empty-state-message")
        self.matches_layout.addWidget(self.lbl_no_matches)

    def _run_scan(self) -> None:
        try:
            self._run_scan_impl()
        except Exception:
            logger.exception("Forensic image scan failed")
            self.progress_bar.hide()
            self.lbl_status.set_text("Scan failed — see log for details")
            self.lbl_status.set_status(PillStatus.CRITICAL)

    def _run_scan_impl(self) -> None:
        if self._loaded_image is None:
            return

        self.lbl_status.set_text("Scanning YuNet & SFace...")
        self.lbl_status.set_status(PillStatus.WARNING)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)

        t0 = time.time()
        annotated = self._loaded_image.copy()

        # Step 1: Detect all faces
        detections = self.detector.detect_faces(self._loaded_image)
        detected_count = len(detections)

        # Clear match cards
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        matches_found: List[tuple[MatchResult, Optional[int], Optional[str]]] = []

        # Step 2: Extract embeddings & match against gallery
        for det in detections:
            emb, demographics = self.recognizer.extract_embedding_and_demographics(
                self._loaded_image, det.raw_row
            )
            face_age = demographics.age if demographics else None
            face_gender = demographics.gender if demographics else None

            if emb is not None:
                match = self.gallery.match_embedding(emb)
                if match is not None:
                    matches_found.append((match, face_age, face_gender))
                    draw_tactical_bbox(
                        frame=annotated,
                        bbox=det.bbox,
                        name=match.target.full_name,
                        category=match.target.category,
                        confidence=match.confidence,
                        age=face_age,
                        gender=face_gender,
                    )
                    self.alert_service.process_match(
                        match=match,
                        frame=self._loaded_image,
                        bbox=det.bbox,
                        location_tag="Forensic Image Scan",
                        age=face_age,
                        gender=face_gender,
                    )
                else:
                    draw_tactical_bbox(
                        frame=annotated,
                        bbox=det.bbox,
                        name="Unknown",
                        category=None,
                        confidence=None,
                        age=face_age,
                        gender=face_gender,
                    )
            else:
                draw_tactical_bbox(
                    frame=annotated,
                    bbox=det.bbox,
                    name="Unknown",
                    category=None,
                    confidence=None,
                    age=face_age,
                    gender=face_gender,
                )

        # Update Display Frame
        self.image_label.set_frame(mat_to_qpixmap(annotated))
        self.progress_bar.hide()

        elapsed = (time.time() - t0) * 1000

        # Populate Matches Cards
        if matches_found:
            for m, m_age, m_gender in matches_found:
                card_data = {
                    "full_name": m.target.full_name,
                    "category": m.target.category,
                    "case_number": m.target.case_number or "N/A",
                    "confidence": m.confidence,
                    "age": m_age,
                    "gender": m_gender,
                }
                card = AlertCard(card_data, self.matches_container)
                self.matches_layout.addWidget(card)
        else:
            lbl_none = QLabel("No registered watchlist targets recognized in image.")
            apply_class(lbl_none, "empty-state-message")
            self.matches_layout.addWidget(lbl_none)

        self.lbl_status.set_text(
            f"Done: {detected_count} faces, {len(matches_found)} matched ({elapsed:.0f}ms)"
        )
        self.lbl_status.set_status(PillStatus.SAFE)
