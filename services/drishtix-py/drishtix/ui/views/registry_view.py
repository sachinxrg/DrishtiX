"""
DrishtiX v4.0 — Target Registry View.

Management interface for registering, updating, and removing watchlist targets
with automatic SFace embedding extraction upon face photo upload.
"""

import logging
from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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


class AddTargetDialog(QDialog):
    """Dialog for creating a new watchlist target with facial photo embedding."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Register New Target")
        self.setFixedSize(480, 520)
        self.setStyleSheet("background-color: #F8FAFC; color: #0F172A;")
        self.selected_image_path: Optional[str] = None

        self.detector = FaceDetectionService()
        self.recognizer = FaceRecognitionService()

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 1. Full Name
        layout.addWidget(QLabel("Full Name *"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. John Doe")
        layout.addWidget(self.txt_name)

        # 2. Category
        layout.addWidget(QLabel("Classification Category *"))
        self.cmb_category = QComboBox()
        self.cmb_category.addItem("CRIMINAL", TargetCategory.CRIMINAL.value)
        self.cmb_category.addItem("MISSING_PERSON", TargetCategory.MISSING_PERSON.value)
        layout.addWidget(self.cmb_category)

        # 3. Case Number
        layout.addWidget(QLabel("Case / FIR Reference Number"))
        self.txt_case = QLineEdit()
        self.txt_case.setPlaceholderText("e.g. FIR-2026-9812")
        layout.addWidget(self.txt_case)

        # 4. Description
        layout.addWidget(QLabel("Notes / Description"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("Identifying marks, known locations, etc.")
        self.txt_desc.setFixedHeight(60)
        layout.addWidget(self.txt_desc)

        # 5. Photo Picker
        layout.addWidget(QLabel("Target Photo (Face Image) *"))
        photo_row = QHBoxLayout()
        self.lbl_photo_status = QLabel("No image selected")
        self.lbl_photo_status.setStyleSheet("color: #64748B; font-size: 11px;")
        photo_row.addWidget(self.lbl_photo_status, stretch=1)

        btn_browse = QPushButton("Browse Image...")
        btn_browse.clicked.connect(self._browse_image)
        photo_row.addWidget(btn_browse)
        layout.addLayout(photo_row)

        # 6. Action Buttons
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        self.btn_save = QPushButton("Register Target")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.clicked.connect(self._save_target)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def _browse_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Target Photo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if file_path:
            self.selected_image_path = file_path
            self.lbl_photo_status.setText(Path(file_path).name)
            self.lbl_photo_status.setStyleSheet("color: #10B981; font-weight: 500;")

    def _save_target(self) -> None:
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Full Name is required.")
            return

        if not self.selected_image_path:
            QMessageBox.warning(self, "Validation Error", "Target photo is required for facial recognition.")
            return

        # Load image with OpenCV
        cv_img = cv2.imread(self.selected_image_path)
        if cv_img is None:
            QMessageBox.critical(self, "Image Error", "Failed to load selected image file.")
            return

        # Detect face & extract embedding
        detections = self.detector.detect_faces(cv_img)
        if not detections:
            # SFace direct extraction fallback if YuNet doesn't find face landmarks
            embedding = self.recognizer.extract_embedding(cv_img)
        else:
            best_det = max(detections, key=lambda d: d.confidence)
            embedding = self.recognizer.extract_embedding(cv_img, best_det.raw_row)

        if embedding is None:
            QMessageBox.critical(self, "Recognition Error", "Failed to extract face embedding from photo.")
            return

        # Copy image to GALLERY_DIR
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        sanitized = "".join(c for c in name if c.isalnum() or c in (" ", "_")).rstrip()
        dest_filename = f"target_{sanitized[:20].replace(' ', '_')}_{Path(self.selected_image_path).suffix}"
        dest_path = GALLERY_DIR / dest_filename
        cv2.imwrite(str(dest_path), cv_img)

        rel_path = str(dest_path.relative_to(Path.cwd()))

        # Save to SQLite
        try:
            with get_session() as session:
                target = TargetRegistry(
                    full_name=name,
                    category=self.cmb_category.currentData(),
                    case_number=self.txt_case.text().strip() or None,
                    description=self.txt_desc.toPlainText().strip() or None,
                    profile_image_path=rel_path,
                    is_active=True,
                )
                TargetDAO.create(session, target)

                # Save TargetImage
                tgt_img = TargetImage(
                    target_id=target.target_id,
                    image_path=rel_path,
                    image_order=0,
                )
                TargetDAO.add_image(session, tgt_img)

                # Save FaceEmbedding
                EmbeddingDAO.create(
                    session=session,
                    target_id=target.target_id,
                    vector=embedding,
                    source_image_id=tgt_img.image_id,
                )

                # Audit
                AuditDAO.log_action(
                    session=session,
                    action="TARGET_CREATED",
                    entity_type="TargetRegistry",
                    entity_id=target.target_id,
                    details=f"Created target '{name}' ({target.category})",
                )

            # Reload in-memory gallery
            GalleryManager.get_instance().reload_gallery()
            signal_bus.targets_changed.emit()

            self.accept()
        except Exception as e:
            logger.error("Failed to register target: %s", e)
            QMessageBox.critical(self, "Database Error", f"Failed to save target: {e}")


class RegistryView(QWidget):
    """Target Watchlist Registry table and management page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()
        self._wire_signals()
        self.load_targets()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ─── Action Toolbar ──────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search box
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search targets by name or case number...")
        self.txt_search.setFixedWidth(280)
        self.txt_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.txt_search)

        # Category Filter
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("All Categories", None)
        self.cmb_filter.addItem("Criminals Only", TargetCategory.CRIMINAL.value)
        self.cmb_filter.addItem("Missing Persons Only", TargetCategory.MISSING_PERSON.value)
        self.cmb_filter.currentIndexChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.cmb_filter)

        toolbar.addStretch()

        btn_add = QPushButton("+ Register New Target")
        btn_add.setProperty("class", "btn-primary")
        btn_add.clicked.connect(self._open_add_dialog)
        toolbar.addWidget(btn_add)

        layout.addLayout(toolbar)

        # ─── Target Table ────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Target Name",
            "Category",
            "Case Reference",
            "Status",
            "Actions",
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

    def _wire_signals(self) -> None:
        signal_bus.targets_changed.connect(self.load_targets)

    def load_targets(self) -> None:
        """Fetch and populate target registry from SQLite."""
        query = self.txt_search.text().strip()
        selected_cat = self.cmb_filter.currentData()

        with get_session() as session:
            if query:
                targets = TargetDAO.search(session, query)
            else:
                targets = TargetDAO.get_all(session, active_only=False)

            if selected_cat:
                targets = [t for t in targets if t.category == selected_cat]

            self.table.setRowCount(len(targets))

            for row, t in enumerate(targets):
                # ID
                item_id = QTableWidgetItem(str(t.target_id))
                item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item_id)

                # Name
                item_name = QTableWidgetItem(t.full_name)
                item_name.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 1, item_name)

                # Category Badge
                is_crim = (t.category == "CRIMINAL")
                cat_label = QLabel(t.category.replace("_", " "))
                cat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cat_label.setProperty("class", "badge-criminal" if is_crim else "badge-missing")
                self.table.setCellWidget(row, 2, cat_label)

                # Case
                item_case = QTableWidgetItem(t.case_number or "N/A")
                item_case.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 3, item_case)

                # Status Toggle
                btn_status = QPushButton("ACTIVE" if t.is_active else "INACTIVE")
                btn_status.setProperty("class", "btn-success" if t.is_active else "")
                btn_status.setFixedHeight(26)
                btn_status.clicked.connect(lambda _, tid=t.target_id, act=t.is_active: self._toggle_active(tid, act))
                self.table.setCellWidget(row, 4, btn_status)

                # Delete Action
                btn_del = QPushButton("Delete")
                btn_del.setProperty("class", "btn-danger")
                btn_del.setFixedHeight(26)
                btn_del.clicked.connect(lambda _, tid=t.target_id, nm=t.full_name: self._delete_target(tid, nm))
                self.table.setCellWidget(row, 5, btn_del)

    def _on_search_changed(self) -> None:
        self.load_targets()

    def _open_add_dialog(self) -> None:
        dlg = AddTargetDialog(self)
        dlg.exec()

    def _toggle_active(self, target_id: int, current_status: bool) -> None:
        new_status = not current_status
        with get_session() as session:
            TargetDAO.set_active(session, target_id, new_status)
            AuditDAO.log_action(
                session=session,
                action="TARGET_STATUS_CHANGED",
                entity_type="TargetRegistry",
                entity_id=target_id,
                details=f"Target {'activated' if new_status else 'deactivated'}",
            )
        GalleryManager.get_instance().reload_gallery()
        self.load_targets()

    def _delete_target(self, target_id: int, name: str) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete target '{name}' and all associated embeddings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            with get_session() as session:
                TargetDAO.delete(session, target_id)
                AuditDAO.log_action(
                    session=session,
                    action="TARGET_DELETED",
                    entity_type="TargetRegistry",
                    entity_id=target_id,
                    details=f"Deleted target '{name}'",
                )
            GalleryManager.get_instance().reload_gallery()
            self.load_targets()
