"""
DrishtiX v4.0 — Image processing and Qt converter utilities.

High-performance OpenCV Mat ↔ QImage / QPixmap conversion with zero/minimal copy,
tactical UI overlay drawing (vivid HUD-style bounding boxes, category badges, landmarks).
"""

from typing import Optional, Sequence, Union
import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap

from drishtix.core.constants import (
    CRIMINAL_COLOR_BGR,
    MISSING_COLOR_BGR,
    UNKNOWN_COLOR_BGR,
)
from drishtix.core.enums import TargetCategory


def mat_to_qimage(cv_img: np.ndarray) -> QImage:
    """
    Convert an OpenCV BGR numpy array to a PySide6 QImage.
    """
    if cv_img is None or cv_img.size == 0:
        return QImage()

    if len(cv_img.shape) == 2:
        height, width = cv_img.shape
        bytes_per_line = width
        return QImage(
            cv_img.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_Grayscale8,
        ).copy()

    height, width, channels = cv_img.shape
    if channels == 3:
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * width
        return QImage(
            rgb_img.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

    if channels == 4:
        rgba_img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        bytes_per_line = 4 * width
        return QImage(
            rgba_img.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGBA8888,
        ).copy()

    return QImage()


def mat_to_qpixmap(cv_img: np.ndarray) -> QPixmap:
    """
    Convert an OpenCV BGR numpy array directly to a QPixmap.
    """
    qimg = mat_to_qimage(cv_img)
    if qimg.isNull():
        return QPixmap()
    return QPixmap.fromImage(qimg)


def safe_crop(image: np.ndarray, bbox: Sequence[int], padding_ratio: float = 0.0) -> Optional[np.ndarray]:
    """
    Safely crop a region of interest from an image with boundary checking and optional padding.
    """
    if image is None or image.size == 0:
        return None

    img_h, img_w = image.shape[:2]
    x, y, w, h = bbox

    if padding_ratio > 0:
        pad_x = int(w * padding_ratio)
        pad_y = int(h * padding_ratio)
        x = max(0, x - pad_x)
        y = max(0, y - pad_y)
        w = min(img_w - x, w + 2 * pad_x)
        h = min(img_h - y, h + 2 * pad_y)

    x1 = max(0, min(int(x), img_w - 1))
    y1 = max(0, min(int(y), img_h - 1))
    x2 = max(x1 + 1, min(int(x + w), img_w))
    y2 = max(y1 + 1, min(int(y + h), img_h))

    if x2 <= x1 or y2 <= y1:
        return None

    return image[y1:y2, x1:x2].copy()


def draw_tactical_bbox(
    frame: np.ndarray,
    bbox: Sequence[int],
    name: str = "Unknown",
    category: Optional[Union[str, TargetCategory]] = None,
    confidence: Optional[float] = None,
    landmarks: Optional[np.ndarray] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
) -> None:
    """
    Draw a vivid tactical HUD bounding box on the OpenCV frame in-place.

    Color Matrix:
    - CRIMINAL: Vivid Crimson Red (0, 0, 255) in BGR
    - MISSING PERSON: Vivid Electric Cyan-Blue (255, 210, 0) in BGR
    - UNKNOWN / DETECTED: Tactical Emerald Green (50, 220, 80) in BGR
    """
    if frame is None or frame.size == 0:
        return

    x, y, w, h = [int(v) for v in bbox]
    img_h, img_w = frame.shape[:2]

    # Resolve category and corresponding vibrant colors
    cat_str = str(category).upper() if category is not None else ""
    is_criminal = "CRIM" in cat_str
    is_missing = "MISS" in cat_str
    is_known_target = (name and name != "Unknown") or (confidence is not None and confidence > 0.0)

    if is_criminal or (is_known_target and not is_missing):
        # 1. CRIMINAL / HIGH THREAT: Bright Crimson Red
        box_color = (0, 0, 255)       # Pure Red in BGR
        badge_bg = (0, 0, 220)
        badge_text_color = (255, 255, 255)  # Crisp White
        prefix = "CRIMINAL: "
    elif is_missing:
        # 2. MISSING PERSON: Electric Cyan Blue
        box_color = (255, 210, 0)     # Bright Cyan-Blue in BGR
        badge_bg = (255, 200, 0)
        badge_text_color = (15, 23, 42)     # High-contrast Dark Navy
        prefix = "MISSING: "
    else:
        # 3. UNKNOWN / DETECTED FACE: Tactical Tech Emerald Green
        box_color = (50, 220, 80)     # Emerald Green in BGR
        badge_bg = (15, 23, 42)       # Dark Glass Pill
        badge_text_color = (100, 255, 140)  # Bright Green Text
        prefix = ""

    # Corner bracket styling
    line_length = max(12, min(w, h) // 4)
    bracket_thickness = 3
    box_thickness = 2

    # Draw Corner Brackets (Top-Left, Top-Right, Bottom-Left, Bottom-Right)
    # Top-Left
    cv2.line(frame, (x, y), (x + line_length, y), box_color, bracket_thickness)
    cv2.line(frame, (x, y), (x, y + line_length), box_color, bracket_thickness)
    # Top-Right
    cv2.line(frame, (x + w, y), (x + w - line_length, y), box_color, bracket_thickness)
    cv2.line(frame, (x + w, y), (x + w, y + line_length), box_color, bracket_thickness)
    # Bottom-Left
    cv2.line(frame, (x, y + h), (x + line_length, y + h), box_color, bracket_thickness)
    cv2.line(frame, (x, y + h), (x, y + h - line_length), box_color, bracket_thickness)
    # Bottom-Right
    cv2.line(frame, (x + w, y + h), (x + w - line_length, y + h), box_color, bracket_thickness)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - line_length), box_color, bracket_thickness)

    # Draw perimeter boundary box
    cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, box_thickness, cv2.LINE_AA)

    # Draw 5-point facial landmarks if present
    if landmarks is not None and len(landmarks) >= 5:
        for lm in landmarks:
            lx, ly = int(lm[0]), int(lm[1])
            if 0 <= lx < img_w and 0 <= ly < img_h:
                cv2.circle(frame, (lx, ly), 2, (0, 255, 255), -1, cv2.LINE_AA)

    # Construct label text
    demo_parts = []
    if gender:
        demo_parts.append(gender.upper())
    if age is not None:
        demo_parts.append(f"~{age}y")
    demo_str = f" ({', '.join(demo_parts)})" if demo_parts else ""

    if confidence is not None:
        label = f"{prefix}{name} [{confidence * 100:.0f}%]{demo_str}"
    else:
        label = f"{prefix}{name}{demo_str}"

    # Calculate text size and badge dimensions
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.52
    font_thickness = 2 if (is_criminal or is_missing) else 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

    badge_h = text_h + baseline + 8
    badge_w = text_w + 12

    badge_y1 = max(0, y - badge_h)
    badge_y2 = badge_y1 + badge_h
    badge_x1 = x
    badge_x2 = min(img_w, x + badge_w)

    # Draw solid pill badge
    cv2.rectangle(frame, (badge_x1, badge_y1), (badge_x2, badge_y2), badge_bg, -1)
    # Draw badge border
    cv2.rectangle(frame, (badge_x1, badge_y1), (badge_x2, badge_y2), box_color, 1, cv2.LINE_AA)

    # Draw crisp text
    text_x = badge_x1 + 6
    text_y = badge_y2 - baseline - 4
    cv2.putText(
        frame,
        label,
        (text_x, text_y),
        font,
        font_scale,
        badge_text_color,
        font_thickness,
        cv2.LINE_AA,
    )
