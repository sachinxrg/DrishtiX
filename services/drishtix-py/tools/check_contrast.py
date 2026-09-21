#!/usr/bin/env python3
"""
DrishtiX v4.0 — WCAG AA Contrast Audit Gate.

Calculates relative luminance and contrast ratios for all critical
text-on-background color pairings in the design token system.
Exits non-zero if any pair falls below WCAG AA threshold (4.5:1 for normal text).

Usage:
    python tools/check_contrast.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from drishtix.ui.theme_tokens import Color  # noqa: E402  (import needs the sys.path bootstrap above)


def parse_hex_color(hex_str: str) -> tuple[float, float, float]:
    """Parse #RRGGBB hex string to normalized RGB floats [0.0, 1.0]."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 6:
        r = int(hex_clean[0:2], 16) / 255.0
        g = int(hex_clean[2:4], 16) / 255.0
        b = int(hex_clean[4:6], 16) / 255.0
        return (r, g, b)
    elif len(hex_clean) == 3:
        r = int(hex_clean[0] * 2, 16) / 255.0
        g = int(hex_clean[1] * 2, 16) / 255.0
        b = int(hex_clean[2] * 2, 16) / 255.0
        return (r, g, b)
    raise ValueError(f"Invalid hex color: {hex_str}")


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    """Calculate WCAG 2.1 relative luminance for sRGB."""
    def channel_luminance(c: float) -> float:
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel_luminance(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between two hex colors."""
    l1 = relative_luminance(parse_hex_color(fg_hex))
    l2 = relative_luminance(parse_hex_color(bg_hex))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def main() -> None:
    # Text-on-background pairs across the app
    PAIRS = [
        ("Primary Text on Canvas", Color.TEXT_PRIMARY, Color.CANVAS, 4.5),
        ("Primary Text on White Card", Color.TEXT_PRIMARY, Color.WHITE, 4.5),
        ("Body Text on Canvas", Color.TEXT_BODY, Color.CANVAS, 4.5),
        ("Secondary Text on White Card", Color.TEXT_SECONDARY, Color.WHITE, 4.5),
        ("Secondary Text on Slate-100", Color.TEXT_SECONDARY, Color.NEU_SURFACE, 4.5),
        ("Accent Button (White on Indigo)", Color.WHITE, Color.ACCENT, 4.5),
        ("Safe Badge (Emerald Bold on Emerald BG)", Color.SAFE_BOLD, Color.SAFE_BG, 4.5),
        ("Critical Badge (White on Crimson-600)", Color.WHITE, Color.CRITICAL_BOLD, 4.5),
        ("Missing Badge (White on Cyan-800)", Color.WHITE, Color.INFO_SKY, 4.5),
    ]

    print("=======================================================================")
    print(" DrishtiX v4.0 -- WCAG 2.1 Contrast Compliance Gate")
    print("=======================================================================")

    failed = 0
    for name, fg, bg, min_ratio in PAIRS:
        ratio = contrast_ratio(fg, bg)
        passed = ratio >= min_ratio
        status = "PASS" if passed else "FAIL"
        print(f"[{status:4s}] {name:<38} {fg} on {bg} -> {ratio:.2f}:1 (min: {min_ratio}:1)")
        if not passed:
            failed += 1

    print("-----------------------------------------------------------------------")
    if failed == 0:
        print("ALL TOKEN PAIRS COMPLIANT WITH WCAG AA (>= 4.5:1)")
        sys.exit(0)
    else:
        print(f"{failed} PAIRS FAILED CONTRAST AUDIT")
        sys.exit(1)


if __name__ == "__main__":
    main()
