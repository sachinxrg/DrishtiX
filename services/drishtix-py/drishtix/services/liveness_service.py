"""
DrishtiX v4.0 — Anti-Spoofing / Liveness Detection Service.

Detects presentation attacks (printed photos, screen replays, masks) using
a combination of passive liveness checks that require no user cooperation:

1. Texture Analysis (LBP variance): Printed photos and screens exhibit
   uniform micro-texture patterns distinct from live skin.
2. Color Space Analysis (YCbCr chrominance): Live skin has characteristic
   chrominance distributions that differ from paper/screen reproductions.
3. Moiré Pattern Detection: Screen replays produce detectable moiré
   interference patterns visible in the frequency domain.

All checks run on CPU with minimal latency (<5ms per face crop on the
hot path). No additional model files required.

Reference:
- Boulkenafet et al., "Face Anti-Spoofing Based on Color Texture Analysis" (ICIP 2015)
- ISO/IEC 30107-3:2023 — Biometric presentation attack detection
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ─── Thresholds (tuned for balance between security and false rejection) ───
LBP_VARIANCE_THRESHOLD = 15.0       # Below this = suspiciously uniform texture
CHROMINANCE_STD_MIN = 5.0           # Minimum Cb/Cr standard deviation for live skin
MOIRE_ENERGY_THRESHOLD = 0.15       # Normalized high-frequency energy ratio
COMBINED_SCORE_THRESHOLD = 0.5      # Final liveness score threshold (0=spoof, 1=live)


@dataclass
class LivenessResult:
    """Result of liveness / anti-spoofing analysis."""

    is_live: bool
    score: float                     # 0.0 (definite spoof) to 1.0 (definite live)
    lbp_score: float = 0.0          # Texture uniformity score
    color_score: float = 0.0        # Chrominance distribution score
    moire_score: float = 0.0        # Moiré pattern absence score
    reason: str = ""                # Human-readable explanation if rejected


def _compute_lbp_variance(gray: np.ndarray) -> float:
    """
    Compute Local Binary Pattern variance as a texture uniformity metric.

    Live faces have rich, varied micro-textures (pores, fine lines).
    Printed photos and screens have smoother, more uniform textures.

    Uses a simplified LBP: compare each pixel to its 8 neighbors,
    then measure the variance of the resulting pattern histogram.

    Returns:
        LBP histogram variance (higher = more texture variation = more likely live).
    """
    if gray is None or gray.size == 0:
        return 0.0

    h, w = gray.shape
    if h < 10 or w < 10:
        return 0.0

    # Compute simplified LBP
    center = gray[1:-1, 1:-1].astype(np.int16)
    lbp = np.zeros_like(center, dtype=np.uint8)

    # 8 neighbor comparisons
    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
    for i, (dy, dx) in enumerate(offsets):
        neighbor = gray[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx].astype(np.int16)
        lbp |= ((neighbor >= center).astype(np.uint8) << i)

    # Histogram variance — higher variance = richer texture
    hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
    hist = hist.astype(np.float64) / max(hist.sum(), 1)
    variance = np.var(hist) * 1e6  # Scale for readability

    return float(variance)


def _compute_chrominance_score(face_bgr: np.ndarray) -> float:
    """
    Analyze YCbCr chrominance distribution for skin-like properties.

    Live skin has characteristic Cb/Cr distributions with moderate spread.
    Paper reproductions tend to have compressed chrominance ranges.
    Screen replays shift chrominance due to backlight color temperature.

    Returns:
        Score 0.0-1.0 (higher = more consistent with live skin).
    """
    if face_bgr is None or face_bgr.size == 0:
        return 0.0

    ycrcb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2YCrCb)
    cr = ycrcb[:, :, 1].astype(np.float64)
    cb = ycrcb[:, :, 2].astype(np.float64)

    cr_std = np.std(cr)
    cb_std = np.std(cb)

    # Live skin: moderate Cb/Cr spread (5-30 std dev typical)
    # Paper: very narrow spread (<5)
    # Screen: shifted mean + variable spread
    if cr_std < CHROMINANCE_STD_MIN or cb_std < CHROMINANCE_STD_MIN:
        return 0.1  # Suspiciously uniform

    # Score based on how "skin-like" the distribution is
    cr_mean = np.mean(cr)
    cb_mean = np.mean(cb)

    # Typical live skin: Cr in [130-175], Cb in [100-130]
    cr_in_range = 1.0 if 125 <= cr_mean <= 180 else 0.5
    cb_in_range = 1.0 if 95 <= cb_mean <= 140 else 0.5

    spread_score = min(1.0, (cr_std + cb_std) / 30.0)
    return float((cr_in_range + cb_in_range + spread_score) / 3.0)


def _compute_moire_score(gray: np.ndarray) -> float:
    """
    Detect moiré patterns from screen replay attacks via frequency analysis.

    Screen displays produce periodic interference patterns (moiré) that
    appear as distinctive peaks in the frequency domain. Live faces have
    more uniform frequency distributions.

    Returns:
        Score 0.0-1.0 (higher = less moiré = more likely live).
    """
    if gray is None or gray.size == 0:
        return 1.0

    h, w = gray.shape
    if h < 32 or w < 32:
        return 1.0

    # Resize to standard size for consistent analysis
    resized = cv2.resize(gray, (64, 64))
    f_transform = np.fft.fft2(resized.astype(np.float64))
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.abs(f_shift)

    # Separate high-frequency energy from total
    cy, cx = 32, 32
    mask_radius = 10
    total_energy = np.sum(magnitude ** 2)
    if total_energy < 1e-10:
        return 1.0

    # Zero out low frequencies
    y, x = np.ogrid[-cy:64 - cy, -cx:64 - cx]
    low_freq_mask = (x * x + y * y) <= mask_radius * mask_radius
    high_freq_magnitude = magnitude.copy()
    high_freq_magnitude[low_freq_mask] = 0

    high_energy = np.sum(high_freq_magnitude ** 2)
    energy_ratio = high_energy / total_energy

    # High ratio of high-frequency energy suggests moiré patterns
    if energy_ratio > MOIRE_ENERGY_THRESHOLD:
        return max(0.0, 1.0 - (energy_ratio - MOIRE_ENERGY_THRESHOLD) * 5.0)

    return 1.0


def check_liveness(face_bgr: np.ndarray) -> LivenessResult:
    """
    Run passive liveness detection on a face crop.

    Combines texture, chrominance, and frequency-domain analysis to
    produce a unified liveness score. No user cooperation required.

    Args:
        face_bgr: BGR face crop (should be at least 40x40 pixels).

    Returns:
        LivenessResult with is_live flag, combined score, and per-check scores.
    """
    if face_bgr is None or face_bgr.size == 0:
        return LivenessResult(is_live=False, score=0.0, reason="Empty face crop")

    h, w = face_bgr.shape[:2]
    if h < 30 or w < 30:
        return LivenessResult(is_live=False, score=0.0, reason="Face crop too small")

    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)

    # Run all three checks
    lbp_var = _compute_lbp_variance(gray)
    color_score = _compute_chrominance_score(face_bgr)
    moire_score = _compute_moire_score(gray)

    # Normalize LBP variance to 0-1 score
    lbp_score = min(1.0, lbp_var / (LBP_VARIANCE_THRESHOLD * 2.0))

    # Weighted combination: texture 40%, color 30%, moiré 30%
    combined = 0.4 * lbp_score + 0.3 * color_score + 0.3 * moire_score
    is_live = combined >= COMBINED_SCORE_THRESHOLD

    reason = ""
    if not is_live:
        reasons = []
        if lbp_score < 0.3:
            reasons.append("uniform texture (possible print)")
        if color_score < 0.3:
            reasons.append("abnormal chrominance (possible screen)")
        if moire_score < 0.5:
            reasons.append("moiré detected (possible screen replay)")
        reason = "; ".join(reasons) if reasons else "low combined liveness score"

    return LivenessResult(
        is_live=is_live,
        score=round(combined, 3),
        lbp_score=round(lbp_score, 3),
        color_score=round(color_score, 3),
        moire_score=round(moire_score, 3),
        reason=reason,
    )
