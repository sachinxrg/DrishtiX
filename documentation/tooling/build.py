"""
DrishtiX Documentation Suite — Master Build Script.

Builds all six documents from Markdown source to DOCX using Pandoc.
Also renders Mermaid diagrams to PNG.

Usage:
    python build.py                    # Build all documents
    python build.py DX-SDD             # Build single document
    python build.py --diagrams-only    # Render diagrams only
    python build.py --summary          # Print build summary
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # documentation/
SRC_DIR = BASE_DIR / "src"
OUTPUT_DIR = BASE_DIR / "output"
THEME_DIR = BASE_DIR / "theme"
DIAGRAMS_SRC = BASE_DIR / "diagrams" / "src"
DIAGRAMS_OUT = BASE_DIR / "diagrams" / "out"
DATA_DIR = BASE_DIR / "data"
TOOLING_DIR = BASE_DIR / "tooling"
BUILD_DIR = BASE_DIR / "_build"
REFERENCE_DOCX = THEME_DIR / "reference.docx"

# Refresh PATH so freshly-installed pandoc is found
os.environ["Path"] = (
    os.environ.get("Path", "")
    + ";"
    + os.path.join(os.environ.get("LOCALAPPDATA", ""), "Pandoc")
    + ";"
    + os.path.join(os.environ.get("PROGRAMFILES", ""), "Pandoc")
)

# ─── Document Registry ──────────────────────────────────────────────
DOCUMENTS = {
    "DX-SDD": {
        "title": "System Design Document",
        "filename": "DrishtiX_01_System_Design_Document_v1.0",
        "owner": "Arjun Prajapati",
    },
    "DX-BED": {
        "title": "Backend Document",
        "filename": "DrishtiX_02_Backend_Document_v1.0",
        "owner": "Tejas Gohil",
    },
    "DX-FED": {
        "title": "Frontend Document",
        "filename": "DrishtiX_03_Frontend_Document_v1.0",
        "owner": "Tejas Gohil",
    },
    "DX-TST": {
        "title": "Testing Document",
        "filename": "DrishtiX_04_Testing_Document_v1.0",
        "owner": "Rohan Mallah",
    },
    "DX-EVD": {
        "title": "Evidence Pack",
        "filename": "DrishtiX_05_Evidence_Pack_v1.0",
        "owner": "Sachidanand Gond, Amos Raj Kennedy",
    },
    "DX-FPR": {
        "title": "Final Project Report",
        "filename": "DrishtiX_06_Final_Project_Report_v1.0",
        "owner": "Sachidanand Gond",
    },
}


def load_facts():
    """Load the shared facts registry."""
    facts_path = DATA_DIR / "facts.json"
    if facts_path.exists():
        with open(facts_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def render_diagrams():
    """Render all Mermaid .mmd files to PNG."""
    DIAGRAMS_OUT.mkdir(parents=True, exist_ok=True)
    mmdc = TOOLING_DIR / "node_modules" / ".bin" / "mmdc.cmd"
    
    if not mmdc.exists():
        mmdc_alt = TOOLING_DIR / "node_modules" / ".bin" / "mmdc"
        if mmdc_alt.exists():
            mmdc = mmdc_alt
        else:
            print("[WARN] Mermaid CLI (mmdc) not found. Skipping diagram rendering.")
            print(f"       Looked in: {mmdc}")
            return 0
    
    rendered = 0
    if not DIAGRAMS_SRC.exists():
        print(f"[WARN] No diagram source dir: {DIAGRAMS_SRC}")
        return 0
    
    for mmd_file in sorted(DIAGRAMS_SRC.glob("*.mmd")):
        out_png = DIAGRAMS_OUT / f"{mmd_file.stem}.png"
        print(f"  Rendering {mmd_file.name} -> {out_png.name}")
        try:
            subprocess.run(
                [str(mmdc), "-i", str(mmd_file), "-o", str(out_png),
                 "-w", "2400", "-b", "white", "--scale", "2"],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            rendered += 1
        except subprocess.CalledProcessError as e:
            print(f"  [ERR] Failed to render {mmd_file.name}: {e.stderr[:200]}")
        except FileNotFoundError:
            print(f"  [ERR] mmdc not found at {mmdc}")
            break
    
    return rendered


def build_document(doc_id: str):
    """Build a single document from Markdown to DOCX."""
    if doc_id not in DOCUMENTS:
        print(f"[ERR] Unknown document ID: {doc_id}")
        return False
    
    doc_info = DOCUMENTS[doc_id]
    src_dir = SRC_DIR / doc_id
    
    if not src_dir.exists():
        print(f"[SKIP] No source directory for {doc_id}: {src_dir}")
        return False
    
    # Collect all markdown files in order (NN-title.md)
    md_files = sorted(src_dir.glob("*.md"))
    if not md_files:
        print(f"[SKIP] No .md files in {src_dir}")
        return False
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{doc_info['filename']}.docx"
    
    # Build Pandoc command
    cmd = [
        "pandoc",
        "--from", "markdown+pipe_tables+yaml_metadata_block+fenced_code_blocks+inline_notes+smart",
        "--to", "docx",
        "--reference-doc", str(REFERENCE_DOCX),
        "--toc",
        "--toc-depth=3",
        "--number-sections",
        "--standalone",
        "--output", str(output_file),
    ]
    
    # Add resource path for images
    cmd.extend(["--resource-path", str(BASE_DIR)])
    cmd.extend(["--resource-path", str(DIAGRAMS_OUT)])
    cmd.extend(["--resource-path", str(BASE_DIR / "assets")])
    
    # Add all markdown files as input
    for md_file in md_files:
        cmd.append(str(md_file))
    
    print(f"  Building {doc_id}: {len(md_files)} files -> {output_file.name}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stderr:
            # Pandoc warnings
            for line in result.stderr.strip().split("\n"):
                if line.strip():
                    print(f"    [WARN] {line.strip()}")
        
        # Get file size
        size_kb = output_file.stat().st_size / 1024
        print(f"  [OK] {doc_id}: {output_file.name} ({size_kb:.0f} KB)")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  [ERR] {doc_id} build failed:")
        print(f"    {e.stderr[:500]}")
        return False
    except FileNotFoundError:
        print("[ERR] pandoc not found. Install with: winget install JohnMacFarlane.Pandoc")
        return False


def build_all():
    """Build all documents."""
    print("=" * 60)
    print(f"DrishtiX Documentation Suite — Build")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. Render diagrams
    print("\n--- Phase 1: Rendering Diagrams ---")
    diagram_count = render_diagrams()
    print(f"  Diagrams rendered: {diagram_count}")
    
    # 2. Build documents
    print("\n--- Phase 2: Building Documents ---")
    results = {}
    for doc_id in DOCUMENTS:
        success = build_document(doc_id)
        results[doc_id] = success
    
    # 3. Summary
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("-" * 60)
    print(f"{'Document':<10} {'Title':<35} {'Status':<10}")
    print("-" * 60)
    
    built = 0
    skipped = 0
    for doc_id, success in results.items():
        title = DOCUMENTS[doc_id]["title"]
        status = "OK" if success else "SKIP/ERR"
        print(f"{doc_id:<10} {title:<35} {status:<10}")
        if success:
            built += 1
        else:
            skipped += 1
    
    print("-" * 60)
    print(f"Built: {built} | Skipped/Error: {skipped} | Diagrams: {diagram_count}")
    print("=" * 60)
    
    return built > 0


def print_summary():
    """Print summary of existing output files."""
    if not OUTPUT_DIR.exists():
        print("No output directory found.")
        return
    
    print("\nExisting output files:")
    print("-" * 60)
    for f in sorted(OUTPUT_DIR.glob("*.docx")):
        size_kb = f.stat().st_size / 1024
        mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {f.name:<55} {size_kb:>6.0f} KB  {mod}")


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--summary" in args:
        print_summary()
    elif "--diagrams-only" in args:
        render_diagrams()
    elif args and args[0] in DOCUMENTS:
        render_diagrams()
        build_document(args[0])
    else:
        build_all()
