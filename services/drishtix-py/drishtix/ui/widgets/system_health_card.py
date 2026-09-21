"""
DrishtiX v5.0 — 21st UI SystemHealthCard Widget.

Compact 2x2 telemetry monitoring card displaying real-time Edge AI compute health:
FPS throughput, RAM RSS usage, CPU load, and system uptime with 21st.dev vector iconography.
"""

import os
import time
from typing import Optional

import psutil
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.signals import signal_bus
from drishtix.ui.icons import render_svg_pixmap
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard


class SystemHealthCard(GlassCard):
    """
    Edge compute node health telemetry card with 21st UI vector telemetry badges.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(variant=CardVariant.GLASS, enable_hover=True, parent=parent)
        self._start_time = time.time()
        self._process = psutil.Process(os.getpid())

        self._init_ui()
        self._wire_signals()

        # Telemetry sample timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._sample_telemetry)
        self._timer.start(1000)

    def _init_ui(self) -> None:
        layout = self.content_layout()
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header
        hdr_layout = QHBoxLayout()
        lbl_title = QLabel("SYSTEM COMPUTE HEALTH")
        apply_class(lbl_title, "type-caption")
        lbl_title.setStyleSheet(f"font-weight: 700; color: {Color.TEXT_MUTED}; letter-spacing: 0.5px;")
        hdr_layout.addWidget(lbl_title)

        self.lbl_node_badge = QLabel("EDGE CPU")
        self.lbl_node_badge.setStyleSheet(
            f"background-color: {Color.SAFE_BG}; color: {Color.SAFE_BOLD}; "
            f"border: 1px solid {Color.SAFE_BORDER}; border-radius: 4px; padding: 1px 6px; font-size: 9px; font-weight: 700;"
        )
        hdr_layout.addWidget(self.lbl_node_badge)
        hdr_layout.addStretch()
        layout.addLayout(hdr_layout)

        # 2x2 Telemetry Grid
        grid = QGridLayout()
        grid.setSpacing(10)

        # 1. FPS Tile
        self.lbl_fps_val = QLabel("15.0 FPS")
        self.lbl_fps_val.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Color.SAFE};")
        lbl_fps_name = QLabel("Inference Rate")
        lbl_fps_name.setStyleSheet(f"font-size: 10px; color: {Color.TEXT_MUTED};")
        v1 = QVBoxLayout()
        v1.setSpacing(1)
        v1_top = QHBoxLayout()
        icon_fps = QLabel()
        icon_fps.setPixmap(render_svg_pixmap("zap", Color.SAFE, 13))
        v1_top.addWidget(icon_fps)
        v1_top.addWidget(self.lbl_fps_val)
        v1_top.addStretch()
        v1.addLayout(v1_top)
        v1.addWidget(lbl_fps_name)
        grid.addLayout(v1, 0, 0)

        # 2. RAM Tile
        self.lbl_ram_val = QLabel("240 MB")
        self.lbl_ram_val.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Color.ACCENT};")
        lbl_ram_name = QLabel("Memory RSS")
        lbl_ram_name.setStyleSheet(f"font-size: 10px; color: {Color.TEXT_MUTED};")
        v2 = QVBoxLayout()
        v2.setSpacing(1)
        v2_top = QHBoxLayout()
        icon_ram = QLabel()
        icon_ram.setPixmap(render_svg_pixmap("ram", Color.ACCENT, 13))
        v2_top.addWidget(icon_ram)
        v2_top.addWidget(self.lbl_ram_val)
        v2_top.addStretch()
        v2.addLayout(v2_top)
        v2.addWidget(lbl_ram_name)
        grid.addLayout(v2, 0, 1)

        # 3. CPU Load Tile
        self.lbl_cpu_val = QLabel("12%")
        self.lbl_cpu_val.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Color.TEXT_PRIMARY};")
        lbl_cpu_name = QLabel("CPU Utilization")
        lbl_cpu_name.setStyleSheet(f"font-size: 10px; color: {Color.TEXT_MUTED};")
        v3 = QVBoxLayout()
        v3.setSpacing(1)
        v3_top = QHBoxLayout()
        icon_cpu = QLabel()
        icon_cpu.setPixmap(render_svg_pixmap("cpu", Color.TEXT_SECONDARY, 13))
        v3_top.addWidget(icon_cpu)
        v3_top.addWidget(self.lbl_cpu_val)
        v3_top.addStretch()
        v3.addLayout(v3_top)
        v3.addWidget(lbl_cpu_name)
        grid.addLayout(v3, 1, 0)

        # 4. Uptime Tile
        self.lbl_uptime_val = QLabel("00:00:00")
        self.lbl_uptime_val.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {Color.TEXT_SECONDARY};")
        lbl_uptime_name = QLabel("System Uptime")
        lbl_uptime_name.setStyleSheet(f"font-size: 10px; color: {Color.TEXT_MUTED};")
        v4 = QVBoxLayout()
        v4.setSpacing(1)
        v4_top = QHBoxLayout()
        icon_uptime = QLabel()
        icon_uptime.setPixmap(render_svg_pixmap("clock", Color.TEXT_MUTED, 13))
        v4_top.addWidget(icon_uptime)
        v4_top.addWidget(self.lbl_uptime_val)
        v4_top.addStretch()
        v4.addLayout(v4_top)
        v4.addWidget(lbl_uptime_name)
        grid.addLayout(v4, 1, 1)

        layout.addLayout(grid)

    def _wire_signals(self) -> None:
        signal_bus.fps_updated.connect(self._on_fps_updated)
        signal_bus.memory_updated.connect(self._on_memory_updated)

    def _on_fps_updated(self, fps: float) -> None:
        color = Color.SAFE if fps >= 15.0 else (Color.WARNING if fps >= 8.0 else Color.CRITICAL)
        self.lbl_fps_val.setText(f"{fps:.1f} FPS")
        self.lbl_fps_val.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {color};")

    def _on_memory_updated(self, rss_mb: float) -> None:
        self.lbl_ram_val.setText(f"{rss_mb:.0f} MB")

    def _sample_telemetry(self) -> None:
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            self.lbl_cpu_val.setText(f"{cpu_pct:.0f}%")

            elapsed = int(time.time() - self._start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.lbl_uptime_val.setText(f"{h:02d}:{m:02d}:{s:02d}")
        except Exception:
            pass
