#!/usr/bin/env python3
"""
DrishtiX v4.0 — QSS Generator.

Renders drishtix_glass.qss from the Jinja2 template + theme_tokens.py.
Single source of truth — the .qss file is GENERATED OUTPUT, never hand-edited.

Usage:
    python tools/generate_qss.py           # Generate/overwrite the .qss
    python tools/generate_qss.py --check   # CI mode: fail if .qss is stale
"""

import argparse
import sys
from pathlib import Path

# Resolve project paths
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
STYLES_DIR = PROJECT_ROOT / "drishtix" / "ui" / "styles"
TEMPLATE_FILE = STYLES_DIR / "drishtix_glass.qss.j2"
OUTPUT_FILE = STYLES_DIR / "drishtix_glass.qss"

# Add project root to path for imports
sys.path.insert(0, str(PROJECT_ROOT))


def generate() -> str:
    """Render QSS from Jinja2 template using design tokens."""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        print("ERROR: jinja2 is required. Install with: pip install jinja2>=3.0")
        sys.exit(1)

    from drishtix.ui.theme_tokens import (
        Breakpoint,
        Color,
        Elevation,
        Radius,
        Spacing,
        Typography,
    )

    env = Environment(
        loader=FileSystemLoader(str(STYLES_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template("drishtix_glass.qss.j2")

    output = template.render(
        color=Color,
        elevation=Elevation,
        radius=Radius,
        spacing=Spacing,
        breakpoint=Breakpoint,
        typography=Typography,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate DrishtiX QSS from tokens")
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: fail if the checked-in .qss differs from generated output",
    )
    args = parser.parse_args()

    generated = generate()

    if args.check:
        if not OUTPUT_FILE.exists():
            print(f"FAIL: {OUTPUT_FILE} does not exist. Run: python tools/generate_qss.py")
            sys.exit(1)

        existing = OUTPUT_FILE.read_text(encoding="utf-8")
        if existing.strip() != generated.strip():
            print(f"FAIL: {OUTPUT_FILE} is stale. Regenerate with: python tools/generate_qss.py")
            sys.exit(1)

        print(f"OK: {OUTPUT_FILE} is up-to-date with tokens.")
        sys.exit(0)

    # Write generated output
    OUTPUT_FILE.write_text(generated, encoding="utf-8")
    lines = generated.count("\n") + 1
    print(f"Generated {OUTPUT_FILE} ({lines} lines)")


if __name__ == "__main__":
    main()
