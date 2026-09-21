---
title: "DrishtiX — Backend Document"
subtitle: "Document ID: DX-BED | Version 1.0"
author:
  - Tejas Gohil (Developer)
date: "September 2026"
subject: "Software Project Management"
keywords: ["DrishtiX", "Backend", "Python", "SQLAlchemy", "Services"]
---

\newpage

| Field | Detail |
|:------|:-------|
| **Document ID** | DX-BED |
| **Title** | DrishtiX — Backend Document |
| **Version** | 1.0 |
| **Date** | September 2026 |
| **Status** | Final |
| **Author(s)** | Tejas Gohil (Developer) |
| **Reviewer** | Prof. Tirup Parmar (Project Guide) |
| **Institution** | SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce |
| **Programme** | TY BSc IT, Semester V, 2026–27 |

## At a Glance

This document details the backend architecture, module implementation, API reference, database layer, AI/ML pipeline, security measures, and configuration of the DrishtiX system. The backend consists of 16 business services, 7 DAO repositories, 8 ORM entities, and 4 worker threads — totalling approximately 8,500 lines of Python across the `drishtix/` core package.

## Related Documents

| Document ID | Title | Relevance |
|:------------|:------|:----------|
| DX-SDD | System Design Document | Architecture decisions, requirements, use case model |
| DX-FED | Frontend Document | UI layer consuming backend services and signals |
| DX-TST | Testing Document | Test cases covering backend modules |
| DX-FPR | Final Project Report | Overall summary |

\newpage

# Role and Contribution Statement

Tejas Gohil served as the **Developer** for the DrishtiX project during Semester V (Academic Year 2026–27) at SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce.

**Responsibilities:**

- Implemented the core Python backend package (`drishtix/`) containing 16 business services
- Built the data access layer with 7 SQLAlchemy DAO repositories
- Designed and implemented the 8 ORM entity models with SQLAlchemy 2.0 declarative syntax
- Developed the 4 background worker threads (capture, recognition, ingestion, video)
- Implemented the AI/CV pipeline: face detection (YuNet), recognition (SFace/ArcFace), tracking (CSRT/KCF), liveness detection, and body Re-ID (OSNet)
- Built the alert coordination system with multi-frame confirmation and Telegram integration
- Implemented DPDP Act compliance features (erasure, retention, consent)
- Developed the PySide6 UI layer (6 views, 21 custom widgets) — see DX-FED for details
- Wrote utility modules for vector math, image conversion, model downloading, and audio playback

**Tools used:** Python 3.11+, PySide6, OpenCV, SQLAlchemy, pytest, Git, GitHub, Ruff linter.

**Timeline:** July–August 2026 (3 sprints, 6 weeks).

\newpage

# Overview and Tech Stack

## Backend Responsibilities

The DrishtiX backend handles all non-visual logic:

1. **Video acquisition** — frame capture from USB/RTSP cameras with buffering
2. **AI inference** — face detection, embedding extraction, quality filtering, liveness checks
3. **Gallery management** — in-memory vector matrix for sub-millisecond cosine matching
4. **Alert coordination** — multi-frame confirmation, cooldown, multi-channel dispatch
5. **Data persistence** — CRUD operations via SQLAlchemy ORM on SQLite/SQLCipher
6. **External integration** — FBI Wanted API ingestion, Telegram Bot API notifications
7. **Configuration** — Pydantic-validated settings with YAML and environment variable support
8. **Observability** — structured logging, system telemetry, audit trail

## Technology Stack

| Technology | Version | Purpose |
|:-----------|:--------|:--------|
| Python | 3.11+ (tested 3.14.2) | Runtime language |
| OpenCV (headless) | >= 4.9.0 | YuNet detection, SFace recognition, CSRT/KCF tracking |
| InsightFace + ONNX Runtime | >= 1.0.0 / >= 1.19.0 | ArcFace 512-D, OSNet body Re-ID |
| SQLAlchemy | >= 2.0.0 | ORM, session management, schema migrations |
| SQLite / SQLCipher | 3.x | Embedded database with optional encryption |
| Pydantic + pydantic-settings | >= 2.0.0 | Configuration validation |
| PyYAML | >= 6.0 | Config file parsing |
| NumPy | >= 1.24.0 | Vector maths, matrix operations |
| structlog | >= 23.0.0 | Structured logging |
| HTTPX | >= 0.24.0 | HTTP client |
| Matplotlib | >= 3.7.0 | Analytics charts |
| psutil | >= 5.9.0 | System telemetry |
| FastAPI + Uvicorn | >= 0.115.0 | Re-ID microservice |

\newpage

# Architecture

## Layer Architecture

The backend follows a 4-layer architecture:

| Layer | Package | Responsibility | Dependencies |
|:------|:--------|:--------------|:-------------|
| **Core** | `drishtix.core` | Config, constants, enums, signal bus, feature flags | None |
| **Data** | `drishtix.models`, `drishtix.dao` | ORM entities, repositories, session management | Core |
| **Service** | `drishtix.services` | Business logic, AI inference, alert coordination | Core, Data |
| **Workers** | `drishtix.workers` | Background thread management | Core, Service |

## Annotated Folder Tree

```
drishtix/                          # Core Python package
├── __init__.py                    # Package marker (version)
├── app.py                         # Application bootstrap & lifecycle (171 lines)
├── core/                          # Foundation layer
│   ├── config.py                  # Pydantic Settings schema (213 lines)
│   ├── constants.py               # Application-wide constants (82 lines)
│   ├── enums.py                   # Domain enumerations (81 lines)
│   ├── feature_flags.py           # Runtime feature gates (24 lines)
│   └── signals.py                 # Qt SignalBus singleton (88 lines)
├── dao/                           # Data Access Objects
│   ├── session.py                 # Engine & session context manager (110 lines)
│   ├── target_dao.py              # Target & image CRUD (164 lines)
│   ├── embedding_dao.py           # Embedding vector CRUD (127 lines)
│   ├── detection_log_dao.py       # Detection log queries (249 lines)
│   ├── camera_dao.py              # Camera source CRUD (83 lines)
│   ├── audit_dao.py               # Audit log insertion (46 lines)
│   └── config_dao.py              # App config key-value CRUD (70 lines)
├── models/                        # ORM Entity Definitions
│   ├── base.py                    # DeclarativeBase, engine factory, migrations (130 lines)
│   ├── target_registry.py         # TargetRegistry entity (77 lines)
│   ├── target_image.py            # TargetImage entity (56 lines)
│   ├── face_embedding.py          # FaceEmbedding entity (98 lines)
│   ├── consent_record.py          # ConsentRecord entity (85 lines)
│   ├── camera_source.py           # CameraSource entity (60 lines)
│   ├── detection_log.py           # DetectionLog entity (79 lines)
│   ├── audit_log.py               # AuditLog entity (40 lines)
│   └── app_config.py              # AppConfig entity (53 lines)
├── services/                      # Business Logic Services (16 modules)
│   ├── face_detection.py          # YuNet ONNX face detection (243 lines)
│   ├── face_recognition.py        # SFace 128-D embedding extraction (255 lines)
│   ├── insightface_service.py     # ArcFace 512-D embeddings (256 lines)
│   ├── gallery_manager.py         # Centroid matrix cosine search (271 lines)
│   ├── face_tracker.py            # CSRT/KCF spatial tracking (216 lines)
│   ├── reid_tracking.py           # OSNet body Re-ID + fusion (472 lines)
│   ├── liveness_service.py        # Anti-spoofing detection (226 lines)
│   ├── alert_service.py           # Multi-frame confirmation + dispatch (280 lines)
│   ├── telegram_service.py        # Telegram Bot API sender (106 lines)
│   ├── ingestion_service.py       # FBI Wanted API sync (313 lines)
│   ├── analytics_service.py       # KPI metrics aggregation (87 lines)
│   ├── occupancy_analytics.py     # Zone occupancy tracking (195 lines)
│   ├── export_service.py          # CSV forensic export (89 lines)
│   ├── erasure_service.py         # DPDP right-to-erasure (228 lines)
│   ├── retention_service.py       # Data retention purge (139 lines)
│   └── rtsp_source.py             # RTSP auto-reconnect (236 lines)
├── utils/                         # Utility Modules
│   ├── vector_math.py             # L2 norm, cosine distance (75 lines)
│   ├── image_utils.py             # Mat-to-QPixmap conversions (226 lines)
│   ├── model_downloader.py        # ONNX model verification (72 lines)
│   └── sound_player.py            # Thread-safe audio player (104 lines)
└── workers/                       # Background Thread Workers
    ├── video_thread.py            # Capture & inference loop (703 lines)
    ├── capture_worker.py          # QThread capture wrapper (14 lines)
    ├── recognition_worker.py      # Recognition dispatch (102 lines)
    └── ingestion_worker.py        # FBI ingestion background (190 lines)
```

## Request Lifecycle

A typical frame flows through the system as follows:

1. **CaptureWorker** starts `VideoThread` on a dedicated QThread
2. **VideoThread** producer loop acquires frames from camera at 30 FPS
3. Frames are pushed to a bounded `queue.Queue(maxsize=2)` — overflow is dropped
4. Consumer loop pulls frame, runs **YuNet** face detection (< 3 ms)
5. Detected faces pass through **quality gate** (blur, resolution checks)
6. Passing crops are dispatched to **RecognitionWorker** via `QThreadPool`
7. RecognitionWorker extracts **SFace** embedding (128-D vector)
8. **GalleryManager** performs matrix cosine similarity matching (< 0.5 ms)
9. If match found: **AlertService** checks multi-frame confirmation and cooldown
10. Confirmed alerts: persist to database, emit `alert_created` signal, play sound, send Telegram
11. `frame_ready` signal delivers annotated frame to UI for rendering

\newpage

# Module-by-Module Description

## Core Module (`drishtix.core`)

### config.py — Configuration Management

**Purpose:** Loads, validates, and provides typed access to all runtime settings.

**Key classes:**

- `Settings` — root Pydantic model aggregating all sections
- `AppSettings`, `CameraSettings`, `DetectionSettings`, `RecognitionSettings`, `AlertSettings`, `DatabaseSettings`, `TrackingSettings` — section models

**Mechanism:** Reads `config.yaml` at startup via PyYAML, validates all fields through Pydantic v2 field validators, supports runtime mutation via `validate_assignment=True`, and allows environment variable overrides with `DRISHTIX_` prefix.

```python
# Excerpt: Recognition settings with validated threshold
class RecognitionSettings(_StrictModel):
    engine: str = "sface"
    match_threshold: float = Field(default=0.58, ge=0.0, le=1.0)
    pool_size: int = Field(default=4, ge=1, le=16)
```

### signals.py — Signal Bus

**Purpose:** Centralised Qt signal bus for thread-safe cross-component communication.

**Signals defined (11 total):**

| Signal | Payload | Emitter | Consumer(s) |
|:-------|:--------|:--------|:------------|
| `frame_ready` | QPixmap, list | VideoThread | VideoLabel, DashboardView |
| `camera_status_changed` | bool | CaptureWorker | StatusBar |
| `fps_updated` | float | VideoThread | StatusBar |
| `match_found` | dict | RecognitionWorker | AlertSidebar, MainWindow |
| `recognition_error` | str | RecognitionWorker | StatusBar |
| `alert_created` | dict | AlertService | AlertSidebar |
| `alert_cleared` | — | User action | AlertSidebar |
| `targets_changed` | — | TargetDAO operations | RegistryView, GalleryManager |
| `gallery_reloaded` | int (count) | GalleryManager | StatusBar |
| `db_status_changed` | bool | Session manager | StatusBar |
| `config_changed` | str, object | SettingsView | Various services |
| `memory_updated` | float (MB) | StatusBar timer | StatusBar |

## Service Layer (`drishtix.services`)

### FaceDetectionService — YuNet ONNX Face Detection

**Purpose:** Wraps the OpenCV DNN YuNet model for real-time multi-face detection.

**Key operations:**

- `detect(frame)` — returns list of `FaceDetection` objects with bounding box, landmarks, and confidence score
- Configurable thresholds: `score_threshold` (default 0.65), `nms_threshold` (default 0.3)
- Model: `face_detection_yunet_2023mar.onnx` (236 KB)

**Performance:** < 3 ms per 720p frame on CPU.

### FaceRecognitionService — SFace 128-D Embedding Extraction

**Purpose:** Extracts normalised 128-dimensional face embeddings from aligned 112×112 face crops.

**Key operations:**

- `extract_embedding(aligned_face)` — returns 128-D float32 NumPy vector
- Embedding is L2-normalised for cosine similarity computation
- Model: `face_recognition_sface_2021dec.onnx` (36.6 MB)

### GalleryManager — In-Memory Vector Search

**Purpose:** Maintains all active target embeddings in a contiguous NumPy matrix for sub-millisecond matching.

**Key operations:**

- `reload_gallery()` — rebuilds the (N, D) matrix from database; computes centroid templates for multi-photo targets
- `match_embedding(query_vector)` — performs `np.dot(matrix, query)` for batch cosine similarity; returns `MatchResult` if above threshold
- Thread safety: atomic swap pattern protected by GIL

**Performance:** < 0.5 ms for 10,000 targets.

```python
# Excerpt: Centroid template averaging
centroid = np.mean(vectors, axis=0)
centroid /= np.linalg.norm(centroid)  # L2 normalise
```

### AlertService — Multi-Frame Confirmation and Dispatch

**Purpose:** Coordinates alert generation with false-positive suppression.

**Multi-frame confirmation (Business Rule BR-02):**

- A target must achieve >= 2 positive cosine matches within a 5-second sliding window
- Only after confirmation: snapshot saved, database record created, sound played, Telegram dispatched
- Cooldown (BR-03): subsequent alerts for the same target suppressed for 30 seconds (configurable)

**Dispatch channels:**

1. `alert_created` signal → AlertSidebar adds AlertCard
2. `SoundPlayer.play()` → category-specific audio (alarm for Criminal, chime for Missing Person)
3. `TelegramService.send_alert()` → async HTTP POST with snapshot image

### IngestionService — FBI Wanted API Synchronisation

**Purpose:** Automatically ingests fugitive and missing person records from the FBI Wanted API.

**Workflow:**

1. HTTP GET to `https://api.fbi.gov/wanted/v1/list` (paginated)
2. Parse JSON response for each wanted person record
3. Check for duplicate case numbers in local database
4. Download mugshot image from FBI CDN
5. Run face detection + embedding extraction on mugshot
6. Persist TargetRegistry, TargetImage, FaceEmbedding, and ConsentRecord (legal_basis=LAW_ENFORCEMENT)
7. Log TARGET_CREATED in audit trail

**Configuration:** Runs every 60 minutes via `IngestionWorker` QThread, max 100 items per sync.

### ErasureService — DPDP Act Right-to-Erasure

**Purpose:** Implements the multi-layer cascade deletion required by Section 8(9) of the Digital Personal Data Protection Act, 2023.

**Erasure cascade:**

1. SQL CASCADE delete: `target_registry` → `target_image` → `face_embedding` → `detection_log` → `consent_record`
2. Filesystem: delete all snapshot images (`data/snapshots/`)
3. Filesystem: delete profile image file
4. Memory: purge from `GalleryManager` in-memory matrix
5. Rebuild: reload gallery to update matching matrix
6. Receipt: generate timestamped `ErasureReceipt` with items deleted
7. Audit: log `DATA_ERASURE` action

### LivenessService — Passive Anti-Spoofing

**Purpose:** Detects presentation attacks (printed photos, screen replay) without requiring active user cooperation.

**Three-factor check:**

| Factor | Weight | Technique | Detection |
|:-------|:-------|:----------|:----------|
| Texture | 40% | Local Binary Pattern (LBP) histogram variance | Printed photos show lower LBP variance |
| Chrominance | 30% | YCbCr colour space standard deviation | Screen replays show different colour distribution |
| Frequency | 30% | 2D FFT high-frequency moiré energy ratio | Printed/screen surfaces produce moiré patterns |

**Output:** Unified liveness score (0.0–1.0) computed in < 5 ms on CPU.

## Data Access Layer (`drishtix.dao`)

### Session Management (`session.py`)

**Purpose:** Provides SQLAlchemy engine creation and session context management.

**Key functions:**

- `initialize(db_path, encryption_key=None)` — creates engine with SQLite pragmas (WAL, foreign keys, busy timeout)
- `get_session()` — context manager yielding a transactional session
- `shutdown()` — disposes the engine connection pool

**SQLite Pragmas applied on connection:**

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
-- Optional: PRAGMA key = '<encryption_key>';  (SQLCipher)
```

### TargetDAO

**Key operations:** `create_target()`, `get_target_by_id()`, `get_all_targets()`, `update_target()`, `delete_target()`, `add_target_image()`, `get_target_images()`.

### EmbeddingDAO

**Key operations:** `save_embedding()`, `get_embeddings_for_target()`, `get_all_active_embeddings()` (used by GalleryManager), `delete_embeddings_for_target()`.

### DetectionLogDAO

**Key operations:** `create_log()`, `get_logs_paginated()`, `get_logs_by_date_range()`, `get_daily_trends()`, `get_hourly_distribution()`, `get_category_breakdown()`, `get_top_targets()`, `get_confidence_distribution()`.

This is the largest DAO (249 lines) due to the analytics aggregation queries.

## Worker Threads (`drishtix.workers`)

### VideoThread — Capture and Inference Loop

**Purpose:** The core processing loop handling frame acquisition, face detection, tracking, and recognition dispatch.

**Size:** 703 lines — the largest single module in the codebase.

**Key responsibilities:**

1. Producer loop: acquires frames from camera/RTSP at target FPS
2. Bounded queue (maxsize=2): prevents memory growth during slow inference
3. Consumer loop: YuNet face detection → quality gate → CSRT tracking
4. Adaptive frame skipping: PID controller targeting < 200 ms processing budget
5. Recognition dispatch: sends 112×112 crops (not full frames) to QThreadPool
6. Signal emission: `frame_ready`, `faces_detected`, `fps_updated`

**Performance optimisation:** Crops dispatched to recognition are 37 KB (112×112×3) instead of 2.76 MB (1280×720×3), eliminating unnecessary heap memory copying.

### IngestionWorker

**Purpose:** Background QThread running FBI Wanted API synchronisation on a timer.

**Mechanism:** Sleeps for `interval_minutes` between cycles; calls `IngestionService.sync()` on each iteration; emits `targets_changed` signal when new targets are ingested.

\newpage

# API Reference — Re-ID Microservice

The standalone Re-ID microservice (`services/reid-service/`) exposes 3 REST endpoints:

| Method | Path | Auth | Purpose |
|:-------|:-----|:-----|:--------|
| GET | `/health` | None | Service health check |
| POST | `/extract` | None | Extract 512-D body embedding |
| POST | `/match` | None | Match query against gallery |

## GET /health

**Response (200 OK):**

```json
{
  "status": "ok",
  "device": "cpu",
  "model_loaded": true
}
```

## POST /extract

**Request:** Multipart form with `file` (image upload)

**Response (200 OK):**

```json
{
  "embedding": [0.0234, -0.0156, ...],
  "dim": 512,
  "execution_time_ms": 12.4
}
```

**Error (400):** No person detected in image.

## POST /match

**Request body:**

```json
{
  "query_embedding": [0.0234, ...],
  "gallery": {
    "person_1": [0.0456, ...],
    "person_2": [0.0789, ...]
  },
  "threshold": 0.6
}
```

**Response (200 OK):**

```json
{
  "matches": [
    {"id": "person_1", "similarity": 0.82}
  ],
  "best_match": "person_1",
  "similarity": 0.82
}
```

\newpage

# Database Implementation

## Schema

The database uses 8 tables as defined in DX-SDD §6. The schema is created automatically at startup via `SQLAlchemy.metadata.create_all()`. Dynamic migrations for new columns are handled by `init_database()` which inspects existing tables and applies `ALTER TABLE ADD COLUMN` for backward-compatible upgrades.

## ORM Models

All models use SQLAlchemy 2.0 declarative syntax with `DeclarativeBase`:

```python
class TargetRegistry(Base):
    __tablename__ = "target_registry"
    target_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # ... relationships with cascade delete-orphan
    images: Mapped[List["TargetImage"]] = relationship(cascade="all, delete-orphan")
    embeddings: Mapped[List["FaceEmbedding"]] = relationship(cascade="all, delete-orphan")
```

## FaceEmbedding BLOB Serialisation

Embeddings are stored as raw `float32` BLOB data:

```python
# Serialise: numpy array → bytes
blob = embedding_vector.astype(np.float32).tobytes()

# Deserialise: bytes → numpy array
vector = np.frombuffer(blob, dtype=np.float32)
```

128-D SFace vectors occupy 512 bytes; 512-D ArcFace vectors occupy 2,048 bytes.

\newpage

# Authentication, Authorisation, and Security

DrishtiX operates as a single-user desktop application. See DX-SDD §7 for the complete security analysis including STRIDE threat model and OWASP Top 10 mapping.

**Key security measures:**

| Measure | Implementation |
|:--------|:--------------|
| SQL injection prevention | SQLAlchemy parameterised queries (no raw SQL) |
| Secret management | Telegram tokens and encryption keys in config.yaml / environment variables |
| Database encryption | Optional SQLCipher AES-256 via `PRAGMA key` |
| Data retention | Automated purge of expired records and snapshot files |
| Audit trail | Immutable audit_log table recording all administrative actions |
| Log sanitisation | structlog processors prevent token/key logging |
| Input validation | Pydantic field validators with type coercion and range constraints |

\newpage

# Configuration and Environment

## Environment Variables

| Variable | Purpose | Default |
|:---------|:--------|:--------|
| `DRISHTIX_APP__LOG_LEVEL` | Logging severity | INFO |
| `DRISHTIX_CAMERA__SOURCE` | Camera device index or RTSP URL | 0 |
| `DRISHTIX_DETECTION__SCORE_THRESHOLD` | YuNet confidence cutoff | 0.65 |
| `DRISHTIX_RECOGNITION__ENGINE` | Recognition backend (sface / insightface) | sface |
| `DRISHTIX_RECOGNITION__MATCH_THRESHOLD` | Cosine similarity threshold | 0.58 |
| `DRISHTIX_ALERTS__TELEGRAM_ENABLED` | Enable Telegram dispatch | false |
| `DRISHTIX_ALERTS__TELEGRAM_BOT_TOKEN` | Telegram Bot API token | (empty) |
| `DRISHTIX_ALERTS__TELEGRAM_CHAT_ID` | Telegram target chat ID | (empty) |
| `DRISHTIX_DATABASE__PATH` | SQLite database file path | data/drishtix.db |
| `DRISHTIX_DATABASE__ENCRYPTION_KEY` | SQLCipher passphrase | (empty) |
| `DRISHTIX_ENABLE_BENTO_UI` | Feature flag for bento grid layout | true |
| `LOG_FORMAT` | Logging output (json / console) | console |

## Setup and Run

```bash
cd services/drishtix-py
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python main.py
```

Or use the one-click launcher: `start_drishtix_py.bat`

\newpage

# Performance and Known Limitations

## Performance Benchmarks

| Operation | Measured Latency | Conditions |
|:----------|:----------------|:-----------|
| YuNet face detection | < 3 ms | 720p frame, CPU |
| SFace embedding extraction | ~ 5 ms | 112×112 crop, CPU |
| Gallery cosine matching | < 0.5 ms | 1,000 targets |
| End-to-end detection-to-alert | < 200 ms | Including multi-frame confirmation |
| Frame throughput | 25–30 FPS | 720p with inference every frame |

## Known Limitations

1. Single camera stream processing at a time
2. SQLite single-writer concurrency (WAL mode mitigates)
3. No CI/CD pipeline for automated testing
4. `evaluate_bias.py` is a stub requiring live recogniser wiring
5. Re-ID microservice (`reid-service/`) exists alongside embedded `DnnBodyReIdService` — redundant

\newpage

# Challenges and Solutions

| Challenge | Solution | Evidence |
|:----------|:---------|:---------|
| Java→Python migration | Complete architectural rewrite preserving all features; Python's richer CV/ML ecosystem justified the effort | Commits `306e6b7` through `b2d42aa` (2026-08-25 to 2026-08-29) |
| UI freezing during inference | Decoupled capture, detection, and recognition into separate QThread workers with bounded queues | `video_thread.py` producer-consumer pattern |
| False positive alerts | Multi-frame confirmation gate requiring N >= 2 matches within 5 seconds | `alert_service.py` lines 49–51 |
| Memory growth from frame buffering | Bounded queue (maxsize=2) with drop-oldest policy; crop-only dispatch (37 KB vs 2.76 MB) | `video_thread.py` line 69, `recognition_worker.py` |
| Gallery rebuild thread safety | Atomic swap pattern: build new state in locals, then reassign attributes in one statement (GIL-protected) | `gallery_manager.py` lines 110–185 |
| Body tracker instability | Migrated from CSRT to KCF for body tracking to prevent camera lag on target turn | Commits `9c79e64`, `3cd4452` (2026-08-02) |

\newpage

# Appendices

## Appendix A: Dependency List

| Package | Version Spec | Licence | Purpose |
|:--------|:------------|:--------|:--------|
| PySide6 | >= 6.5.0 | LGPL v3 | Qt6 GUI framework |
| opencv-python-headless | >= 4.9.0 | Apache 2.0 | Computer vision |
| sqlalchemy | >= 2.0.0 | MIT | ORM |
| pydantic | >= 2.0.0 | MIT | Configuration validation |
| pydantic-settings | >= 2.0.0 | MIT | Settings management |
| pyyaml | >= 6.0 | MIT | YAML parsing |
| numpy | >= 1.24.0 | BSD | Numerical computing |
| structlog | >= 23.0.0 | Apache 2.0 | Structured logging |
| httpx | >= 0.24.0 | BSD | HTTP client |
| psutil | >= 5.9.0 | BSD | System monitoring |
| matplotlib | >= 3.7.0 | PSF-based | Chart rendering |
| insightface | >= 1.0.0 | MIT | Face analysis models |
| onnxruntime | >= 1.19.0 | MIT | ONNX inference |
| pytest | >= 7.0 | MIT | Testing framework |
| jinja2 | >= 3.0 | BSD | Template rendering |
| pytest-qt | >= 4.2 | MIT | Qt testing plugin |
