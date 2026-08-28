"""
DrishtiX v4.0 — Settings View.

Configuration management view for camera sources, DNN model thresholds,
alert parameters, database health, and Telegram notifications.
Migrated from: com.drishtix.controller.SettingsController (Java)
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.config import get_settings
from drishtix.core.signals import signal_bus
from drishtix.dao.session import test_connection
from drishtix.services.gallery_manager import GalleryManager
from drishtix.utils.sound_player import SoundPlayer

logger = logging.getLogger(__name__)


class SettingsView(QWidget):
    """System configuration and hardware delegate settings."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings = get_settings()

        self._init_ui()
        self._load_current_values()

    def _init_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ─── Header ──────────────────────────────────────────────────
        header = QHBoxLayout()
        lbl_title = QLabel("SYSTEM CONFIGURATION & HARDWARE DELEGATES")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #E8EAED; letter-spacing: 0.5px;")
        header.addWidget(lbl_title)

        header.addStretch()

        btn_save = QPushButton("Save & Apply Settings")
        btn_save.setProperty("class", "btn-primary")
        btn_save.clicked.connect(self._save_settings)
        header.addWidget(btn_save)

        layout.addLayout(header)

        # ─── 1. Camera & Video Pipeline ──────────────────────────────
        grp_camera = QGroupBox("Camera & Capture Settings")
        grp_camera.setStyleSheet("QGroupBox { font-weight: bold; color: #4A9EFF; border: 1px solid #2E3140; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        cam_layout = QGridLayout(grp_camera)
        cam_layout.setSpacing(10)

        cam_layout.addWidget(QLabel("Primary Video Source:"), 0, 0)
        self.txt_cam_source = QLineEdit()
        self.txt_cam_source.setPlaceholderText("0 for Webcam, or rtsp://... URL")
        cam_layout.addWidget(self.txt_cam_source, 0, 1)

        cam_layout.addWidget(QLabel("Target Frame Rate (FPS):"), 1, 0)
        self.spn_target_fps = QSpinBox()
        self.spn_target_fps.setRange(5, 60)
        self.spn_target_fps.setValue(30)
        cam_layout.addWidget(self.spn_target_fps, 1, 1)

        cam_layout.addWidget(QLabel("Inference Keyframe Interval:"), 2, 0)
        self.spn_interval = QSpinBox()
        self.spn_interval.setRange(1, 10)
        self.spn_interval.setToolTip("Run full YuNet detection every Nth frame (1 = every frame, 3 = recommended)")
        cam_layout.addWidget(self.spn_interval, 2, 1)

        layout.addWidget(grp_camera)

        # ─── 2. Deep Learning Detection & Recognition ────────────────
        grp_dnn = QGroupBox("Deep Neural Network Thresholds (YuNet + SFace)")
        grp_dnn.setStyleSheet("QGroupBox { font-weight: bold; color: #34D399; border: 1px solid #2E3140; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        dnn_layout = QGridLayout(grp_dnn)
        dnn_layout.setSpacing(10)

        dnn_layout.addWidget(QLabel("YuNet Detection Score Threshold:"), 0, 0)
        self.spn_score_thresh = QDoubleSpinBox()
        self.spn_score_thresh.setRange(0.1, 0.99)
        self.spn_score_thresh.setSingleStep(0.05)
        dnn_layout.addWidget(self.spn_score_thresh, 0, 1)

        dnn_layout.addWidget(QLabel("SFace Cosine Match Threshold:"), 1, 0)
        self.spn_match_thresh = QDoubleSpinBox()
        self.spn_match_thresh.setRange(0.2, 0.95)
        self.spn_match_thresh.setSingleStep(0.05)
        self.spn_match_thresh.setToolTip("Cosine similarity for positive identity match (0.45 = standard)")
        dnn_layout.addWidget(self.spn_match_thresh, 1, 1)

        layout.addWidget(grp_dnn)

        # ─── 3. Tactical Alerts & Audio ──────────────────────────────
        grp_alert = QGroupBox("Perimeter Alerts & Audio Configuration")
        grp_alert.setStyleSheet("QGroupBox { font-weight: bold; color: #FF4D2E; border: 1px solid #2E3140; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        alert_layout = QGridLayout(grp_alert)
        alert_layout.setSpacing(10)

        alert_layout.addWidget(QLabel("Per-Target Alert Cooldown (seconds):"), 0, 0)
        self.spn_cooldown = QSpinBox()
        self.spn_cooldown.setRange(0, 300)
        self.spn_cooldown.setSuffix(" sec")
        alert_layout.addWidget(self.spn_cooldown, 0, 1)

        self.chk_sound = QCheckBox("Enable Audible Alarms & Notification Chimes")
        alert_layout.addWidget(self.chk_sound, 1, 0, 1, 2)

        self.chk_telegram = QCheckBox("Enable Telegram Bot Incident Notifications")
        alert_layout.addWidget(self.chk_telegram, 2, 0, 1, 2)

        alert_layout.addWidget(QLabel("Telegram Bot API Token:"), 3, 0)
        self.txt_tele_token = QLineEdit()
        self.txt_tele_token.setEchoMode(QLineEdit.EchoMode.Password)
        alert_layout.addWidget(self.txt_tele_token, 3, 1)

        alert_layout.addWidget(QLabel("Telegram Destination Chat ID:"), 4, 0)
        self.txt_tele_chat = QLineEdit()
        alert_layout.addWidget(self.txt_tele_chat, 4, 1)

        layout.addWidget(grp_alert)

        # ─── 4. Database Diagnostics ─────────────────────────────────
        grp_db = QGroupBox("Edge SQLite Database Diagnostics")
        grp_db.setStyleSheet("QGroupBox { font-weight: bold; color: #FBBF24; border: 1px solid #2E3140; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        db_layout = QHBoxLayout(grp_db)
        db_layout.setSpacing(12)

        self.lbl_db_path = QLabel("Database: data/drishtix.db (SQLite WAL Mode)")
        self.lbl_db_path.setStyleSheet("color: #9AA0A6; font-size: 11px;")
        db_layout.addWidget(self.lbl_db_path)

        db_layout.addStretch()

        btn_test_db = QPushButton("Test Connection")
        btn_test_db.clicked.connect(self._test_db)
        db_layout.addWidget(btn_test_db)

        btn_reload_gallery = QPushButton("Force Reload Gallery")
        btn_reload_gallery.clicked.connect(self._reload_gallery)
        db_layout.addWidget(btn_reload_gallery)

        layout.addWidget(grp_db)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_current_values(self) -> None:
        """Hydrate UI from settings."""
        self.txt_cam_source.setText(str(self.settings.camera.source))
        self.spn_target_fps.setValue(self.settings.camera.target_fps)
        self.spn_interval.setValue(self.settings.detection.inference_interval)

        self.spn_score_thresh.setValue(self.settings.detection.score_threshold)
        self.spn_match_thresh.setValue(self.settings.recognition.match_threshold)

        self.spn_cooldown.setValue(self.settings.alerts.cooldown_seconds)
        self.chk_sound.setChecked(self.settings.alerts.sound_enabled)
        self.chk_telegram.setChecked(self.settings.alerts.telegram_enabled)
        self.txt_tele_token.setText(self.settings.alerts.telegram_bot_token)
        self.txt_tele_chat.setText(self.settings.alerts.telegram_chat_id)

    def _save_settings(self) -> None:
        """Apply changes to runtime settings."""
        # Update settings object
        cam_src = self.txt_cam_source.text().strip()
        try:
            self.settings.camera.source = int(cam_src)
        except ValueError:
            self.settings.camera.source = cam_src

        self.settings.camera.target_fps = self.spn_target_fps.value()
        self.settings.detection.inference_interval = self.spn_interval.value()
        self.settings.detection.score_threshold = self.spn_score_thresh.value()
        self.settings.recognition.match_threshold = self.spn_match_thresh.value()
        self.settings.alerts.cooldown_seconds = self.spn_cooldown.value()
        self.settings.alerts.sound_enabled = self.chk_sound.isChecked()
        self.settings.alerts.telegram_enabled = self.chk_telegram.isChecked()
        self.settings.alerts.telegram_bot_token = self.txt_tele_token.text().strip()
        self.settings.alerts.telegram_chat_id = self.txt_tele_chat.text().strip()

        # Update SoundPlayer
        SoundPlayer.get_instance().set_enabled(self.chk_sound.isChecked())
        GalleryManager.get_instance().set_match_threshold(self.spn_match_thresh.value())

        QMessageBox.information(self, "Settings Saved", "Runtime configuration updated successfully.")

    def _test_db(self) -> None:
        ok = test_connection()
        if ok:
            QMessageBox.information(self, "Database Status", "✓ SQLite database connection is healthy.")
        else:
            QMessageBox.critical(self, "Database Status", "✗ Failed to connect to SQLite database.")

    def _reload_gallery(self) -> None:
        count = GalleryManager.get_instance().reload_gallery()
        QMessageBox.information(self, "Gallery Reloaded", f"Successfully reloaded {count} active embeddings.")
