"""
DrishtiX v4.0 — Static Image Scan View.

High-density multi-target face detection and recognition for static crowd photos.
Can identify 40+ individuals simultaneously in forensic imagery.
Migrated from: com.drishtix.controller.ImageScanController (Java)
"""

import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
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
from drishtix.ui.widgets.alert_card import AlertCard
from drishtix.ui.widgets.video_label import VideoLabel
from drishtix.utils.image_utils import draw_tactical_bbox, mat_to_qpixmap


class ImageScanView(QWidget):
    """Forensic static image scanning view."""

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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ─── Top Control Toolbar ─────────────────────────────────────
        toolbar = QHBoxLayout()
        lbl_title = QLabel("FORENSIC CROWD IMAGE SCANNER")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #E8EAED; letter-spacing: 0.5px;")
        toolbar.addWidget(lbl_title)

        toolbar.addStretch()

        self.lbl_status = QLabel("Load high-resolution image to analyze")
        self.lbl_status.setStyleSheet("color: #9AA0A6; font-size: 12px; margin-right: 12px;")
        toolbar.addWidget(self.lbl_status)

        btn_load = QPushButton("Select Image...")
        btn_load.clicked.connect(self._select_image)
        toolbar.addWidget(btn_load)

        self.btn_scan = QPushButton("Run Deep Scan")
        self.btn_scan.setProperty("class", "btn-primary")
        self.btn_scan.setEnabled(False)
        self.btn_scan.clicked.connect(self._run_scan)
        toolbar.addWidget(self.btn_scan)

        layout.addLayout(toolbar)

        # ─── Progress Bar ────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # ─── Center: Image View Surface ──────────────────────────────
        self.image_label = VideoLabel()
        layout.addWidget(self.image_label, stretch=3)

        # ─── Bottom: Identified Matches Container ────────────────────
        matches_frame = QFrame()
        matches_frame.setProperty("class", "bento-card")
        matches_frame.setFixedHeight(140)
        matches_layout = QVBoxLayout(matches_frame)
        matches_layout.setContentsMargins(8, 8, 8, 8)
        matches_layout.setSpacing(4)

        lbl_matches_hdr = QLabel("IDENTIFIED TARGETS IN IMAGE")
        lbl_matches_hdr.setStyleSheet("font-weight: bold; font-size: 11px; color: #9AA0A6;")
        matches_layout.addWidget(lbl_matches_hdr)

        self.scroll_matches = QScrollArea()
        self.scroll_matches.setWidgetResizable(True)
        self.scroll_matches.setStyleSheet("background: transparent; border: none;")

        self.matches_container = QWidget()
        self.matches_layout = QHBoxLayout(self.matches_container)
        self.matches_layout.setContentsMargins(0, 0, 0, 0)
        self.matches_layout.setSpacing(8)
        self.matches_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.lbl_no_matches = QLabel("No targets identified in current image")
        self.lbl_no_matches.setStyleSheet("color: #555A65; font-size: 11px;")
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
                self.lbl_status.setText(f"Ready: {Path(file_path).name} ({cv_img.shape[1]}x{cv_img.shape[0]})")
                self.lbl_status.setStyleSheet("color: #34D399;")
                self._clear_matches()

    def _clear_matches(self) -> None:
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.lbl_no_matches = QLabel("Click 'Run Deep Scan' to analyze faces")
        self.lbl_no_matches.setStyleSheet("color: #555A65; font-size: 11px;")
        self.matches_layout.addWidget(self.lbl_no_matches)

    def _run_scan(self) -> None:
        if self._loaded_image is None:
            return

        self.lbl_status.setText("Running YuNet multi-target detection & SFace matching...")
        self.lbl_status.setStyleSheet("color: #FBBF24;")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate animation

        t0 = time.time()
        annotated = self._loaded_image.copy()

        # Step 1: Detect all faces (supports 40+ faces)
        detections = self.detector.detect_faces(self._loaded_image)
        detected_count = len(detections)

        # Clear match cards
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        matches_found: List[MatchResult] = []

        # Step 2: Extract embeddings & match against gallery
        for det in detections:
            emb = self.recognizer.extract_embedding(self._loaded_image, det.raw_row)
            if emb is not None:
                match = self.gallery.match_embedding(emb)
                if match is not None:
                    matches_found.append(match)
                    # Draw Tactical box for match
                    draw_tactical_bbox(
                        frame=annotated,
                        bbox=det.bbox,
                        name=match.target.full_name,
                        category=match.target.category,
                        confidence=match.confidence,
                    )
                    # Trigger alert record
                    self.alert_service.process_match(
                        match=match,
                        frame=self._loaded_image,
                        bbox=det.bbox,
                        location_tag="Forensic Image Scan",
                    )
                else:
                    # Draw Unknown face box
                    draw_tactical_bbox(
                        frame=annotated,
                        bbox=det.bbox,
                        name="Unknown",
                        category=None,
                        confidence=None,
                    )
            else:
                draw_tactical_bbox(
                    frame=annotated,
                    bbox=det.bbox,
                    name="Unknown",
                    category=None,
                    confidence=None,
                )

        # Update Display Frame
        self.image_label.set_frame(mat_to_qpixmap(annotated))
        self.progress_bar.hide()

        elapsed = (time.time() - t0) * 1000

        # Populate Matches Cards
        if matches_found:
            for m in matches_found:
                card_data = {
                    "full_name": m.target.full_name,
                    "category": m.target.category,
                    "case_number": m.target.case_number or "N/A",
                    "confidence": m.confidence,
                }
                card = AlertCard(card_data, self.matches_container)
                self.matches_layout.addWidget(card)
        else:
            lbl_none = QLabel("No registered watchlist targets recognized in image.")
            lbl_none.setStyleSheet("color: #9AA0A6; font-size: 11px; padding: 10px;")
            self.matches_layout.addWidget(lbl_none)

        self.lbl_status.setText(
            f"Scan Complete: {detected_count} faces detected, {len(matches_found)} matched in {elapsed:.0f}ms"
        )
        self.lbl_status.setStyleSheet("color: #34D399; font-weight: bold;")
