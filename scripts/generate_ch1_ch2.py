"""
DrishtiX v3.0 — Chapter 1 & Chapter 2 DOCX Generator
=====================================================
Generates a professionally formatted Word document with Heading styles,
bold text, bullet points, and justified paragraph alignment.

Run:  python generate_ch1_ch2.py
Output: docs/DrishtiX_Chapter_1_2.docx
"""

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

# ═══════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "docs", "DrishtiX_Chapter_1_2.docx")

# ═══════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════

def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def style_table_header(table):
    """Dark header row, alternating body rows, light borders."""
    for cell in table.rows[0].cells:
        set_cell_shading(cell, "1A1A2E")
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(10)
                run.font.name = "Calibri"
    for i, row in enumerate(table.rows[1:], 1):
        bg = "F8F9FA" if i % 2 == 0 else "FFFFFF"
        for cell in row.cells:
            set_cell_shading(cell, bg)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
                    run.font.name = "Calibri"
    # Borders
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

def add_para(doc, text, bold=False, italic=False, size=Pt(11), alignment=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = size
    run.bold = bold
    run.italic = italic
    p.alignment = alignment
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    return p

def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.name = "Calibri"
        r.font.size = Pt(11)
        r2 = p.add_run(text)
        r2.font.name = "Calibri"
        r2.font.size = Pt(11)
    else:
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(11)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ci, h in enumerate(headers):
        table.rows[0].cells[ci].text = h
    for ri, row_data in enumerate(rows):
        for ci, val in enumerate(row_data):
            table.rows[ri + 1].cells[ci].text = str(val)
    style_table_header(table)
    doc.add_paragraph()  # spacing
    return table


# ═══════════════════════════════════════════════════
# DOCUMENT CREATION
# ═══════════════════════════════════════════════════

doc = Document()

# -- Page Setup --
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)

# -- Default Style --
style = doc.styles["Normal"]
font = style.font
font.name = "Calibri"
font.size = Pt(11)
font.color.rgb = RGBColor(0x33, 0x33, 0x33)

# -- Heading Styles --
for level, sz in [(1, 22), (2, 16), (3, 13), (4, 12)]:
    hs = doc.styles[f"Heading {level}"]
    hf = hs.font
    hf.name = "Calibri"
    hf.bold = True
    hf.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    hf.size = Pt(sz)
    hs.paragraph_format.space_before = Pt(18 if level <= 2 else 12)
    hs.paragraph_format.space_after = Pt(10 if level <= 2 else 6)


# ═══════════════════════════════════════════════════
# TITLE PAGE
# ═══════════════════════════════════════════════════

for _ in range(6):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("DrishtiX v3.0")
run.bold = True
run.font.size = Pt(36)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
run.font.name = "Calibri"

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = p2.add_run("Advanced Facial Recognition & Alert System")
run2.font.size = Pt(16)
run2.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
run2.font.name = "Calibri"

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
run3 = p3.add_run("Chapter 1: Introduction & Chapter 2: Survey of Technologies")
run3.font.size = Pt(14)
run3.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
run3.font.name = "Calibri"

for _ in range(4):
    doc.add_paragraph()

add_para(doc, "Project Code: DX-JVPD-2026", bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER)
add_para(doc, "Version: 3.0.0 (DNN Pipeline + Multi-Channel Push Engine + Background Ingestion)",
         alignment=WD_ALIGN_PARAGRAPH.CENTER)
add_para(doc, "August 2026", alignment=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_page_break()


# ═══════════════════════════════════════════════════
# CHAPTER 1: INTRODUCTION
# ═══════════════════════════════════════════════════

doc.add_heading("CHAPTER 1: INTRODUCTION", level=1)

# --- 1.1 Background ---
doc.add_heading("1.1 Background", level=2)

add_para(doc,
    "Traditional closed-circuit television (CCTV) infrastructure suffers from a fundamental "
    "design limitation: it produces video, not intelligence. In deployments across Indian "
    "police jurisdictions, surveillance operators are tasked with monitoring 16 to 64 camera "
    "feeds simultaneously, mentally cross-referencing each face against thousands of printed "
    "FIR photographs stored in unindexed binder volumes. Cognitive psychology research "
    "consistently demonstrates that human vigilance in sustained monitoring tasks degrades "
    "below 50% accuracy within the first 20 minutes.")

add_para(doc,
    "The consequence is a catastrophic latency gap. When a wanted criminal passes through a "
    "surveilled corridor, the identification \u2014 if it occurs at all \u2014 happens hours or days "
    "later during post-incident footage review. By that point, the individual has left the "
    "jurisdiction, the tactical advantage is lost, and the camera recording serves only as "
    "retrospective evidence, not as an operational tool for real-time interdiction.")

add_para(doc,
    "DrishtiX was conceived to eliminate this latency entirely. Rather than relying on human "
    "pattern-matching against a mental database of suspects, the system automates the entire "
    "surveillance-to-action pipeline using deep neural networks executing on commodity hardware. "
    "The transition is from passive recording to proactive edge AI: the camera itself becomes "
    "the first responder, raising alerts before the human operator has even registered the "
    "subject's presence.")

add_para(doc,
    "The system's architectural philosophy is rooted in the understanding that in law enforcement, "
    "the value of a detection decays exponentially with time. A match identified at t=200ms has "
    "immense tactical value; the same match at t=24h is merely an investigation data point. "
    "DrishtiX v3.0 delivers the former: from the instant a face appears in the camera's field "
    "of view to the instant a multi-channel alert reaches the field officer's phone, the total "
    "elapsed time is under 200 milliseconds \u2014 faster than the human blink reflex (300\u2013400ms).")


# --- 1.2 Objectives ---
doc.add_heading("1.2 Objectives", level=2)

add_para(doc, "The primary objectives of DrishtiX v3.0, derived directly from the implemented codebase, are:")

add_bullet(doc, " Achieve sub-200ms pixel-to-alert latency by decomposing "
    "the inference pipeline across dedicated thread pools: 2-thread VideoInference for frame "
    "capture and YuNet detection (~2ms), 4-thread RecognitionInference for SFace embedding "
    "extraction (~35ms), and 1-thread AudioAlert for non-blocking sound playback and I/O-bound "
    "Telegram/Email dispatch.", bold_prefix="Sub-Second Detection:")

add_bullet(doc, " Support up to DNN_MAX_FACES = 200 simultaneous face detections "
    "per frame via the YuNet FaceDetectorYN ONNX model, with 128-dimensional SFace embeddings "
    "matched against a ConcurrentHashMap gallery supporting 10,000+ registered targets.",
    bold_prefix="Multi-Target Throughput:")

add_bullet(doc, " Maintain persistent body-level tracking via KCF/CSRT "
    "trackers with OSNet x0.25 body embeddings (512-dimensional), allowing the system to "
    "continue monitoring a matched individual even after facial occlusion, through a "
    "configurable body lock expansion ratio of 2.5x with up to 1,800 frames (120 seconds "
    "at 15 FPS) of sustained tracking.", bold_prefix="Continuous Target Tracking:")

add_bullet(doc, " Deliver alerts through four independent, parallel "
    "channels \u2014 audio (javax.sound.sampled), desktop toast (ControlsFX Notifications), "
    "Telegram Bot API (HttpClient POST with multipart photo), and Email (SMTP via "
    "javax.mail) \u2014 each executing asynchronously via CompletableFuture on the "
    "AudioAlertPool to ensure no single channel failure blocks the others.",
    bold_prefix="Multi-Channel Alerting:")

add_bullet(doc, " Automatically ingest wanted person profiles from "
    "three external sources \u2014 FBI Wanted API (REST JSON), CBI Most Wanted (HTML scraping), "
    "and NCPCR TrackChild Missing Children (HTML scraping) \u2014 via a scheduled "
    "BackgroundIngestionEngine running on a dedicated 2-thread IngestionPool at "
    "MIN_PRIORITY, with configurable sync intervals (default: every 6 hours).",
    bold_prefix="Automated Watchlist Ingestion:")


# --- 1.3 Purpose, Scope, and Applicability ---
doc.add_heading("1.3 Purpose, Scope, and Applicability", level=2)

doc.add_heading("1.3.1 Purpose", level=3)

add_para(doc,
    "DrishtiX serves as a real-time, AI-powered surveillance force multiplier for environments "
    "where the delay between a target being visually present and an actionable alert being raised "
    "is operationally unacceptable. The system converts passive CCTV infrastructure into an "
    "active threat-detection mesh by replacing human visual pattern-matching with deep neural "
    "network inference executing at machine speed.")

add_para(doc,
    "The system is designed around a strict dashboard-centric philosophy: the operator must "
    "never leave the primary screen. The live camera feed occupies 70% of the viewport as "
    "the hero element, while detection alerts, target management, and configuration controls "
    "are accessible from the same unified interface. This eliminates the cognitive overhead "
    "of tab-switching during active surveillance operations, as implemented in the "
    "DashboardController.java (1,484 lines \u2014 the single largest class in the codebase).")

doc.add_heading("1.3.2 Scope", level=3)

add_para(doc, "DrishtiX v3.0 encompasses the following functional boundaries:")

add_bullet(doc, " YuNet DNN face detection (ONNX) with SFace DNN recognition (128-dim cosine similarity), "
    "falling back to Haar Cascade + LBPH when DNN models are unavailable.",
    bold_prefix="AI Pipeline: ")
add_bullet(doc, " MongoDB 6.0+ document store with 7 collections (targets, target_images, "
    "detection_logs, camera_sources, alert_config, audit_log, person_embeddings) plus a counters "
    "collection for auto-increment ID simulation.",
    bold_prefix="Data Layer: ")
add_bullet(doc, " JavaFX 21.0.2 with FXML (6 views: dashboard_view, registry_view, "
    "detection_log_view, settings_view, image_scan_view, main_view), premium dark CSS theme, "
    "ControlsFX toast notifications.",
    bold_prefix="UI Layer: ")
add_bullet(doc, " Audio + Desktop Toast + Telegram Bot + Email SMTP, "
    "orchestrated through AlertService with per-target cooldown via ConcurrentHashMap<Integer, Instant>.",
    bold_prefix="Alert Layer: ")
add_bullet(doc, " FBI API + CBI HTML + TrackChild HTML via "
    "BackgroundIngestionEngine on a 2-thread ScheduledExecutorService.",
    bold_prefix="Ingestion Layer: ")

doc.add_heading("1.3.3 Applicability", level=3)

add_para(doc, "DrishtiX is applicable to the following deployment scenarios:")

add_bullet(doc, "Law enforcement control rooms (police stations, crime branch offices)")
add_bullet(doc, "Campus security operations (universities, corporate campuses)")
add_bullet(doc, "Civic authority surveillance (municipal CCTV grids, transport hubs)")
add_bullet(doc, "Border checkpoints and immigration desks")
add_bullet(doc, "Hospital and critical infrastructure entry-point monitoring")

add_para(doc,
    "The system is explicitly not designed for covert mass surveillance. It operates against a "
    "defined watchlist; faces that do not match any registered target produce RecognitionResult"
    ".unknownDnn() and are immediately discarded with no data retention.")


# --- 1.4 Achievements ---
doc.add_heading("1.4 Achievements", level=2)

add_para(doc, "DrishtiX v3.0 represents the following verified technical achievements over the v1.0/v2.0 baseline:")

add_table(doc,
    ["Achievement", "v1.0/v2.0 Baseline", "v3.0 Implementation"],
    [
        ["Face Detection", "Haar Cascade (haarcascade_frontalface_alt2.xml), "
         "~15-30ms/frame, max ~5 faces", "YuNet DNN (face_detection_yunet_2023mar.onnx), "
         "~2ms/frame, DNN_MAX_FACES=200"],
        ["Face Recognition", "LBPH (distance-based, lower=better), "
         "requires full retrain on new target", "SFace DNN (face_recognition_sface_2021dec.onnx), "
         "128-dim cosine similarity, gallery injection without retrain"],
        ["Threading", "2-thread VideoInference + 1-thread AudioAlert", "5-pool architecture: "
         "2 VideoInference + 4 RecognitionInference + 1 AudioAlert + 2 Ingestion + 1 Scheduled"],
        ["Alert Channels", "Audio only (v1.0), Audio + Telegram (v2.0)", "4 channels: Audio + "
         "Desktop Toast + Telegram + Email, all async via CompletableFuture"],
        ["Body Tracking", "None", "KCF/CSRT tracker with OSNet x0.25 body embeddings, "
         "BODY_LOCK_MAX_FRAMES=1800 (120s continuous tracking)"],
        ["Watchlist Ingestion", "Manual upload only", "Automated 3-source sync: "
         "FBI API + CBI scraper + TrackChild scraper, every 6 hours"],
        ["Gallery Scalability", "~100 targets (LBPH retrain)", "10,000+ targets "
         "(ConcurrentHashMap + cosine similarity, ~2ms for 10K comparisons)"],
        ["Real-Time FPS", "~10 FPS (detection+recognition on same thread)",
         "15 FPS sustained (async recognition offloaded to 4-thread pool)"],
    ]
)


# --- 1.5 Organization of Report ---
doc.add_heading("1.5 Organization of Report", level=2)

add_para(doc, "This document is structured as follows:")

add_bullet(doc, " Establishes the problem domain, "
    "system objectives, scope boundaries, and key technical achievements of DrishtiX v3.0.",
    bold_prefix="Chapter 1 (Introduction): ")
add_bullet(doc, " Provides a deep technical "
    "analysis of each technology in the stack, explaining why it was chosen, how it is used "
    "in the codebase, and the specific concurrency and AI inference patterns employed.",
    bold_prefix="Chapter 2 (Survey of Technologies): ")


doc.add_page_break()


# ═══════════════════════════════════════════════════
# CHAPTER 2: SURVEY OF TECHNOLOGIES
# ═══════════════════════════════════════════════════

doc.add_heading("CHAPTER 2: SURVEY OF TECHNOLOGIES", level=1)

add_para(doc,
    "This chapter provides a repository-grounded analysis of every major technology in the "
    "DrishtiX v3.0 stack. Each subsection traces the technology's role to specific classes, "
    "methods, and configuration values found in the codebase. All version numbers are sourced "
    "from the project's pom.xml (Maven Project Object Model).")


# --- 2.1 Java 17+ & JavaFX 21+ ---
doc.add_heading("2.1 Java 17+ and JavaFX 21.0.2", level=2)

doc.add_heading("2.1.1 Language Runtime: Java 17 LTS", level=3)

add_para(doc,
    "DrishtiX targets Java 17 LTS as its minimum runtime, as declared in pom.xml via "
    "<java.version>17</java.version> and enforced by maven-compiler-plugin 3.12.1. Java 17 "
    "provides three capabilities critical to DrishtiX's architecture:")

add_bullet(doc, " The JVM module system (introduced in Java 9, stabilized "
    "by Java 17) enables ControlsFX 11.2.1 to access internal JavaFX APIs for sliding toast "
    "notifications. The application requires --add-opens flags for javafx.controls and "
    "javafx.graphics packages, as documented in DrishtiXLauncher.java.",
    bold_prefix="Module System: ")
add_bullet(doc, " java.util.concurrent.CompletableFuture "
    "(enhanced in Java 9+) is the primary mechanism for the asynchronous handoff between the "
    "VideoInference pool and the RecognitionInference pool. The DashboardController uses "
    "CompletableFuture.supplyAsync() to dispatch SFace embedding extraction to the 4-thread "
    "pool, then .thenAcceptAsync() to handle the recognition result back on the video thread.",
    bold_prefix="CompletableFuture API: ")
add_bullet(doc, " java.net.http.HttpClient (Java 11+) is used by "
    "TelegramAlertService for asynchronous HTTP POST requests to the Telegram Bot API, and "
    "by FbiWantedApiClient for REST polling of the FBI Wanted API at api.fbi.gov/wanted/v1/list.",
    bold_prefix="HTTP Client: ")

doc.add_heading("2.1.2 UI Framework: JavaFX 21.0.2", level=3)

add_para(doc,
    "JavaFX 21.0.2 (declared as <javafx.version>21.0.2</javafx.version> in pom.xml) provides "
    "the desktop GUI framework. The application uses four JavaFX modules: javafx-controls, "
    "javafx-fxml, javafx-graphics, and javafx-media.")

add_para(doc, "The FXML-Controller binding architecture comprises 6 views and 6 controllers:", bold=True)

add_table(doc,
    ["FXML View", "Controller", "Lines", "Responsibility"],
    [
        ["dashboard_view.fxml", "DashboardController", "1,484", "Hero screen: live feed, alert queue, stats, quick-add"],
        ["registry_view.fxml", "RegistryController", "~650", "Target CRUD: TableView, FileChooser, multi-photo upload"],
        ["detection_log_view.fxml", "DetectionLogController", "~500", "Historical logs: search, filter, CSV export"],
        ["settings_view.fxml", "SettingsController", "~200", "Configuration: thresholds, toggles, Telegram/Email setup"],
        ["image_scan_view.fxml", "ImageScanController", "~200", "Static CCTV image analysis and annotation"],
        ["main_view.fxml", "MainController", "~120", "TabPane navigation between views"],
    ]
)

add_para(doc, "Critical JavaFX Patterns in the Codebase:", bold=True)

add_bullet(doc, " All four dashboard metrics (Total Targets, "
    "Criminals, Missing Persons, Detections Today) are backed by SimpleIntegerProperty instances. "
    "The labels are bound via lblTotalTargets.textProperty().bind(totalTargetsProperty.asString()), "
    "ensuring automatic UI updates when any property value changes.",
    bold_prefix="IntegerProperty Binding: ")
add_bullet(doc, " Every scene graph modification from a background "
    "thread (alert card injection, ImageView updates, stat counter refreshes) is wrapped in "
    "Platform.runLater(() -> { ... }). This is enforced because JavaFX is single-threaded; "
    "any modification from a non-FX thread throws IllegalStateException.",
    bold_prefix="Platform.runLater(): ")
add_bullet(doc, " The alert queue (alertQueueBox, a VBox) enforces "
    "MAX_ALERT_QUEUE_SIZE = 50. When a new alert card (HBox) is prepended at index 0, the oldest "
    "card at the bottom is automatically removed if the size exceeds 50, preventing unbounded "
    "scene graph growth and maintaining layout performance within the 16ms frame budget.",
    bold_prefix="Alert Queue Memory Cap: ")


# --- 2.2 OpenCV, YuNet, and SFace ---
doc.add_heading("2.2 OpenCV 4.9.0, YuNet, and SFace", level=2)

doc.add_heading("2.2.1 OpenCV via JavaCV 1.5.10", level=3)

add_para(doc,
    "OpenCV 4.9.0 is accessed through the JavaCV 1.5.10 bridge layer (declared as "
    "<javacv.version>1.5.10</javacv.version> and <opencv.version>4.9.0-1.5.10</opencv.version> "
    "in pom.xml). JavaCV provides Java bindings to the native OpenCV C++ library via "
    "Bytedeco's JavaCPP presets. The critical OpenCV modules used are:")

add_bullet(doc, " FaceDetectorYN (YuNet ONNX model) for multi-face detection",
    bold_prefix="opencv_objdetect: ")
add_bullet(doc, " FaceRecognizerSF (SFace ONNX model) for embedding extraction",
    bold_prefix="opencv_objdetect: ")
add_bullet(doc, " CascadeClassifier (Haar Cascade XML) for legacy fallback",
    bold_prefix="opencv_objdetect: ")
add_bullet(doc, " LBPHFaceRecognizer for legacy histogram-based recognition",
    bold_prefix="opencv_face: ")
add_bullet(doc, " TrackerKCF and TrackerCSRT for body-level tracking",
    bold_prefix="opencv_tracking: ")

doc.add_heading("2.2.2 YuNet Face Detection (DnnFaceDetectionService)", level=3)

add_para(doc,
    "YuNet is a single-shot, anchor-free deep learning face detector loaded from the ONNX "
    "model file face_detection_yunet_2023mar.onnx (~260KB). The DnnFaceDetectionService class "
    "wraps OpenCV's FaceDetectorYN API.")

add_para(doc, "Each detection produces a 15-value output row:", bold=True)

add_table(doc,
    ["Values", "Meaning", "Usage in FaceDetection.java"],
    [
        ["[0..3]: x, y, w, h", "Bounding box (top-left origin)", "new Rect(x, y, w, h)"],
        ["[4..5]: x_re, y_re", "Right eye landmark", "landmarks[0] = {x_re, y_re}"],
        ["[6..7]: x_le, y_le", "Left eye landmark", "landmarks[1] = {x_le, y_le}"],
        ["[8..9]: x_nt, y_nt", "Nose tip landmark", "landmarks[2] = {x_nt, y_nt}"],
        ["[10..11]: x_rm, y_rm", "Right mouth corner", "landmarks[3] = {x_rm, y_rm}"],
        ["[12..13]: x_lm, y_lm", "Left mouth corner", "landmarks[4] = {x_lm, y_lm}"],
        ["[14]: score", "Detection confidence (0.0-1.0)", "detectionScore (threshold: 0.35)"],
    ]
)

add_para(doc,
    "The detector is configured with DEFAULT_DNN_SCORE_THRESHOLD = 0.35 (optimized for "
    "crowd-density scenarios at Zone 1 college corridors), DEFAULT_DNN_NMS_THRESHOLD = 0.3 "
    "for non-maximum suppression, and DNN_MAX_FACES = 200 to handle extreme crowd surges "
    "during college festivals.")

doc.add_heading("2.2.3 SFace Recognition (DnnFaceRecognitionService)", level=3)

add_para(doc,
    "SFace (ShuffleFace) is a deep metric learning model that extracts 128-dimensional "
    "embedding vectors based on facial geometry. The DnnFaceRecognitionService loads "
    "face_recognition_sface_2021dec.onnx (~37MB) and wraps FaceRecognizerSF.")

add_para(doc, "The SFace pipeline operates in three stages:", bold=True)

add_bullet(doc, " The face region from YuNet is cropped and resized "
    "to the canonical 112x112 BGR input size required by SFace, using the 5-point landmarks "
    "for alignment (FaceProcessingService.alignFaceForDnn()).",
    bold_prefix="Stage 1 - Alignment: ")
add_bullet(doc, " FaceRecognizerSF.feature(alignedFace, featureMat) "
    "extracts an L2-normalized 128-dimensional float array. The FaceRecognizerSF instance is "
    "stored in a ThreadLocal<FaceRecognizerSF> to enable safe parallel execution across the "
    "4-thread RecognitionInferencePool.",
    bold_prefix="Stage 2 - Embedding Extraction: ")
add_bullet(doc, " The probe embedding is compared against every "
    "entry in the ConcurrentHashMap<Integer, TargetEmbeddings> gallery using cosine similarity. "
    "A match is declared when similarity >= DEFAULT_DNN_COSINE_THRESHOLD = 0.363 (SFace's "
    "recommended threshold). Gallery reads acquire galleryLock.readLock(); gallery rebuilds "
    "acquire galleryLock.writeLock().",
    bold_prefix="Stage 3 - Gallery Matching: ")

add_para(doc, "The cosine similarity computation (VectorMathUtil.cosineSimilarity):", bold=True)
add_para(doc,
    "cos(A, B) = (A . B) / (||A|| * ||B||), where A and B are 128-dimensional float arrays. "
    "The dot product and magnitudes are computed in a single loop for cache efficiency. The "
    "result ranges from -1.0 (opposite) to 1.0 (identical), with the match threshold at 0.363.",
    italic=True)


# --- 2.3 MongoDB & Connection Management ---
doc.add_heading("2.3 MongoDB 6.0+ and Connection Management", level=2)

add_para(doc,
    "DrishtiX v3.0 uses MongoDB as its primary data store, accessed through the MongoDB "
    "Java Sync Driver 5.1.0 (declared as <mongodb.version>5.1.0</mongodb.version> in pom.xml). "
    "The original codebase included MySQL schema definitions (drishtix_schema.sql) as a "
    "reference, but the runtime data layer is built entirely on MongoDB.")

doc.add_heading("2.3.1 Connection Management: DatabaseManager Singleton", level=3)

add_para(doc,
    "The DatabaseManager class implements a thread-safe singleton pattern using double-checked "
    "locking with a volatile instance field. It reads db.uri and db.name from config.properties "
    "(default: mongodb://localhost:27017 / drishtix_db). The connection is validated at startup "
    "via a ping command: database.runCommand(new Document('ping', 1)).")

add_para(doc, "Key methods:", bold=True)

add_bullet(doc, " Returns a typed MongoCollection<Document> "
    "from the database instance. Throws IllegalStateException if the database is not initialized.",
    bold_prefix="getCollection(String name): ")
add_bullet(doc, " Atomically increments and returns the next "
    "integer ID from the 'counters' collection using findOneAndUpdate with $inc operator and "
    "upsert:true. This simulates relational auto-increment IDs in MongoDB.",
    bold_prefix="getNextSequence(String name): ")
add_bullet(doc, " Wipes all operational data (targets, target_images, "
    "detection_logs, audit_log) and resets counter sequences to 0. Preserves camera_sources and "
    "alert_config. Protected by explicit log.warn().",
    bold_prefix="clearSystemData(): ")

doc.add_heading("2.3.2 DAO Architecture", level=3)

add_para(doc,
    "The data access layer follows a pure DAO pattern without an ORM. Each DAO class directly "
    "constructs and parses BSON Documents:")

add_table(doc,
    ["DAO Class", "Collection", "Key Operations"],
    [
        ["TargetDAO", "targets", "insert, update, deactivate, delete, findById, "
         "findByRecognizerLabel, findAllActive, search(query, category), "
         "getNextRecognizerLabel, countByCategory"],
        ["TargetImageDAO", "target_images", "insert, findByTargetId, deleteByTargetId, "
         "countByTargetId"],
        ["DetectionLogDAO", "detection_logs", "insert, findByDateRange, findByTargetId, "
         "countToday, findRecent(limit)"],
        ["AlertConfigDAO", "alert_config", "findByKey, upsert, findAll"],
        ["AuditLogDAO", "audit_log", "insert (action_type, target_id, details)"],
        ["CameraSourceDAO", "camera_sources", "findAllActive, findById, insert"],
        ["PersonEmbeddingDAO", "person_embeddings", "insert, findRecent(limit), "
         "findByTargetId, deleteByTargetId"],
    ]
)


# --- 2.4 Threading & Concurrency ---
doc.add_heading("2.4 Threading and Concurrency Architecture", level=2)

add_para(doc,
    "DrishtiX v3.0 implements a 5-pool + 1 scheduled pool threading model, centrally managed "
    "by the ThreadPools utility class. Every pool uses daemon threads to ensure the JVM can "
    "exit cleanly even if tasks are hung. The architecture is designed to prevent any single "
    "operation from starving the others.")

add_table(doc,
    ["Pool", "Thread Name", "Threads", "Priority", "Responsibility"],
    [
        ["Pool 1", "JavaFX Application Thread", "1", "Normal", "UI rendering, Platform.runLater() "
         "callbacks, IntegerProperty binding, ControlsFX toast display"],
        ["Pool 2", "DrishtiX-VideoInference", "2", "Normal", "Frame capture (OpenCVFrameGrabber), "
         "YuNet face detection (~2ms), frame annotation, snapshot writes"],
        ["Pool 3", "DrishtiX-RecognitionInference", "4", "Normal", "SFace embedding extraction "
         "(ThreadLocal FaceRecognizerSF), cosine similarity gallery matching, gallery rebuild"],
        ["Pool 4", "DrishtiX-AudioAlert", "1", "Normal", "WAV playback (javax.sound.sampled), "
         "Telegram Bot API HTTP calls, Email SMTP dispatch"],
        ["Pool 5", "DrishtiX-Ingestion", "2", "MIN_PRIORITY", "Scheduled FBI/CBI/TrackChild sync, "
         "HTTP polling, HTML scraping, profile registration"],
        ["Pool 6", "DrishtiX-Scheduled", "1", "Normal", "Periodic snapshot cleanup, config refresh"],
    ]
)

doc.add_heading("2.4.1 The CompletableFuture Async Pipeline", level=3)

add_para(doc,
    "The critical innovation in v3.0 is the decoupling of face detection (fast, ~2ms) from "
    "face recognition (slow, ~35ms per face on CPU). In v1.0/v2.0, both ran synchronously on "
    "the same thread, capping the effective FPS at ~10. In v3.0, the DashboardController.processFrameDnn() "
    "method uses CompletableFuture to dispatch recognition to the 4-thread pool asynchronously:")

add_bullet(doc, " YuNet detection runs on the VideoInference thread. "
    "Takes ~2ms. Returns List<FaceDetection> with bounding boxes + 5-point landmarks.",
    bold_prefix="Step 1 (Capture Thread): ")
add_bullet(doc, " For each detected face, the aligned 112x112 BGR "
    "crop is cloned and dispatched via CompletableFuture.supplyAsync(() -> "
    "recognitionService.predictDnn(alignedCopy), ThreadPools.getRecognitionInferencePool()). "
    "The capture thread immediately draws 'Analyzing...' placeholder labels and pushes the "
    "annotated frame to the UI.",
    bold_prefix="Step 2 (Async Dispatch): ")
add_bullet(doc, " The .thenAcceptAsync() callback runs on the "
    "VideoInference pool, calling handleRecognitionResult() which triggers AlertService if a "
    "match is found. The cloned Mat is released in this callback to prevent memory leaks.",
    bold_prefix="Step 3 (Result Callback): ")

doc.add_heading("2.4.2 Thread Safety Mechanisms", level=3)

add_para(doc, "The codebase employs the following concurrency primitives:")

add_bullet(doc, " On the DnnFaceRecognitionService gallery "
    "(ConcurrentHashMap<Integer, TargetEmbeddings>). Multiple recognition threads acquire "
    "readLock() for concurrent gallery matching. Gallery rebuilds and embedding injections "
    "acquire writeLock(), blocking all readers during the update.",
    bold_prefix="ReentrantReadWriteLock: ")
add_bullet(doc, " The FaceRecognizerSF instance (an OpenCV native "
    "object that is NOT thread-safe) is stored in a ThreadLocal<FaceRecognizerSF> within "
    "DnnFaceRecognitionService. Each of the 4 recognition threads gets its own model instance, "
    "loaded lazily on first access. The pre-warming routine in ThreadPools.preWarmRecognitionPool() "
    "triggers all 4 ThreadLocal instances to initialize at startup, eliminating the ~200ms "
    "cold-start penalty.",
    bold_prefix="ThreadLocal<FaceRecognizerSF>: ")
add_bullet(doc, " cameraRunning (AtomicBoolean) guards the "
    "capture loop start/stop. globalFrameIndex (AtomicLong) counts total frames for the "
    "inference_frame_interval skip logic. currentThreshold (AtomicReference<Double>) holds "
    "the confidence slider value, updated from the FX thread and read from inference threads.",
    bold_prefix="AtomicBoolean / AtomicLong / AtomicReference: ")
add_bullet(doc, " AlertService.lastAlertTimes "
    "(ConcurrentHashMap<Integer, Instant>) tracks per-target cooldown state. The gallery "
    "itself is a ConcurrentHashMap<Integer, TargetEmbeddings>. BackgroundIngestionEngine"
    ".processedExternalIds uses ConcurrentHashMap.newKeySet() for thread-safe deduplication.",
    bold_prefix="ConcurrentHashMap: ")
add_bullet(doc, " All singleton services "
    "(DatabaseManager, DnnFaceDetectionService, DnnFaceRecognitionService, AlertService, "
    "ConfigurationService, BackgroundIngestionEngine) use the double-checked locking idiom "
    "with a volatile instance field to ensure safe lazy initialization across threads.",
    bold_prefix="volatile + Double-Checked Locking: ")

doc.add_heading("2.4.3 Graceful Shutdown Protocol", level=3)

add_para(doc,
    "On application exit, DrishtiXApp.shutdown() calls ThreadPools.shutdownAll(), which "
    "iterates over all 5 pools: (1) calls shutdown() to stop accepting new tasks, "
    "(2) awaitTermination(3, TimeUnit.SECONDS) for graceful completion, (3) if not terminated, "
    "calls shutdownNow() to interrupt running tasks. Since all threads are daemon threads, "
    "the JVM will force-exit regardless. After pool shutdown, DatabaseManager.getInstance()"
    ".shutdown() closes the MongoClient connection.")


# ═══════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
doc.save(OUTPUT_PATH)
print(f"Document saved: {OUTPUT_PATH}")
print(f"Size: {os.path.getsize(OUTPUT_PATH):,} bytes")
