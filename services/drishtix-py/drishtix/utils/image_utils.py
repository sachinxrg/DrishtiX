"""
DrishtiX v4.0 — Image processing and Qt converter utilities.

High-performance OpenCV Mat ↔ QImage / QPixmap conversion with zero/minimal copy,
tactical UI overlay drawing (HUD-style bounding boxes, category badges, landmarks).
"""

from typing import Optional, Sequence
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

    Args:
        cv_img: Input BGR image (H, W, 3) or Grayscale image (H, W).

    Returns:
        QImage representation ready for Qt rendering.
    """
    if cv_img is None or cv_img.size == 0:
        return QImage()

    if len(cv_img.shape) == 2:
        # Grayscale
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
        # Convert BGR to RGB
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
        # BGRA to RGBA
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

    Args:
        cv_img: Input BGR image.

    Returns:
        QPixmap instance.
    """
    qimg = mat_to_qimage(cv_img)
    if qimg.isNull():
        return QPixmap()
    return QPixmap.fromImage(qimg)


def safe_crop(image: np.ndarray, bbox: Sequence[int], padding_ratio: float = 0.0) -> Optional[np.ndarray]:
    """
    Safely crop a region of interest from an image with boundary checking and optional padding.

    Args:
        image: Full image (H, W, C).
        bbox: (x, y, w, h) bounding box.
        padding_ratio: Optional expansion factor (e.g. 0.1 for 10% border padding).

    Returns:
        Cropped image slice as a numpy array, or None if invalid.
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

    crop = image[y1:y2, x1:x2].copy()
    return crop


def draw_tactical_bbox(
    frame: np.ndarray,
    bbox: Sequence[int],
    name: str = "Unknown",
    category: Optional[str | TargetCategory] = None,
    confidence: Optional[float] = None,
    landmarks: Optional[np.ndarray] = None,
) -> None:
    """
    Draw a HUD-style tactical bounding box on the image in-place.

    Features:
    - Corner brackets for tactical look
    - Category-themed solid background header badge
    - WCAG AA high-contrast dark text on bright pill/badge
    - 5-point facial landmark crosshairs if provided
    """
    x, y, w, h = [int(v) for v in bbox]
    img_h, img_w = frame.shape[:2]

    # Determine colors
    if isinstance(category, TargetCategory):
        color = category.box_color_bgr
    elif isinstance(category, str):
        try:
            color = TargetCategory(category.upper()).box_color_bgr
        except ValueError:
            color = UNKNOWN_COLOR_BGR
    else:
        color = UNKNOWN_COLOR_BGR

    # Corner bracket length
    line_length = max(10, min(w, h) // 4)
    thickness = 2

    # Draw 4 corner brackets
    # Top-Left
    cv2.line(frame, (x, y), (x + line_length, y), color, thickness)
    cv2.line(frame, (x, y), (x, y + line_length), color, thickness)

    # Top-Right
    cv2.line(frame, (x + w, y), (x + w - line_length, y), color, thickness)
    cv2.line(frame, (x + w, y), (x + w, y + line_length), color, thickness)

    # Bottom-Left
    cv2.line(frame, (x, y + h), (x + line_length, y + h), color, thickness)
    cv2.line(frame, (x, y + h), (x, y + h - line_length), color, thickness)

    # Bottom-Right
    cv2.line(frame, (x + w, y + h), (x + w - line_length, y + h), color, thickness)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - line_length), color, thickness)

    # Draw semi-transparent boundary box (subtle)
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1, cv2.LINE_AA)

    # Draw landmarks if provided (5-points: right_eye, left_eye, nose, right_mouth, left_mouth)
    if landmarks is not None and len(landmarks) >= 5:
        for lm in landmarks:
            lx, ly = int(lm[0]), int(lm[1])
            if 0 <= lx < img_w and 0 <= ly < img_h:
                cv2.circle(frame, (lx, ly), 2, (0, 255, 255), -1, cv2.LINE_AA)

    # Construct label text
    if confidence is not None:
        label = f"{name} [{confidence * 100:.0f}%]"
    else:
        label = name

    # Label badge background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

    badge_h = text_h + baseline + 6
    badge_w = text_w + 10

    badge_y1 = max(0, y - badge_h)
    badge_y2 = badge_y1 + badge_h
    badge_x1 = x
    badge_x2 = min(img_w, x + badge_w)

    # Draw solid pill badge
    cv2.rectangle(frame, (badge_x1, badge_y1), (badge_x2, badge_y2), color, -1)

    # Draw dark text on bright background for WCAG contrast
    text_x = badge_x1 + 5
    text_y = badge_y2 - baseline - 3
    cv2.putText(
        frame,
        label,
        (text_x, text_y),
        font,
        font_scale,
        (13, 15, 20),  # Dark background text (#0D0F14)
        font_thickness,
        cv2.LINE_AA,
    )
