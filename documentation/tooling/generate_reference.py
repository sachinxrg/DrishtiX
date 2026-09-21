"""
DrishtiX Documentation Suite — Reference DOCX Template Generator.

Creates a reference.docx with the design system's typography, colours,
and page layout. Used by Pandoc --reference-doc for styled DOCX output.

Requires: python-docx
Install:  pip install python-docx
"""

import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import copy


# ─── Design Tokens ──────────────────────────────────────────────────
NAVY       = RGBColor(0x0B, 0x1F, 0x3A)
INDIGO     = RGBColor(0x4F, 0x46, 0xE5)
INDIGO_600 = RGBColor(0x3E, 0x56, 0xE0)
TEAL       = RGBColor(0x14, 0xB8, 0xA6)
AMBER      = RGBColor(0xF5, 0x9E, 0x0B)
BODY_TEXT  = RGBColor(0x11, 0x18, 0x27)
MUTED_TEXT = RGBColor(0x64, 0x74, 0x8B)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF3, 0xF4, 0xF6)
BORDER     = RGBColor(0xE5, 0xE7, 0xEB)

HEADING_FONT = "Calibri"   # Pandoc reference uses system fonts; calibri is universal
BODY_FONT    = "Calibri"
CODE_FONT    = "Consolas"

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "theme"


def create_reference_docx():
    """Generate reference.docx for Pandoc."""
    doc = Document()
    
    # ─── Page Setup: A4, binding margin ──────────────────────────────
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(3.0)    # Binding margin
        section.right_margin = Cm(2.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.5)
        section.header_distance = Cm(1.0)
        section.footer_distance = Cm(1.0)
    
    # ─── Style: Normal (Body Text) ──────────────────────────────────
    style = doc.styles['Normal']
    font = style.font
    font.name = BODY_FONT
    font.size = Pt(11)
    font.color.rgb = BODY_TEXT
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.5
    
    # ─── Style: Heading 1 ───────────────────────────────────────────
    h1 = doc.styles['Heading 1']
    h1.font.name = HEADING_FONT
    h1.font.size = Pt(24)
    h1.font.bold = True
    h1.font.color.rgb = NAVY
    h1.paragraph_format.space_before = Pt(24)
    h1.paragraph_format.space_after = Pt(12)
    h1.paragraph_format.keep_with_next = True
    h1.paragraph_format.page_break_before = True
    
    # ─── Style: Heading 2 ───────────────────────────────────────────
    h2 = doc.styles['Heading 2']
    h2.font.name = HEADING_FONT
    h2.font.size = Pt(17)
    h2.font.bold = True
    h2.font.color.rgb = INDIGO_600
    h2.paragraph_format.space_before = Pt(18)
    h2.paragraph_format.space_after = Pt(8)
    h2.paragraph_format.keep_with_next = True
    
    # ─── Style: Heading 3 ───────────────────────────────────────────
    h3 = doc.styles['Heading 3']
    h3.font.name = HEADING_FONT
    h3.font.size = Pt(13)
    h3.font.bold = True
    h3.font.color.rgb = NAVY
    h3.paragraph_format.space_before = Pt(12)
    h3.paragraph_format.space_after = Pt(6)
    h3.paragraph_format.keep_with_next = True
    
    # ─── Style: Heading 4 ───────────────────────────────────────────
    h4 = doc.styles['Heading 4']
    h4.font.name = HEADING_FONT
    h4.font.size = Pt(11)
    h4.font.bold = True
    h4.font.color.rgb = INDIGO
    h4.paragraph_format.space_before = Pt(8)
    h4.paragraph_format.space_after = Pt(4)
    h4.paragraph_format.keep_with_next = True
    
    # ─── Style: Title ────────────────────────────────────────────────
    title_style = doc.styles['Title']
    title_style.font.name = HEADING_FONT
    title_style.font.size = Pt(28)
    title_style.font.bold = True
    title_style.font.color.rgb = NAVY
    title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # ─── Style: Subtitle ────────────────────────────────────────────
    subtitle = doc.styles['Subtitle']
    subtitle.font.name = HEADING_FONT
    subtitle.font.size = Pt(14)
    subtitle.font.bold = False
    subtitle.font.color.rgb = MUTED_TEXT
    subtitle.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # ─── Style: Code ────────────────────────────────────────────────
    # Pandoc uses "Source Code" and "Verbatim Char" styles
    for code_style_name in ['Body Text', 'Body Text 2']:
        try:
            cs = doc.styles[code_style_name]
            cs.font.name = CODE_FONT
            cs.font.size = Pt(9)
        except KeyError:
            pass
    
    # ─── Style: Table Grid ──────────────────────────────────────────
    try:
        tbl_style = doc.styles['Table Grid']
        tbl_style.font.size = Pt(10)
    except KeyError:
        pass
    
    # ─── Style: List Bullet / List Number ───────────────────────────
    for lst in ['List Bullet', 'List Number']:
        try:
            ls = doc.styles[lst]
            ls.font.name = BODY_FONT
            ls.font.size = Pt(11)
        except KeyError:
            pass
    
    # ─── Style: Caption ─────────────────────────────────────────────
    try:
        cap = doc.styles['Caption']
        cap.font.name = BODY_FONT
        cap.font.size = Pt(9)
        cap.font.italic = True
        cap.font.color.rgb = MUTED_TEXT
        cap.paragraph_format.space_before = Pt(4)
        cap.paragraph_format.space_after = Pt(8)
    except KeyError:
        pass
    
    # ─── Style: Header / Footer ─────────────────────────────────────
    try:
        hdr = doc.styles['Header']
        hdr.font.name = BODY_FONT
        hdr.font.size = Pt(8)
        hdr.font.color.rgb = MUTED_TEXT
    except KeyError:
        pass
    
    try:
        ftr = doc.styles['Footer']
        ftr.font.name = BODY_FONT
        ftr.font.size = Pt(8)
        ftr.font.color.rgb = MUTED_TEXT
    except KeyError:
        pass
    
    # Add a sample paragraph so Pandoc picks up the Normal style
    doc.add_paragraph("")
    
    # ─── Save ────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "reference.docx"
    doc.save(str(output_path))
    print(f"[OK] Created reference.docx at: {output_path}")
    return output_path


if __name__ == "__main__":
    create_reference_docx()
