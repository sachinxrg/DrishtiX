"""
DrishtiX v3.0 — Architectural Diagrams DOCX Generator (Print-Optimized)
=======================================================================
Directives Implemented:
1. Mermaid Font & Node Scaling:
   Injects %%{init: {"theme": "default", "themeVariables": {"fontSize": "24px", "fontFamily": "arial", "nodePadding": 15}}}%%
   at the top of EVERY Mermaid diagram code block.

2. Python-Docx Landscape Orientation:
   Creates a new Landscape Section (11" x 8.5") for each complex diagram,
   scaling the rendered high-DPI image to fill the page (9.8" width) for maximum print readability.

Run:
    python generate_diagrams_docx.py

Output:
    docs/DrishtiX_Diagrams.docx
"""

import urllib.request
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
MD_PATH = os.path.join(PROJECT_ROOT, "docs", "DrishtiX_Diagrams.md")
DOCX_PATH = os.path.join(PROJECT_ROOT, "docs", "DrishtiX_Diagrams.docx")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch", "diagram_imgs")

os.makedirs(SCRATCH_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DOCX_PATH), exist_ok=True)

MERMAID_INIT_HEADER = '%%{init: {"theme": "default", "themeVariables": {"fontSize": "24px", "fontFamily": "arial", "nodePadding": 15}}}%%'

def render_mermaid_to_png(mermaid_code, output_image_path):
    """Injects 24px font scaling header if missing and renders high-res PNG via Kroki POST API."""
    try:
        clean_code = mermaid_code.strip()
        if not clean_code.startswith('%%{init:'):
            clean_code = MERMAID_INIT_HEADER + '\n' + clean_code
            
        url = "https://kroki.io/mermaid/png"
        headers = {
            'Content-Type': 'text/plain; charset=utf-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        data = clean_code.encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=20) as response:
            img_bytes = response.read()
            with open(output_image_path, 'wb') as f:
                f.write(img_bytes)
        print(f"  [OK] Rendered print-scaled diagram: {os.path.basename(output_image_path)} ({len(img_bytes):,} bytes)", flush=True)
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to render diagram ({os.path.basename(output_image_path)}): {e}", flush=True)
        return False

def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def style_table_header(table):
    if len(table.rows) > 0:
        for cell in table.rows[0].cells:
            set_cell_shading(cell, "1A1A2E")
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    run.font.size = Pt(9.5)
                    run.font.name = "Calibri"
    for i, row in enumerate(table.rows[1:], 1):
        bg = "F8F9FA" if i % 2 == 0 else "FFFFFF"
        for cell in row.cells:
            set_cell_shading(cell, bg)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9.5)
                    run.font.name = "Calibri"
    tbl = table._tbl
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '  <w:top w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '  <w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '  <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '</w:tblBorders>'
    )
    tbl.tblPr.append(borders)

def add_rich_paragraph(doc, text, bold=False, italic=False, size=Pt(11), alignment=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = alignment
    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`[^`]+`)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
            run = p.add_run(part[1:-1])
            run.italic = True
        elif part.startswith('`') and part.endswith('`'):
            run = p.add_run(part[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0xC7, 0x25, 0x4E)
        else:
            run = p.add_run(part)

        if bold: run.bold = True
        if italic: run.italic = True
        run.font.name = "Calibri"
        run.font.size = size
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    return p

def parse_markdown_table(lines):
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith('|') and not re.match(r'^\|[\s\-:|]+\|$', line):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            rows.append(cells)
    return rows

with open(MD_PATH, 'r', encoding='utf-8') as f:
    md_content = f.read()

doc = Document()

# Default Initial Section (Portrait for Cover/Header)
initial_section = doc.sections[0]
initial_section.top_margin = Cm(2)
initial_section.bottom_margin = Cm(2)
initial_section.left_margin = Cm(2.5)
initial_section.right_margin = Cm(2.5)

style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)
style.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

for level, sz in [(1, 20), (2, 15), (3, 12.5)]:
    hs = doc.styles[f'Heading {level}']
    hf = hs.font
    hf.name = 'Calibri'
    hf.bold = True
    hf.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    hf.size = Pt(sz)
    hs.paragraph_format.space_before = Pt(16 if level <= 2 else 10)
    hs.paragraph_format.space_after = Pt(8 if level <= 2 else 4)

# Title Header
p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_t = p_title.add_run("DrishtiX v3.0 — Architectural Diagrams & Visual Models")
r_t.bold = True
r_t.font.size = Pt(24)
r_t.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_s = p_sub.add_run("Print-Optimized High-DPI Visualizations & Schema Specifications")
r_s.font.size = Pt(13)
r_s.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

doc.add_paragraph()

lines = md_content.split('\n')
i = 0
diagram_count = 0
current_heading = ""

while i < len(lines):
    line = lines[i].rstrip('\n').rstrip('\r')

    # Headings
    h_match = re.match(r'^(#{1,3})\s+(.*)', line)
    if h_match:
        level = len(h_match.group(1))
        title = h_match.group(2).strip()
        title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)
        current_heading = title
        doc.add_heading(title, level=level)
        i += 1
        continue

    # Horizontal Rules
    if re.match(r'^---+\s*$', line.strip()):
        i += 1
        continue

    # Blockquotes
    if line.strip().startswith('>'):
        quote_text = line.strip().lstrip('>').strip()
        p = add_rich_paragraph(doc, quote_text, italic=True)
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="18" w:space="4" w:color="1A1A2E"/></w:pBdr>')
        pPr.append(pBdr)
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9" w:val="clear"/>')
        pPr.append(shading)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(8)
        i += 1
        continue

    # Markdown Tables
    if line.strip().startswith('|'):
        tbl_lines = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            tbl_lines.append(lines[i])
            i += 1
        rows = parse_markdown_table(tbl_lines)
        if rows:
            num_cols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for ri, row_data in enumerate(rows):
                for ci, cell_text in enumerate(row_data):
                    if ci < num_cols:
                        cell = table.cell(ri, ci)
                        cell.text = ""
                        p = cell.paragraphs[0]
                        clean = cell_text.strip()
                        parts = re.split(r'(\*\*.*?\*\*|`[^`]+`)', clean)
                        for part in parts:
                            if part.startswith('**') and part.endswith('**'):
                                run = p.add_run(part[2:-2])
                                run.bold = True
                            elif part.startswith('`') and part.endswith('`'):
                                run = p.add_run(part[1:-1])
                                run.font.name = 'Consolas'
                                run.font.size = Pt(9)
                                run.font.color.rgb = RGBColor(0xC7, 0x25, 0x4E)
                            else:
                                run = p.add_run(part)
                            run.font.name = 'Calibri'
                            run.font.size = Pt(9.5)
            style_table_header(table)
            doc.add_paragraph()
        continue

    # Mermaid Code Blocks -> DIRECTIVE 2: Add LANDSCAPE section & render print-scaled diagram
    if line.strip().startswith('```mermaid'):
        diagram_count += 1
        mermaid_lines = []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            mermaid_lines.append(lines[i])
            i += 1
        i += 1 # skip closing ```

        mermaid_code = '\n'.join(mermaid_lines)
        img_filename = f"diagram_{diagram_count}.png"
        img_path = os.path.join(SCRATCH_DIR, img_filename)

        print(f"Rendering Diagram {diagram_count} with 24px font scaling...", flush=True)
        success = render_mermaid_to_png(mermaid_code, img_path)

        # DIRECTIVE 2: Switch to LANDSCAPE Section for Diagram Page
        ls_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
        ls_section.orientation = WD_ORIENT.LANDSCAPE
        ls_section.page_width = Inches(11)
        ls_section.page_height = Inches(8.5)
        ls_section.top_margin = Inches(0.5)
        ls_section.bottom_margin = Inches(0.5)
        ls_section.left_margin = Inches(0.5)
        ls_section.right_margin = Inches(0.5)

        if success and os.path.exists(img_path):
            p_head = doc.add_paragraph()
            r_h = p_head.add_run(f"Diagram {diagram_count}: {current_heading}")
            r_h.bold = True
            r_h.font.size = Pt(14)
            r_h.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
            p_head.paragraph_format.space_after = Pt(4)

            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(4)
            p_img.paragraph_format.space_after = Pt(4)

            # Insert Image scaled to full landscape page width (9.8 inches max)
            run_img = p_img.add_run()
            run_img.add_picture(img_path, width=Inches(9.8))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_cap = p_cap.add_run(f"Figure {diagram_count}: High-Resolution Landscape Diagram (Print-Scaled 24px Font)")
            r_cap.font.name = 'Calibri'
            r_cap.font.size = Pt(9.5)
            r_cap.italic = True
            r_cap.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
            p_cap.paragraph_format.space_after = Pt(8)
        else:
            p_err = doc.add_paragraph()
            p_err.add_run(f"[Diagram {diagram_count} - Code Representation]\n" + mermaid_code)
            p_err.paragraph_format.space_after = Pt(12)

        continue

    if line.strip():
        add_rich_paragraph(doc, line.strip())
    i += 1

# Save final docx (with fallback timestamp if opened/locked in MS Word)
import time
target_save_path = DOCX_PATH
try:
    doc.save(target_save_path)
except PermissionError:
    try:
        target_save_path = os.path.join(PROJECT_ROOT, "docs", "DrishtiX_Diagrams_PrintOptimized.docx")
        doc.save(target_save_path)
        print(f"\n[NOTICE] Primary file was locked in Word. Saved to print-optimized fallback path:")
    except PermissionError:
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        target_save_path = os.path.join(PROJECT_ROOT, "docs", f"DrishtiX_Diagrams_Expanded_{timestamp_str}.docx")
        doc.save(target_save_path)
        print(f"\n[NOTICE] Previous files locked in Word. Saved to fresh timestamped target path:")

print(f"\n[SUCCESS] Print-optimized document saved successfully to:", flush=True)
print(f"   {target_save_path}", flush=True)
print(f"   Size: {os.path.getsize(target_save_path):,} bytes", flush=True)
