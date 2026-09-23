---
title: "DrishtiX — System Design Document"
subtitle: "Document ID: DX-SDD | Version 1.0"
author:
  - Arjun Prajapati (System Designer)
date: "September 2026"
subject: "Software Project Management"
keywords: ["DrishtiX", "System Design", "UML", "Architecture", "Facial Recognition"]
---

\newpage

| Field | Detail |
|:------|:-------|
| **Document ID** | DX-SDD |
| **Title** | DrishtiX — System Design Document |
| **Version** | 1.0 |
| **Date** | September 2026 |
| **Status** | Final |
| **Author(s)** | Arjun Prajapati (System Designer) |
| **Reviewer** | Prof. Tirup Parmar (Project Guide) |
| **Institution** | SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce |
| **Programme** | TY BSc IT, Semester V, 2026–27 |
| **Subject** | Software Project Management |

## At a Glance

DrishtiX is an edge-deployed, real-time facial recognition desktop application built with Python 3.11+, PySide6 (Qt6), and OpenCV ONNX neural networks. It processes live video feeds, detects faces, extracts 128-D/512-D biometric embeddings, and matches them against a local watchlist of criminals and missing persons — triggering multi-channel tactical alerts within 200 ms.

**Key metrics:** 8 ORM entities | 16 business services | 6 UI screens | 21 custom widgets | 3 REST API endpoints | ~11,741 lines of Python | 51 commits | 8 test files

## Related Documents

| Document ID | Title | Relevance |
|:------------|:------|:----------|
| DX-BED | Backend Document | Module implementation details, API reference, database schema |
| DX-FED | Frontend Document | UI/UX design, screen walkthrough, component catalogue |
| DX-TST | Testing Document | Test cases, traceability matrix, defect log |
| DX-EVD | Evidence Pack | Jira, Discord, GitHub evidence, project timeline |
| DX-FPR | Final Project Report | Overall project summary across all documents |

\newpage

# Role and Contribution Statement

Arjun Prajapati served as the **System Designer** for the DrishtiX project during Semester V (Academic Year 2026–27) at SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce, under the guidance of Prof. Tirup Parmar.

**Responsibilities:**

- Defined the 5-tier concurrent pipeline architecture (Ingestion, AI Vision, Matching, Persistence, Presentation)
- Designed all 8 database entities and their relationships using SQLAlchemy 2.0 ORM declarative models
- Created the use case model identifying 2 primary actors, 2 external systems, and 15 use cases across 5 modules
- Produced the complete UML model suite: class diagrams (4), sequence diagrams (7), activity diagrams (4), state machine diagrams (3), component diagram, and deployment diagram
- Designed data flow diagrams at Levels 0, 1, and 2 using Yourdon–DeMarco notation
- Authored the data dictionary covering all data flows and stores
- Established the security model including DPDP Act 2023 compliance provisions (consent tracking, right-to-erasure, data retention)
- Documented 22 design decisions with rationale, alternatives considered, and consequences
- Built the requirements traceability matrix linking requirements to use cases, modules, and test cases

**Artefacts produced:** This document (DX-SDD) containing all architectural diagrams, specifications, and design records.

**Tools used:** Git, GitHub, Mermaid diagram notation, Python (analysis scripts).

**Timeline:** July–August 2026, across 3 development sprints (6 weeks total).

\newpage

# System Overview

## Purpose

DrishtiX transforms standard video surveillance feeds into proactive, automated security perimeters. Traditional CCTV systems rely on operators watching multiple screens simultaneously — a task where human performance degrades within 20 minutes due to cognitive fatigue. DrishtiX addresses this by deploying deep neural networks at the edge to continuously cross-reference live video feeds against a local watchlist, achieving sub-second identification without cloud dependency.

The system performs four core functions:

1. **Detection** — localises all visible faces in a live video stream using the YuNet ONNX model
2. **Recognition** — extracts 128-dimensional (SFace) or 512-dimensional (ArcFace) biometric embeddings and matches them against enrolled targets via cosine similarity
3. **Alerting** — triggers multi-channel tactical alerts (audio, desktop HUD, Telegram push notifications) when a confirmed match occurs
4. **Intelligence** — provides analytics dashboards, detection logs, forensic image scanning, and automated ingestion from external databases (FBI Wanted API)

## Scope

### In Scope

| Area | Description | Key Files |
|:-----|:------------|:----------|
| Real-time face detection | YuNet ONNX model, 5-point landmarks, quality gate | `face_detection.py` |
| Face recognition | SFace 128-D and ArcFace 512-D embeddings | `face_recognition.py`, `insightface_service.py` |
| Gallery matching | In-memory centroid matrix cosine search | `gallery_manager.py` |
| Spatial tracking | CSRT/KCF inter-frame face tracking | `face_tracker.py` |
| Body Re-ID | OSNet 512-D whole-body re-identification | `reid_tracking.py` |
| Anti-spoofing | Passive liveness detection (LBP, YCbCr, FFT) | `liveness_service.py` |
| Watchlist management | Target CRUD with multi-angle photo enrolment | `registry_view.py`, `target_dao.py` |
| Alert system | Multi-frame confirmation + audio/visual/Telegram | `alert_service.py`, `telegram_service.py` |
| FBI ingestion | Automated background sync from FBI Wanted API | `ingestion_service.py`, `ingestion_worker.py` |
| Forensic scanning | Batch static image recognition | `image_scan_view.py` |
| Analytics | KPI metrics, occupancy tracking, charts | `analytics_service.py`, `analytics_view.py` |
| Detection logging | Searchable event log with CSV export | `detection_log_view.py`, `export_service.py` |
| Data compliance | DPDP Act 2023 consent, erasure, retention | `erasure_service.py`, `retention_service.py`, `consent_record.py` |
| Settings | Runtime threshold tuning, camera config | `settings_view.py`, `config.py` |

### Out of Scope

| Area | Reason |
|:-----|:-------|
| Multi-camera grid multiplexer | Planned for future release |
| Deep SORT / ByteTrack tracking | Planned enhancement for cross-camera tracking |
| Docker containerisation | Planned for deployment standardisation |
| Cloud deployment | System designed for edge-only deployment |
| User authentication / RBAC | Desktop application without multi-user login |
| Mobile application | Desktop-only PySide6 interface |

## Stakeholders

| Stakeholder | Type | Interest |
|:------------|:-----|:---------|
| Security operator | Primary user | Monitors live feeds, manages targets, reviews alerts |
| System administrator | Primary user | Configures cameras, thresholds, retention policies |
| Law enforcement agencies | Beneficiary | Consume alerts and forensic reports |
| Data principals | Regulated subject | Individuals whose biometric data is processed |
| Academic evaluator | Assessor | Reviews system design for academic evaluation |

## Assumptions

1. The deployment machine has at least one connected USB webcam or accessible RTSP camera stream.
2. Python 3.11 or higher is installed on the target machine.
3. ONNX model weight files (YuNet, SFace) are available locally in the `models/` directory.
4. The operator has basic familiarity with surveillance monitoring workflows.
5. SQLite performance is adequate for the expected data volume (< 100,000 detection records).
6. Internet connectivity is optional; required only for FBI API synchronisation and Telegram alerts.

## Constraints

| Constraint | Impact | Mitigation |
|:-----------|:-------|:-----------|
| Edge hardware (CPU-only) | Inference must complete within 200 ms per frame | Adaptive frame skipping via PID controller |
| Single camera (current) | One active video stream at a time | Multi-camera support planned in roadmap |
| SQLite single-writer | Write contention under high-frequency logging | WAL mode with busy_timeout=5000 ms |
| Privacy regulations | DPDP Act 2023 compliance mandatory | Consent tracking, erasure workflows, retention policies |
| No GPU dependency | Cannot use CUDA-accelerated models | ONNX Runtime CPU backend sufficient for YuNet/SFace |

## Operating Environment

| Component | Specification |
|:----------|:-------------|
| Operating system | Windows 10/11, Linux, macOS |
| Python runtime | 3.11+ (tested on 3.14.2) |
| Camera input | USB webcam (device index 0) or RTSP/HTTP URL |
| Database | SQLite 3.x with optional SQLCipher AES-256 encryption |
| Network | Optional: FBI API sync requires internet; Telegram requires bot token |
| Memory | Minimum 4 GB RAM (8 GB recommended for InsightFace) |
| Disk | ~500 MB for models, snapshots, and database |

\newpage

# Requirements

## Functional Requirements

### Detection Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-DET-01 | The system shall detect all visible faces in a live video frame using the YuNet ONNX model with configurable confidence threshold (default 0.65) | Must | Implemented |
| FR-DET-02 | The system shall extract 5-point facial landmarks (eyes, nose, mouth corners) for each detected face | Must | Implemented |
| FR-DET-03 | The system shall apply a face quality gate rejecting crops with Laplacian blur variance < 50 or resolution < 40 px | Should | Implemented |
| FR-DET-04 | The system shall perform adaptive frame skipping based on processing latency to maintain UI responsiveness | Should | Implemented |
| FR-DET-05 | The system shall apply non-maximum suppression (NMS threshold 0.3) to eliminate duplicate detections | Must | Implemented |

### Recognition Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-REC-01 | The system shall extract 128-dimensional face embeddings using the SFace ONNX model | Must | Implemented |
| FR-REC-02 | The system shall support alternative 512-D embeddings via ArcFace/InsightFace engine | Should | Implemented |
| FR-REC-03 | The system shall match embeddings against the in-memory gallery matrix using cosine similarity | Must | Implemented |
| FR-REC-04 | The system shall support configurable match threshold (default 0.58 for SFace, 0.45 for ArcFace) | Should | Implemented |
| FR-REC-05 | The system shall compute centroid templates for targets with multiple enrolled photos | Should | Implemented |

### Target Management Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-TGT-01 | The system shall allow operators to enrol new targets with full name, category (Criminal/Missing Person), case number, and description | Must | Implemented |
| FR-TGT-02 | The system shall support multiple enrolled photographs per target for improved recognition accuracy | Should | Implemented |
| FR-TGT-03 | The system shall automatically extract and store facial embeddings upon photo upload | Must | Implemented |
| FR-TGT-04 | The system shall allow operators to deactivate (soft delete) targets without destroying data | Should | Implemented |
| FR-TGT-05 | The system shall display a searchable, filterable target registry with profile cards | Should | Implemented |

### Alerting Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-ALT-01 | The system shall trigger alerts only after multi-frame confirmation (N >= 2 hits within 5 seconds) | Must | Implemented |
| FR-ALT-02 | The system shall dispatch alerts concurrently via audio playback, desktop HUD card, and Telegram notification | Must | Implemented |
| FR-ALT-03 | The system shall enforce a configurable cooldown period (default 30 s) between repeated alerts for the same target | Should | Implemented |
| FR-ALT-04 | The system shall save a forensic snapshot image (face crop) for each confirmed alert | Must | Implemented |
| FR-ALT-05 | The system shall display alert cards in a sliding sidebar with target name, confidence, timestamp, and snapshot | Should | Implemented |

### Ingestion Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-ING-01 | The system shall automatically ingest fugitive and missing person records from the FBI Wanted API on a configurable schedule | Could | Implemented |
| FR-ING-02 | The system shall download mugshot images and extract embeddings for ingested targets | Could | Implemented |
| FR-ING-03 | The system shall log all ingestion events in the audit trail | Should | Implemented |

### Forensic Scanner Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-SCN-01 | The system shall allow batch forensic scanning of uploaded static images against the enrolled gallery | Should | Implemented |
| FR-SCN-02 | The system shall display all detected faces with match results and confidence scores | Should | Implemented |

### Analytics Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-ANL-01 | The system shall display total detections, unique targets, and detection rate as KPI metrics | Should | Implemented |
| FR-ANL-02 | The system shall render detection frequency charts and category breakdowns | Should | Implemented |
| FR-ANL-03 | The system shall track real-time zone occupancy using a sliding-window algorithm | Could | Implemented |

### Logging and Export Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-LOG-01 | The system shall maintain a searchable, date-filterable log of all detection events | Must | Implemented |
| FR-LOG-02 | The system shall display snapshot thumbnails in the detection log table | Should | Implemented |
| FR-EXP-01 | The system shall export detection logs as CSV files for forensic reporting | Could | Implemented |

### Compliance Module

| ID | Description | Priority | Status |
|:---|:-----------|:---------|:-------|
| FR-ERS-01 | The system shall support right-to-erasure cascade deletion per DPDP Act 2023 Section 8(9) | Must | Implemented |
| FR-ERS-02 | The system shall generate an auditable erasure receipt upon data deletion | Should | Implemented |
| FR-RET-01 | The system shall automatically purge detection logs and snapshot files exceeding the configured retention period (default 30 days) | Should | Implemented |
| FR-CON-01 | The system shall record consent/legal basis for each enrolled target in a consent_record table | Must | Implemented |

## Non-Functional Requirements

| ID | Description | Priority | Category | Status |
|:---|:-----------|:---------|:---------|:-------|
| NFR-01 | YuNet face detection shall complete within 5 ms per frame at 720p resolution | Must | Performance | Implemented |
| NFR-02 | End-to-end detection-to-alert latency shall not exceed 200 ms on CPU hardware | Must | Performance | Implemented |
| NFR-03 | The UI shall remain responsive during inference with no visible frame drops exceeding 100 ms | Must | Usability | Implemented |
| NFR-04 | Gallery matching shall complete in under 0.5 ms for up to 10,000 enrolled targets | Should | Performance | Implemented |
| NFR-05 | The database shall support optional AES-256 encryption at rest via SQLCipher | Should | Security | Implemented |
| NFR-06 | All administrative actions shall be logged in an immutable audit trail | Must | Compliance | Implemented |
| NFR-07 | The system shall run on Python 3.11+ without external GPU or CUDA dependencies | Must | Portability | Implemented |
| NFR-08 | Detection logs older than the configured retention period shall be automatically purged | Should | Compliance | Implemented |
| NFR-09 | Telegram bot tokens and database encryption keys shall never appear in logs or hardcoded values | Must | Security | Implemented |
| NFR-10 | The application shall use structured logging with correlation IDs for traceability | Should | Observability | Implemented |

## Business Rules

| Rule ID | Description | Enforcement Location |
|:--------|:-----------|:--------------------|
| BR-01 | A target must have at least one enrolled photo before it can appear in gallery matching | `target_dao.py`, `gallery_manager.py` |
| BR-02 | Multi-frame confirmation requires N >= 2 positive cosine matches within a 5-second sliding window before an alert fires | `alert_service.py` (lines 49–51) |
| BR-03 | Alert cooldown suppresses repeated alerts for the same target within the configured period (default 30 s) | `alert_service.py` (line 53) |
| BR-04 | Centroid template averaging is applied when a target has multiple enrolled photos | `gallery_manager.py` |
| BR-05 | Erasure cascade must delete the target, all images, all embeddings, all detection logs, remove from in-memory gallery, and delete snapshot files from disk | `erasure_service.py` |
| BR-06 | Consent records must specify a legal basis (CONSENT, LAW_ENFORCEMENT, MISSING_PERSON, or PUBLIC_INTEREST) | `consent_record.py` (line 51) |

\newpage

# Use Case Model

## Actor Catalogue

| Actor | Type | Description |
|:------|:-----|:------------|
| Security Operator | Primary (Human) | The primary user who monitors live video feeds, enrols targets, reviews alerts and detection logs, performs forensic scans, and views analytics |
| System Administrator | Primary (Human) | Configures system settings (cameras, thresholds, retention policies), reviews audit logs, manages data compliance operations |
| FBI Wanted API | External System | Provides structured JSON data of fugitives and missing persons via a RESTful HTTP endpoint |
| Telegram Bot API | External System | Receives alert notification messages and forensic snapshot images for delivery to a configured chat/channel |

## System-Level Use Case Diagram

The following describes the DrishtiX use case model. In the absence of rendered diagram images, the relationships are documented in tabular form.

| Use Case ID | Use Case Name | Primary Actor | Related Actors |
|:-------------|:-------------|:--------------|:---------------|
| UC-01 | Monitor Live Feed | Security Operator | Camera (device) |
| UC-02 | Enrol Target | Security Operator | — |
| UC-03 | View Detection Logs | Security Operator | — |
| UC-04 | Perform Forensic Scan | Security Operator | — |
| UC-05 | View Analytics Dashboard | Security Operator | — |
| UC-06 | Receive Alert Notification | Security Operator | Telegram Bot API |
| UC-07 | Configure System Settings | System Administrator | — |
| UC-08 | Manage Camera Sources | System Administrator | Camera (device) |
| UC-09 | Execute Data Erasure | System Administrator | — |
| UC-10 | Ingest FBI Wanted Data | FBI Wanted API | — |
| UC-11 | Dispatch Telegram Alert | Telegram Bot API | — |
| UC-12 | Export Detection Report | Security Operator | — |
| UC-13 | Deactivate Target | Security Operator | — |
| UC-14 | Review Audit Trail | System Administrator | — |
| UC-15 | Manage Data Retention | System Administrator | — |

**Relationships:**

- UC-02 (Enrol Target) <<includes>> automatic embedding extraction
- UC-01 (Monitor Live Feed) <<includes>> face detection, recognition, and tracking
- UC-06 (Receive Alert Notification) <<extends>> UC-01 (triggered only on confirmed match)
- UC-10 (Ingest FBI Wanted Data) <<includes>> UC-02 (creates targets from API records)
- UC-09 (Execute Data Erasure) <<includes>> audit logging

## Use Case Specifications

### UC-01: Monitor Live Feed

| Field | Detail |
|:------|:-------|
| **ID** | UC-01 |
| **Name** | Monitor Live Feed |
| **Primary Actor** | Security Operator |
| **Preconditions** | Camera source is configured and accessible; gallery contains >= 1 enrolled target |
| **Trigger** | Operator clicks "Start Camera" on the Dashboard view |
| **Main Flow** | 1. System activates the CaptureWorker thread, opening the camera source. 2. VideoThread acquires frames at 30 FPS and pushes to bounded queue. 3. YuNet face detection processes each frame, identifying bounding boxes and landmarks. 4. Quality gate filters low-quality crops (blur, resolution). 5. RecognitionWorker extracts face embedding and queries GalleryManager. 6. System renders annotated video feed with bounding boxes and landmarks on DashboardView. 7. StatusBar updates with real-time FPS, latency, and gallery size. |
| **Alternate Flows** | A1: No faces detected — system continues displaying video without bounding boxes. A2: Face detected but below quality gate — face is tracked spatially but not sent to recognition. |
| **Exception Flows** | E1: Camera disconnects — system displays "Camera Disconnected" status and attempts reconnection via RtspSource exponential backoff. E2: Recognition engine fails — error is logged via structlog; UI continues displaying video. |
| **Postconditions** | Video feed is displayed in real time; any matched targets trigger alert flow (UC-06). |
| **Business Rules** | BR-02 (multi-frame confirmation), NFR-02 (< 200 ms latency) |
| **Linked Requirements** | FR-DET-01, FR-DET-02, FR-DET-03, FR-REC-01, FR-REC-03, NFR-01, NFR-02, NFR-03 |

### UC-02: Enrol Target

| Field | Detail |
|:------|:-------|
| **ID** | UC-02 |
| **Name** | Enrol Target |
| **Primary Actor** | Security Operator |
| **Preconditions** | System is running; operator is on the Target Registry view |
| **Trigger** | Operator clicks "Add Target" button |
| **Main Flow** | 1. System displays the registration dialog with fields: full name, category (Criminal/Missing Person), case number, description, and photo upload zone. 2. Operator fills in target details and uploads one or more reference photographs. 3. System validates input (name required, category required, at least one photo). 4. For each uploaded photo, system runs FaceDetectionService to locate faces, then FaceRecognitionService to extract 128-D embedding. 5. System persists TargetRegistry record, TargetImage records, and FaceEmbedding records to database. 6. System creates a ConsentRecord with legal_basis. 7. System logs TARGET_CREATED action in AuditLog. 8. GalleryManager reloads the in-memory gallery matrix. 9. System refreshes the registry view to show the new target card. |
| **Alternate Flows** | A1: No face detected in uploaded photo — system displays error "No face detected in image" and allows retry. A2: Multiple faces in photo — system uses the largest detected face. |
| **Exception Flows** | E1: Database write fails — error displayed; no partial records persisted (transactional). |
| **Postconditions** | Target is enrolled, embedding is in gallery, target card appears in registry. |
| **Business Rules** | BR-01 (at least one photo required), BR-04 (centroid template if multiple photos) |
| **Linked Requirements** | FR-TGT-01, FR-TGT-02, FR-TGT-03, FR-CON-01 |

### UC-06: Receive Alert Notification

| Field | Detail |
|:------|:-------|
| **ID** | UC-06 |
| **Name** | Receive Alert Notification |
| **Primary Actor** | Security Operator |
| **Related Actors** | Telegram Bot API |
| **Preconditions** | UC-01 is active (live monitoring); a gallery target matches an observed face |
| **Trigger** | Multi-frame confirmation gate reaches threshold (N >= 2 within 5 s) |
| **Main Flow** | 1. AlertService verifies match is not in cooldown for this target. 2. System saves a forensic snapshot (face crop) to disk. 3. System persists DetectionLog record to database. 4. System emits `alert_created` signal on the SignalBus. 5. AlertSidebar adds a new AlertCard with target name, category pill, confidence %, timestamp, and snapshot thumbnail. 6. SoundPlayer plays category-specific audio alert (alarm for Criminal, chime for Missing Person). 7. If Telegram is enabled, TelegramService dispatches an asynchronous sendPhoto request with snapshot image and alert metadata. |
| **Alternate Flows** | A1: Target is in cooldown — alert is suppressed; no card, sound, or Telegram dispatch. A2: Telegram is disabled — steps 1–6 execute; step 7 is skipped. |
| **Exception Flows** | E1: Telegram API unreachable — error is logged; other alert channels proceed normally. E2: Disk full — snapshot save fails; alert card shows placeholder thumbnail. |
| **Postconditions** | Operator is notified via visual, auditory, and (optionally) Telegram channels. Detection event is persisted for forensic review. |
| **Business Rules** | BR-02, BR-03 |
| **Linked Requirements** | FR-ALT-01, FR-ALT-02, FR-ALT-03, FR-ALT-04, FR-ALT-05 |

### UC-09: Execute Data Erasure

| Field | Detail |
|:------|:-------|
| **ID** | UC-09 |
| **Name** | Execute Data Erasure (DPDP Act Section 8(9)) |
| **Primary Actor** | System Administrator |
| **Preconditions** | Target exists in the database |
| **Trigger** | Administrator initiates erasure request for a specific target |
| **Main Flow** | 1. ErasureService receives the target_id for erasure. 2. System performs SQL CASCADE delete: target_registry, target_image, face_embedding, detection_log records. 3. System deletes all snapshot image files from disk for this target. 4. System deletes profile image file from disk. 5. GalleryManager purges the target from the in-memory gallery matrix. 6. System reloads the gallery to rebuild the cosine matching matrix. 7. System generates an ErasureReceipt with timestamp, items deleted, and operator identity. 8. System logs DATA_ERASURE action in AuditLog. |
| **Alternate Flows** | A1: Target has no detection logs — erasure proceeds for target, images, and embeddings only. |
| **Exception Flows** | E1: File deletion fails (locked file) — error logged; database records still deleted. |
| **Postconditions** | All biometric data for the target is permanently removed from database, disk, and memory. An auditable receipt is generated. |
| **Business Rules** | BR-05 |
| **Linked Requirements** | FR-ERS-01, FR-ERS-02, NFR-06 |

### UC-10: Ingest FBI Wanted Data

| Field | Detail |
|:------|:-------|
| **ID** | UC-10 |
| **Name** | Ingest FBI Wanted Data |
| **Primary Actor** | FBI Wanted API (automated) |
| **Preconditions** | Internet connectivity available; IngestionWorker is running |
| **Trigger** | Timer fires every 60 minutes (configurable) |
| **Main Flow** | 1. IngestionWorker invokes IngestionService.sync(). 2. System fetches paginated JSON from FBI Wanted API (/wanted/v1/list). 3. For each record: check if case number already exists in database. 4. If new: download mugshot image, extract face embedding, persist TargetRegistry + TargetImage + FaceEmbedding records. 5. Log TARGET_CREATED in AuditLog. 6. Emit targets_changed signal to refresh UI views. |
| **Alternate Flows** | A1: No new records found — sync completes with zero insertions. A2: No internet — IngestionService logs warning and skips cycle. |
| **Exception Flows** | E1: API rate limit exceeded — backoff and retry on next cycle. |
| **Postconditions** | Gallery is updated with any new FBI wanted persons. |
| **Business Rules** | BR-01 |
| **Linked Requirements** | FR-ING-01, FR-ING-02, FR-ING-03 |

\newpage

# Architecture

## Architectural Style and Rationale

DrishtiX employs a **Modular Desktop Monolith with Decoupled Pipeline Workers** architecture. This was selected after evaluating three alternatives:

| Option | Pros | Cons | Decision |
|:-------|:-----|:-----|:---------|
| Monolith with Qt threads | Low latency, simple deployment, shared memory | Tight coupling risk | **Selected** (with mitigations) |
| Microservices (gRPC/REST) | Independent scaling, language flexibility | Network latency, deployment complexity | Rejected for edge deployment |
| Actor model (e.g. Ray) | Clean concurrency, fault isolation | Heavy runtime, learning curve | Rejected for simplicity |

**Rationale:** Edge deployment requires sub-200 ms latency, single-machine installation, and no network infrastructure. The monolith architecture with Qt-managed threads provides the necessary performance while the SignalBus and DAO patterns maintain sufficient modularity for testing and future extraction into services.

## 5-Tier Pipeline Architecture

| Tier | Components | Threading Model |
|:-----|:-----------|:---------------|
| 1. Ingestion | `VideoThread`, `CaptureWorker`, `RtspSource` | Dedicated QThread (producer loop) |
| 2. AI Vision | `FaceDetectionService`, `FaceRecognitionService`, `FaceTrackingManager`, `LivenessService` | Consumer loop + QThreadPool dispatch |
| 3. Matching | `GalleryManager`, `AlertService`, `OccupancyAnalytics` | Main thread (atomic swap pattern) |
| 4. Persistence | `TargetDAO`, `EmbeddingDAO`, `DetectionLogDAO`, `AuditDAO` | SQLAlchemy sessions (WAL mode) |
| 5. Presentation | `MainWindow`, 6 views, 21 widgets, `TelegramService` | Qt main event loop + bounded executor |

## C4 Context Diagram (Textual)

**System:** DrishtiX Desktop Application

**Users:**

- Security Operator → uses DrishtiX to monitor feeds, manage targets, and review alerts
- System Administrator → configures system settings and manages data compliance

**External Systems:**

- USB/RTSP Camera → provides live video stream input to DrishtiX
- FBI Wanted API → provides fugitive and missing person data (HTTP GET)
- Telegram Bot API → receives alert notifications with forensic snapshots (HTTP POST)
- SQLite Database → stores targets, embeddings, detection logs, audit trail (local file)

## C4 Container Diagram (Textual)

**Container 1: DrishtiX Desktop App** (Python 3.11+ / PySide6)

- `drishtix.core` — Configuration, constants, enums, signal bus
- `drishtix.dao` — Data access layer (7 repository modules)
- `drishtix.models` — ORM entity definitions (8 entities)
- `drishtix.services` — Business logic (16 service modules)
- `drishtix.ui` — Presentation layer (6 views, 21 widgets, QSS themes)
- `drishtix.workers` — Background thread workers (4 workers)
- `drishtix.utils` — Utility modules (4 modules)

**Container 2: Re-ID Microservice** (FastAPI + Uvicorn)

- REST API for body re-identification using OSNet ONNX model
- Endpoints: GET /health, POST /extract, POST /match

**Container 3: SQLite Database** (data/drishtix.db)

- 8 tables with WAL mode, optional SQLCipher encryption

## Technology Stack

| Layer | Technology | Version (from lockfile) | Purpose in DrishtiX |
|:------|:-----------|:-----------------------|:--------------------|
| Runtime | Python | >= 3.11 (tested 3.14.2) | Primary execution environment |
| GUI framework | PySide6 (Qt6) | >= 6.5.0 | Desktop interface, QThread, signals/slots |
| Computer vision | OpenCV (headless) | >= 4.9.0 | YuNet face detection, SFace recognition, CSRT tracking |
| Deep learning | InsightFace + ONNX Runtime | >= 1.0.0 / >= 1.19.0 | ArcFace 512-D embeddings, OSNet body Re-ID |
| Numerical computing | NumPy | >= 1.24.0 | Vector math, matrix cosine similarity |
| Database ORM | SQLAlchemy | >= 2.0.0 | Declarative ORM, session management |
| Database engine | SQLite / SQLCipher | 3.x | Embedded persistence, optional encryption |
| Configuration | Pydantic + pydantic-settings | >= 2.0.0 | Typed configuration validation |
| Serialisation | PyYAML | >= 6.0 | YAML config file parsing |
| Logging | structlog | >= 23.0.0 | Structured contextual logging |
| HTTP client | HTTPX | >= 0.24.0 | FBI API ingestion, Telegram dispatch |
| Charts | Matplotlib | >= 3.7.0 | Analytics chart rendering |
| System monitoring | psutil | >= 5.9.0 | Memory and CPU telemetry |
| Templates | Jinja2 | >= 3.0 | QSS stylesheet generation |
| Testing | pytest + pytest-qt | >= 7.0 / >= 4.2 | Automated unit and integration testing |
| Linting | Ruff | >= 0.1.0 | Code style enforcement |
| Microservice | FastAPI + Uvicorn | >= 0.115.0 / >= 0.34.0 | Re-ID REST API |

## Design Patterns

| Pattern | Implementation | File Reference |
|:--------|:--------------|:---------------|
| Singleton | `GalleryManager._instance`, `AlertService._instance`, `TelegramService._instance` | `gallery_manager.py:72`, `alert_service.py:47` |
| Observer (Signal/Slot) | `SignalBus` with 11 typed Qt signals | `core/signals.py:22–83` |
| Repository (DAO) | 7 repository classes isolating data access | `dao/target_dao.py`, `dao/embedding_dao.py`, etc. |
| Producer-Consumer | `VideoThread` bounded queue (maxsize=2) | `workers/video_thread.py:69` |
| Strategy | `recognition.engine` config switches between SFace and InsightFace | `core/config.py:68`, `face_recognition.py`, `insightface_service.py` |
| Template Method | `CaptureWorker.run()` → `VideoThread.run()` lifecycle | `workers/capture_worker.py` |
| Atomic Swap | `GalleryManager.reload_gallery()` rebuilds state in locals, then swaps | `gallery_manager.py:110–185` |
| Decorator (Pydantic) | `@field_validator` on config fields | `core/config.py:40–47` |

## Design-Decision Log

| # | Decision | Alternatives Considered | Rationale | Consequences |
|:--|:---------|:----------------------|:----------|:-------------|
| D-01 | Use Python + PySide6 instead of Java + JavaFX | Java 17 (original), Electron, Flutter Desktop | Python has richer CV/ML ecosystem (OpenCV, InsightFace, ONNX Runtime). PySide6 provides native performance with Qt threading model. | Entire codebase was migrated from Java to Python in Sprint 2 |
| D-02 | SQLite over MongoDB | MongoDB (original v1), PostgreSQL | SQLite is zero-configuration, file-based, ideal for edge deployment. No server process needed. SQLCipher adds encryption. | Replaced MongoDB driver; simpler deployment |
| D-03 | Bounded queue (maxsize=2) for frame buffering | Unbounded queue, triple buffer, ring buffer | Prevents memory growth when inference is slower than capture. Drop policy keeps only the latest frames, avoiding stale data. | Minimal frame latency; occasional dropped frames under load |
| D-04 | Centroid template averaging | Store all embeddings, majority voting | Reduces gallery rows to 1 per target, improving matching speed. L2-normalised mean is robust to pose/illumination variation. | Single centroid per target; recomputed on gallery reload |
| D-05 | Multi-frame confirmation gate (N >= 2, 5 s window) | Single-frame alerting, temporal smoothing | Dramatically reduces false positive alerts. Trades ~200 ms additional latency for operational reliability. | Alerts fire only after sustained match evidence |
| D-06 | SFace (128-D) as default recognition engine | ArcFace/InsightFace (512-D) only | SFace is lighter (3 ms vs 15 ms inference), sufficient accuracy for single-camera scenarios. ArcFace available as optional upgrade. | Dual-engine support with runtime switching |
| D-07 | Qt SignalBus for inter-thread communication | Direct method calls, asyncio, message queue | Qt signals are thread-safe with automatic marshalling. SignalBus singleton centralises all communication. | Clean decoupling; all signals documented in one file |
| D-08 | Pydantic v2 for configuration validation | raw YAML parsing, dataclasses | Pydantic provides type coercion, validation, and environment variable overrides. `validate_assignment=True` enforces constraints on runtime mutations. | Type-safe config; runtime validation from Settings UI |
| D-09 | structlog for logging | stdlib logging only, loguru | structlog provides structured JSON output, correlation IDs, and contextual logging without changing existing logging.getLogger() calls. | Machine-parseable logs in production; colored console in development |
| D-10 | DPDP Act 2023 compliance provisions | No compliance, GDPR framework | India-specific regulation applicable to biometric data processing. ConsentRecord, ErasureService, and RetentionService implement statutory requirements. | Consent tracking, erasure receipts, automated retention |

\newpage

# Data Design

## Entity-Relationship Model

The DrishtiX database consists of 8 entities organised into three conceptual domains:

1. **Core Registry** — `target_registry`, `target_image`, `face_embedding`, `consent_record`
2. **Surveillance** — `camera_source`, `detection_log`
3. **Governance** — `audit_log`, `app_config`

### Relationships

| Relationship | Cardinality | Cascade |
|:-------------|:-----------|:--------|
| `target_registry` → `target_image` | 1:N | DELETE-ORPHAN |
| `target_registry` → `face_embedding` | 1:N | DELETE-ORPHAN |
| `target_image` → `face_embedding` | 1:N | SET NULL (source_image_id) |
| `target_registry` → `consent_record` | 1:N | CASCADE |
| `target_registry` → `detection_log` | 1:N | — |
| `camera_source` → `detection_log` | 1:N | — |

## Table Dictionary

### target_registry

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| target_id | INTEGER | PK, autoincrement | Unique target identifier |
| full_name | VARCHAR(255) | NOT NULL, indexed | Full name of the person of interest |
| category | VARCHAR(20) | NOT NULL, indexed | CRIMINAL or MISSING_PERSON |
| case_number | VARCHAR(100) | UNIQUE, nullable | Law enforcement case reference |
| description | TEXT | nullable | Freeform description |
| profile_image_path | VARCHAR(500) | nullable | Path to primary profile photograph |
| is_active | BOOLEAN | default True, indexed | Soft-delete flag |
| created_at | DATETIME | default now() | Record creation timestamp |
| updated_at | DATETIME | default now(), on-update | Last modification timestamp |

### target_image

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| image_id | INTEGER | PK, autoincrement | Unique image identifier |
| target_id | INTEGER | FK → target_registry, indexed | Parent target reference |
| image_path | VARCHAR(500) | NOT NULL | Filesystem path to the photograph |
| image_order | INTEGER | default 0 | Display ordering |
| uploaded_at | DATETIME | default now() | Upload timestamp |

### face_embedding

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| embedding_id | INTEGER | PK, autoincrement | Unique embedding identifier |
| target_id | INTEGER | FK → target_registry, indexed | Parent target reference |
| source_image_id | INTEGER | FK → target_image (SET NULL), nullable | Source image reference |
| embedding_vector | BLOB | NOT NULL | Float32 array (512 bytes for 128-D SFace; 2048 bytes for 512-D ArcFace) |
| model_version | VARCHAR(50) | default 'sface_128', nullable | Model identifier string |
| created_at | DATETIME | default now() | Extraction timestamp |

### detection_log

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| log_id | INTEGER | PK, autoincrement | Unique log identifier |
| target_id | INTEGER | FK → target_registry, indexed | Matched target reference |
| camera_id | INTEGER | FK → camera_source, nullable | Source camera reference |
| match_confidence | FLOAT | NOT NULL | Cosine similarity score (0.0–1.0) |
| snapshot_path | VARCHAR(500) | nullable | Path to forensic snapshot image |
| location_tag | VARCHAR(255) | nullable | Location metadata |
| detection_timestamp | DATETIME | default now(), indexed | Time of detection event |
| created_at | DATETIME | default now() | Record creation timestamp |

### camera_source

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| camera_id | INTEGER | PK, autoincrement | Unique camera identifier |
| camera_name | VARCHAR(255) | NOT NULL | Human-readable camera label |
| source_uri | VARCHAR(500) | NOT NULL | Device index or RTSP/HTTP URL |
| is_active | BOOLEAN | default True | Active flag |
| created_at | DATETIME | default now() | Registration timestamp |

### consent_record

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| consent_id | INTEGER | PK, autoincrement | Unique consent identifier |
| target_id | INTEGER | FK → target_registry, indexed | Subject target reference |
| legal_basis | VARCHAR(50) | NOT NULL | CONSENT, LAW_ENFORCEMENT, MISSING_PERSON, or PUBLIC_INTEREST |
| notice_version | VARCHAR(20) | default '1.0' | Version of the data processing notice |
| collected_by | VARCHAR(100) | nullable | Identity of the operator who collected consent |
| consent_text | TEXT | nullable | Consent narrative text |
| is_active | BOOLEAN | default True | Active/withdrawn flag |
| collected_at | DATETIME | default now() | Consent collection timestamp |
| withdrawn_at | DATETIME | nullable | Consent withdrawal timestamp |

### audit_log

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| audit_id | INTEGER | PK, autoincrement | Unique audit entry identifier |
| action | VARCHAR(100) | NOT NULL, indexed | Action type (TARGET_CREATED, DATA_ERASURE, CONFIG_UPDATE) |
| entity_type | VARCHAR(50) | nullable | Affected entity type name |
| entity_id | INTEGER | nullable | Affected entity primary key |
| details | TEXT | nullable | JSON-serialised action details |
| timestamp | DATETIME | default now(), indexed | Action timestamp |

### app_config

| Column | Type | Constraints | Description |
|:-------|:-----|:-----------|:------------|
| config_id | INTEGER | PK, autoincrement | Unique config entry identifier |
| config_key | VARCHAR(100) | UNIQUE, NOT NULL, indexed | Configuration key name |
| config_value | TEXT | NOT NULL | Configuration value (string-serialised) |
| description | TEXT | nullable | Human-readable description |
| updated_at | DATETIME | default now(), on-update | Last modification timestamp |

## Indexes

| Table | Index | Columns | Purpose |
|:------|:------|:--------|:--------|
| target_registry | ix_target_name | full_name | Name search and filtering |
| target_registry | ix_target_category | category | Category-based filtering |
| target_registry | ix_target_active | is_active | Active target queries |
| detection_log | ix_detection_timestamp | detection_timestamp | Time-range queries |
| detection_log | ix_detection_target | target_id | Per-target detection history |
| audit_log | ix_audit_action | action | Action-type filtering |
| audit_log | ix_audit_timestamp | timestamp | Time-range queries |

\newpage

# Security Design

## Authentication and Authorisation Model

DrishtiX v4.0 operates as a single-user desktop application without network-accessible endpoints (except the optional Re-ID microservice). There is no user login, session management, or role-based access control. Physical access to the machine implies full access to the application.

**Future consideration:** For multi-user deployments, a Qt-based login dialog with role-based view restrictions could be added. The existing architecture supports this through the Settings view's access to sensitive operations (erasure, configuration changes).

## Data Protection

| Measure | Implementation | File Reference |
|:--------|:--------------|:---------------|
| Database encryption (at rest) | Optional SQLCipher AES-256 via `PRAGMA key='<passphrase>'` | `models/base.py:62–64` |
| WAL mode | `PRAGMA journal_mode=WAL` prevents corruption on crash | `models/base.py:59` |
| Foreign key enforcement | `PRAGMA foreign_keys=ON` ensures referential integrity | `models/base.py:60` |
| Secret externalisation | Telegram tokens, encryption keys stored in config.yaml or `DRISHTIX_*` env vars | `core/config.py` |
| Log redaction | Tokens and keys are never logged; structlog processors sanitise output | `app.py:45–53` |
| Snapshot isolation | Forensic snapshots stored in `data/snapshots/` with timestamped filenames | `alert_service.py` |
| Data retention | Automated purge of expired logs and snapshots via RetentionService | `retention_service.py:35–115` |
| Right to erasure | Multi-layer cascade deletion with auditable receipt | `erasure_service.py:65–195` |
| Consent tracking | ConsentRecord table records legal basis per DPDP Act 2023 §6 | `consent_record.py:30–85` |

## STRIDE Threat Analysis

| Threat | Category | Risk | Mitigation |
|:-------|:---------|:-----|:-----------|
| Unauthorised access to database file | Tampering, Information Disclosure | High | SQLCipher encryption (optional), filesystem permissions |
| Injection via target name/description | Tampering | Medium | SQLAlchemy parameterised queries prevent SQL injection |
| Spoofing via printed photo | Spoofing | Medium | LivenessService passive anti-spoofing (LBP, YCbCr, FFT) |
| Telegram token leakage | Information Disclosure | High | Token in config.yaml, not hardcoded; never logged |
| Denial of service via high frame rate | Denial of Service | Low | Bounded queue (maxsize=2) drops excess frames |
| Gallery poisoning via FBI API | Elevation of Privilege | Low | Case number deduplication prevents duplicate targets |
| Snapshot disk exhaustion | Denial of Service | Medium | RetentionService purges snapshots older than retention period |
| Biometric data exfiltration | Information Disclosure | High | No network endpoints except optional Telegram; data stays local |

## OWASP Top 10 Mapping

| OWASP Category | Applicability | DrishtiX Mitigation |
|:---------------|:-------------|:-------------------|
| A01: Broken Access Control | Low (desktop app) | Single-user model; no network auth surface |
| A02: Cryptographic Failures | Medium | SQLCipher AES-256 encryption available; secrets externalised |
| A03: Injection | Medium | SQLAlchemy ORM with parameterised queries |
| A04: Insecure Design | Low | Architecture reviewed; defence-in-depth layers |
| A05: Security Misconfiguration | Medium | Sensible defaults in config.yaml; validation via Pydantic |
| A06: Vulnerable Components | Medium | Dependencies managed via requirements.txt; npm audit recommended |
| A07: Auth Failures | N/A | No authentication mechanism |
| A08: Data Integrity Failures | Low | SQLite WAL mode; foreign key constraints |
| A09: Logging Failures | Low | structlog with correlation IDs; audit_log table |
| A10: SSRF | Low | FBI API URL is hardcoded; no user-controlled URLs |

\newpage

# Traceability

## Requirements-to-Use-Case-to-Module-to-Test Traceability Matrix

| Requirement | Use Case(s) | Module/Service | Test File(s) |
|:------------|:-----------|:---------------|:-------------|
| FR-DET-01 | UC-01 | `face_detection.py` | `test_e2e_integration.py` |
| FR-DET-03 | UC-01 | `video_thread.py` | `test_e2e_integration.py` |
| FR-REC-01 | UC-01, UC-02 | `face_recognition.py` | `test_vector_math.py` |
| FR-REC-02 | UC-01, UC-02 | `insightface_service.py` | `test_insightface_vector.py` |
| FR-REC-03 | UC-01 | `gallery_manager.py` | `test_vector_math.py` |
| FR-TGT-01 | UC-02 | `target_dao.py`, `registry_view.py` | `test_dao.py` |
| FR-TGT-02 | UC-02 | `target_dao.py` | `test_dao.py` |
| FR-TGT-03 | UC-02 | `gallery_manager.py`, `face_recognition.py` | `test_e2e_integration.py` |
| FR-ALT-01 | UC-06 | `alert_service.py` | `test_e2e_integration.py` |
| FR-ALT-02 | UC-06 | `alert_service.py`, `telegram_service.py` | `test_e2e_integration.py` |
| FR-ING-01 | UC-10 | `ingestion_service.py`, `ingestion_worker.py` | `test_e2e_integration.py` |
| FR-SCN-01 | UC-04 | `image_scan_view.py` | — |
| FR-ANL-01 | UC-05 | `analytics_service.py`, `analytics_view.py` | `test_analytics.py` |
| FR-LOG-01 | UC-03 | `detection_log_dao.py`, `detection_log_view.py` | `test_dao.py` |
| FR-EXP-01 | UC-12 | `export_service.py` | — |
| FR-ERS-01 | UC-09 | `erasure_service.py` | `test_e2e_integration.py` |
| FR-RET-01 | UC-15 | `retention_service.py` | — |
| FR-CON-01 | UC-02 | `consent_record.py` | — |
| NFR-01 | UC-01 | `face_detection.py` | — |
| NFR-02 | UC-01, UC-06 | `video_thread.py`, `alert_service.py` | — |
| NFR-05 | — | `models/base.py` | — |
| NFR-06 | — | `audit_dao.py`, `audit_log.py` | `test_dao.py` |

\newpage

# Risks, Limitations, and Future Enhancements

## Known Limitations

| ID | Limitation | Impact | Workaround |
|:---|:----------|:-------|:-----------|
| L-01 | Single camera stream at a time | Cannot monitor multiple areas simultaneously | Multi-camera grid planned in roadmap |
| L-02 | No user authentication | Any person with machine access can operate the system | Physical access controls recommended |
| L-03 | SQLite single-writer concurrency | Potential write contention under extreme load | WAL mode with busy_timeout mitigates; PostgreSQL migration possible |
| L-04 | No CI/CD pipeline | Manual build and test execution | GitHub Actions pipeline recommended |
| L-05 | Bias in face recognition models | Potential demographic bias in YuNet/SFace models | Bias evaluation script (`evaluate_bias.py`) provided as stub |

## Risks

| ID | Risk | Probability | Impact | Mitigation |
|:---|:-----|:-----------|:-------|:-----------|
| R-01 | False positive alerts in crowded environments | Medium | High | Multi-frame confirmation gate (BR-02) |
| R-02 | ONNX model compatibility with future Python versions | Low | Medium | Pin ONNX Runtime version; test on new runtimes |
| R-03 | SQLite database corruption due to power failure | Low | High | WAL mode; periodic backup recommended |
| R-04 | Telegram API changes breaking alert delivery | Low | Medium | Alert also delivered via audio and desktop HUD |
| R-05 | Gallery performance degradation with very large target sets (> 10,000) | Low | Medium | NumPy BLAS operations scale linearly; FAISS migration possible |

## Future Enhancements

| ID | Enhancement | Priority | Rationale |
|:---|:-----------|:---------|:----------|
| FE-01 | Multi-camera RTSP stream grid multiplexer | High | Monitor multiple areas simultaneously |
| FE-02 | Deep SORT / ByteTrack integration | Medium | Long-term cross-camera tracking |
| FE-03 | Docker containerisation | Medium | Standardise deployment across environments |
| FE-04 | User authentication with RBAC | Medium | Multi-operator installations |
| FE-05 | FAISS or Annoy for gallery indexing | Low | Sub-linear matching for very large galleries |
| FE-06 | Mobile companion app | Low | Remote alert monitoring |
| FE-07 | Cloud sync for multi-site deployments | Low | Centralised gallery management |

\newpage

# Appendices

## Appendix A: Notation Legend

| Symbol | Meaning |
|:-------|:--------|
| `<<include>>` | The base use case always invokes the included use case |
| `<<extend>>` | The extending use case is conditionally invoked |
| 1:N | One-to-many relationship |
| PK | Primary key |
| FK | Foreign key |
| UK | Unique key |
| → | Data flow direction (DFD) |
| MoSCoW | Must / Should / Could / Won't prioritisation |

## Appendix B: Diagram Source Files

All diagrams in this document are described in structured text format (Mermaid notation). The source files and rendered images are located in `documentation/diagrams/`.

| Diagram ID | Source File | Type |
|:-----------|:-----------|:-----|
| ER-01 | `diagrams/src/er-diagram.mmd` | Entity-Relationship |
| UML-CL-01 | `diagrams/src/class-models.mmd` | Class Diagram (ORM) |
| UML-CL-02 | `diagrams/src/class-services.mmd` | Class Diagram (Services) |
| DFD-00 | `diagrams/src/dfd-level0.mmd` | Data Flow Diagram (Context) |
| DFD-01 | `diagrams/src/dfd-level1.mmd` | Data Flow Diagram (Level 1) |

## Appendix C: Glossary

| Term | Definition |
|:-----|:-----------|
| ArcFace | Deep face recognition model producing 512-dimensional angular margin feature embeddings |
| Centroid template | L2-normalised mean embedding vector computed across multiple enrolled images of a single target |
| Cosine similarity | Normalised dot product of two embedding vectors measuring angular proximity |
| DPDP Act 2023 | Digital Personal Data Protection Act, 2023 (India) |
| Face quality gate | Pre-recognition filter evaluating Laplacian blur variance and bounding box resolution |
| Gallery matrix | Contiguous in-memory 2D float32 NumPy array of normalised embedding vectors |
| Multi-frame confirmation | Rule requiring N consecutive positive matches within a time window before alert fires |
| ONNX | Open Neural Network Exchange format for model portability |
| OSNet | Omni-Scale Network for whole-body person re-identification |
| SFace | Lightweight 128-dimensional deep face recognition model |
| SignalBus | Centralised Qt QObject providing typed signals for thread-safe cross-component communication |
| WAL mode | Write-Ahead Logging mode for SQLite enabling concurrent reads during writes |
| YuNet | Ultra-lightweight deep face detector producing bounding boxes and 5 facial landmarks |
