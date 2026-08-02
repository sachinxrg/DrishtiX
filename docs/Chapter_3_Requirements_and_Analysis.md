# CHAPTER 3: REQUIREMENTS AND ANALYSIS

---

## 3.1 Problem Definition

### 3.1.1 The Passive Surveillance Crisis

The global deployment of over one billion CCTV cameras represents one of the largest capital investments in public safety infrastructure ever undertaken. Yet the operational return on this investment remains critically undermined by a single architectural flaw: **traditional CCTV infrastructure produces passive video, not actionable intelligence**.

In the prevailing "record and review" paradigm, the interpretive burden — determining whether a wanted criminal, a missing child, or an absconding suspect has appeared in the camera's field of view — is delegated entirely to human operators. A typical command-and-control centre requires a single surveillance operator to simultaneously monitor between 16 and 64 multiplexed camera feeds, mentally cross-referencing each face against printed First Information Report (FIR) photographs pinned to a corkboard or stored in unindexed binder volumes. The cognitive demands of this task are immense, and the ergonomic reality is sobering.

### 3.1.2 The Vigilance Decrement

Decades of human factors research have established that sustained vigilance in monotonous visual monitoring tasks degrades below **50% accuracy within the first 20 minutes** of a shift. This phenomenon, formally documented as the *vigilance decrement*, is not a failure of training or discipline — it is a well-characterized limitation of human attentional capacity. When an operator is scanning 32 simultaneous feeds for a specific face, the probability of detecting that face in any given 5-second window approaches statistical negligibility.

The operational latency of the traditional workflow is measured not in milliseconds but in **hours to days**:

```
┌───────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────────┐
│  Camera   │────▶│  NVR/DVR   │────▶│  Manual      │────▶│  Alert       │
│  Captures │     │  Records   │     │  Review      │     │  (if any)    │
│  Frame    │     │  to Disk   │     │  by Operator │     │  to Officer  │
└───────────┘     └────────────┘     └──────────────┘     └──────────────┘
    t = 0           t = 0              t = hours            t = hours+
```

A wanted criminal can traverse a surveilled corridor, board public transport, and vanish entirely — and the alert, if it ever materializes, arrives only during post-incident forensic review. The footage becomes courtroom evidence rather than an operational tool for interdiction.

### 3.1.3 The Alert Fatigue Problem

Even when automated face detection is deployed, poorly designed alert systems compound the problem through **alert fatigue**. If the system generates a modal popup dialog for every detection event, the operator's primary visual resource — the live camera feed — is repeatedly occluded. If the same target is re-detected every 2 seconds, the operator is bombarded with hundreds of identical alerts per hour, each requiring manual dismissal. Within minutes, operators develop "popup blindness" and begin reflexively closing alerts without reviewing them, negating the value of the automated system entirely.

### 3.1.4 The DrishtiX Solution

DrishtiX v3.0 is engineered to resolve all three failure modes simultaneously:

1. **Eliminate Human Vigilance Dependency**: Replace the manual face-matching task with automated deep learning inference (YuNet + SFace + OSNet), collapsing the surveillance-to-action pipeline to under 200 milliseconds.
2. **Non-Blocking Alert Delivery**: Deliver all alerts as styled, scrollable sidebar cards that never occlude the live camera feed.
3. **Intelligent Cooldown Management**: Enforce per-target cooldown windows (default: 30 seconds) that suppress redundant alerts while ensuring no unique detection is missed.

---

## 3.2 Requirements Specification

### 3.2.1 Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| FR-01 | **Live Video Capture** | Capture and render live video from a connected camera (USB, integrated, or RTSP) at a sustained 15+ FPS. |
| FR-02 | **Multi-Target Face Detection** | Detect and localize 9–10+ simultaneous faces in a single frame using the YuNet DNN model, returning bounding boxes and 5-point landmarks. |
| FR-03 | **Real-Time Face Recognition** | Extract 128-dimensional SFace embeddings from detected faces and match against the watchlist gallery via cosine similarity (threshold: 0.363). |
| FR-04 | **Body Re-Identification** | When a recognized target's face is lost (head turn, occlusion), maintain persistent tracking via OSNet 512-dim body embeddings and KCF/CSRT object trackers. |
| FR-05 | **Non-Blocking Sidebar Alerts** | Deliver detection alerts as styled cards in a scrollable sidebar, showing: target name, category badge (CRIMINAL/MISSING), confidence score, case number, live snapshot vs. database photo, and timestamp. |
| FR-06 | **Target Registration** | Allow operators to register new targets by uploading a facial photograph, specifying name, category, case number, and description. Automatically extract and store the SFace embedding. |
| FR-07 | **Target Management** | Provide search, filter (by category), deactivate, and delete operations on the target registry with confirmation dialogs. |
| FR-08 | **Multi-Channel Alert Dispatch** | On positive detection, simultaneously trigger: (a) audible alarm (category-specific WAV), (b) Telegram push notification with snapshot, and (c) sidebar alert card. |
| FR-09 | **Background Watchlist Ingestion** | Automatically ingest wanted profiles from the FBI API (REST/JSON), CBI Wanted List (HTML scraping), and TrackChild Portal (HTML scraping) on a configurable schedule. |
| FR-10 | **Runtime Configuration** | Allow operators to adjust detection thresholds, cooldown periods, audio mute, tracker type, and ingestion settings without restarting the application. |
| FR-11 | **Audit Logging** | Record all critical operations (target add/edit/delete, configuration changes, alert acknowledgements) to an immutable audit trail collection. |
| FR-12 | **Reactive Dashboard Metrics** | Display real-time counters for Total Targets, Criminals, Missing Persons, and Detections Today, updated reactively via JavaFX `IntegerProperty` bindings. |

### 3.2.2 Non-Functional Requirements

| NFR ID | Category | Requirement | Target | Justification |
|---|---|---|---|---|
| NFR-01 | **Latency** | End-to-end pipeline: frame capture → annotated alert delivery | ≤ 200 ms | Faster than human blink reflex (300–400 ms), making the system perceptually instantaneous |
| NFR-02 | **Detection Speed** | YuNet face detection inference per frame | ≤ 5 ms (target ~2 ms) | Must run on the capture thread without dropping frames |
| NFR-03 | **Recognition Speed** | SFace embedding extraction + gallery match per face | ≤ 150 ms | Runs on dedicated 4-thread recognition pool, never blocking the UI |
| NFR-04 | **Frame Rate** | Live camera feed rendering rate | ≥ 15 FPS | Minimum for perceptually smooth video; 30 FPS preferred |
| NFR-05 | **Memory Safety** | Alert queue bounded size | 50 cards max | Prevents unbounded heap growth during extended shifts |
| NFR-06 | **Uptime** | Continuous operation without memory leaks or crashes | 99.5% over 8-hour shifts | `Mat.release()` + bounded alert queue + daemon threads |
| NFR-07 | **Scalability** | Watchlist gallery capacity | 10,000+ profiles | ConcurrentHashMap gallery with O(n) scan, pre-computed centroids |
| NFR-08 | **Privacy** | Data locality | 100% on-device | Zero cloud dependency — no frames, embeddings, or PII leave the machine |
| NFR-09 | **Thermal** | CPU utilization sustainability | ≤ 60% sustained | Frame-skipping (inference every 2nd frame) + KCF (~0.3 ms) trackers |
| NFR-10 | **Resilience** | Graceful degradation when MongoDB is unavailable | Hardcoded defaults | ConfigurationService falls back to `loadDefaults()` |

---

## 3.3 Planning and Scheduling

### 3.3.1 Iterative Development Phases

DrishtiX v3.0 was developed through four iterative architectural upgrade phases, each building upon the validated output of the previous phase:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     DrishtiX v3.0 Development Timeline                       │
├──────────┬───────────────────────────────────────────────────────────────────┤
│ Phase 1  │  Deep Learning CV Pipeline Migration                             │
│          │  ├─ YuNet ONNX integration (FaceDetectorYN)                      │
│          │  ├─ SFace ONNX integration (FaceRecognizerSF)                    │
│          │  ├─ ThreadLocal<FaceRecognizerSF> for pool safety                │
│          │  ├─ 128-dim embedding gallery (ConcurrentHashMap)                │
│          │  └─ Legacy Haar/LBPH fallback preservation                       │
├──────────┼───────────────────────────────────────────────────────────────────┤
│ Phase 2  │  UI/UX Modernization & Bento Grid Dashboard                     │
│          │  ├─ FXML layout redesign (65/35 split, GridPane bento)           │
│          │  ├─ CSS dark theme (WCAG AA compliant)                           │
│          │  ├─ Non-blocking sidebar alert queue (50-card cap)               │
│          │  ├─ Reactive IntegerProperty stat counters                       │
│          │  └─ Category-coded alert badges (red/blue pills)                 │
├──────────┼───────────────────────────────────────────────────────────────────┤
│ Phase 3  │  Dynamic Alert Queue & Multi-Channel Notifications               │
│          │  ├─ Frame-skip strategy (inference every Nth frame)              │
│          │  ├─ KCF/CSRT inter-frame tracker integration                    │
│          │  ├─ OSNet body re-identification (512-dim embeddings)            │
│          │  ├─ Facial-to-Spatial Handoff (body lock mechanism)              │
│          │  ├─ Telegram Bot API push notifications                          │
│          │  └─ Background Ingestion Engine (FBI/CBI/TrackChild)             │
├──────────┼───────────────────────────────────────────────────────────────────┤
│ Phase 4  │  State Management, Threading Fixes & Production Hardening        │
│          │  ├─ Alert card duplication race condition fix                     │
│          │  ├─ IntegerProperty binding desynchronization fix                │
│          │  ├─ Platform.runLater() standardization for all UI mutations     │
│          │  ├─ Recognition pool pre-warming (eliminate cold-start penalty)  │
│          │  ├─ 5-pool threading architecture formalization                  │
│          │  └─ Graceful shutdown hooks (ThreadPools.shutdownAll())          │
└──────────┴───────────────────────────────────────────────────────────────────┘
```

### 3.3.2 Gantt Chart (Simplified)

| Phase | Duration | Key Deliverable |
|---|---|---|
| Phase 1: DNN Pipeline | 4 weeks | YuNet + SFace operational on CPU |
| Phase 2: UI/UX | 3 weeks | Bento grid dashboard, dark theme |
| Phase 3: Alert & Tracking | 4 weeks | Body lock, Telegram, ingestion engine |
| Phase 4: Hardening | 2 weeks | Race condition fixes, pre-warming, shutdown |
| **Total** | **13 weeks** | **Production-ready v3.0** |

---

## 3.4 Software and Hardware Requirements

### 3.4.1 Software Requirements

| Component | Minimum Version | Recommended | Purpose |
|---|---|---|---|
| **Java Runtime** | JDK 17 (LTS) | JDK 17.0.10+ | Platform runtime |
| **JavaFX** | 21.0.2 | 21.0.2 | GPU-accelerated desktop UI |
| **OpenCV** | 4.9.0 | 4.9.0 (via JavaCV 1.5.10) | DNN inference, tracking |
| **MongoDB** | 5.0 | 5.1+ | Document persistence |
| **Operating System** | Windows 10 x64 | Windows 11 x64 | Primary deployment target |
| **Apache Maven** | 3.8+ | 3.9+ | Build and dependency management |

### 3.4.2 Hardware Requirements

| Component | Minimum Specification | Recommended Specification | Rationale |
|---|---|---|---|
| **Processor** | Intel Core i5 (8th Gen) / AMD Ryzen 5 | Intel Core i7 (10th Gen+) with integrated Intel UHD/Iris Xe | YuNet + SFace ONNX inference on CPU; 4+ cores for 5-pool threading |
| **RAM** | 8 GB DDR4 | 16 GB DDR4 | JVM heap (512 MB) + MongoDB WiredTiger cache (1–2 GB) + native Mat buffers |
| **Storage** | 256 GB SSD | 512 GB NVMe SSD | ONNX models (~10 MB), MongoDB data, ingestion images, snapshots |
| **Camera** | 720p USB webcam | 1080p integrated/USB camera | Higher resolution improves small-face detection at distance |
| **GPU** | Not required (CPU-only) | Integrated Intel UHD/Iris Xe | JavaFX Prism uses iGPU for scene graph rendering; ONNX inference remains CPU |
| **Network** | Not required for core operation | Broadband for Telegram alerts + ingestion | Telegram push, FBI/CBI/TrackChild scraping |
| **Display** | 1366×768 | 1920×1080 (Full HD) | Dashboard designed for minimum 1024×700; optimal at 1280×800 |

> **Note on NPU/GPU Acceleration**: While the current architecture executes all ONNX inference on CPU via OpenCV's built-in DNN module, the system is architecturally prepared for hardware acceleration. Laptops equipped with Intel Neural Processing Units (NPU) can leverage **OpenVINO** as an inference backend, and systems with NVIDIA discrete GPUs can use **TensorRT**, both accessible through the OpenCV DNN module's backend selector without source code changes.

---

## 3.5 Preliminary Product Description

### 3.5.1 Dashboard-Centric User Interface

The DrishtiX v3.0 user interface is designed around a single-screen, **dashboard-centric** philosophy: all critical information — live video, detection alerts, system status, and target management — is accessible without navigating away from the primary view. The operator must never lose sight of the live camera feed.

**Layout Architecture (65/35 Bento Grid Split)**:

```
┌─────────────────────────────────────┬──────────────────────┐
│                                     │   System Status       │
│     LIVE SURVEILLANCE FEED          │   ┌──────┬──────┐    │
│     (Camera ImageView)              │   │Total │Today │    │
│                                     │   │Tgts  │Scans │    │
│     • YuNet bounding boxes drawn    │   ├──────┼──────┤    │
│     • Category-coded colors:        │   │Crim  │Miss  │    │
│       RED = Criminal                │   │Match │Prsns │    │
│       CYAN = Missing Person         │   └──────┴──────┘    │
│       GREEN = Unknown               │                      │
│       AMBER = Body Lock (face lost) │   Live Alert Queue    │
│                                     │   ┌─────────────┐    │
├─────────────────────────────────────┤   │ 🚨 Alert #1  │    │
│   Control Bar                       │   │ Name | Cat   │    │
│   ┌────────────────┐ ┌────┐ ┌────┐ │   │ [DB] [Live]  │    │
│   │ Threshold ──○──│ │Cam▾│ │STOP│ │   ├─────────────┤    │
│   └────────────────┘ └────┘ └────┘ │   │ 🔍 Alert #2  │    │
│   FPS: 15  |  🔇 Mute              │   └─────────────┘    │
└─────────────────────────────────────┤   [+ Add Target]     │
                                      └──────────────────────┘
```

**Key UI Elements**:

| Element | Location | Function |
|---|---|---|
| **Camera Feed** | Left 65%, Row 0 | Real-time video with annotated bounding boxes |
| **Stats Panel** | Right 35%, Row 0 (top) | Reactive counters bound to `IntegerProperty` |
| **Control Bar** | Left 65%, Row 1 | Confidence slider, camera selector, start/stop button, mute toggle, FPS counter |
| **Alert Queue** | Right 35%, Row 0–1 | Scrollable list of non-blocking alert cards (max 50) |
| **Header Bar** | Full width, top | "Dashboard" title, notification bell (🔔), profile icon (👤) |

### 3.5.2 Alert Card Anatomy

Each sidebar alert card is a self-contained intelligence unit, displaying:

| Field | Source | Purpose |
|---|---|---|
| Target Name | `TargetRegistry.fullName` | Immediate identification |
| Category Badge | `TargetCategory` (CRIMINAL / MISSING_PERSON) | Color-coded pill: red or blue |
| Confidence Score | Cosine similarity × 100 | Operator verification metric |
| Case/FIR Number | `TargetRegistry.caseNumber` | Immediate legal reference |
| Database Photo | `TargetRegistry.profileImagePath` | Side-by-side verification (left) |
| Live Snapshot | Frame crop at detection time | Side-by-side verification (right) |
| Timestamp | `LocalDateTime.now()` | Forensic and shift-log reference |

### 3.5.3 Memory-Safe Alert Queue

The alert queue enforces a strict **50-card memory cap** (`MAX_ALERT_QUEUE_SIZE = 50`). When the queue reaches capacity, the oldest alert card is removed before a new one is prepended. Combined with the per-target cooldown window (default: 30 seconds), this architecture guarantees bounded memory consumption regardless of surveillance duration, enabling uninterrupted 8–12-hour operational shifts without heap exhaustion.

---

## 3.6 Conceptual Models

### 3.6.1 Data Flow Diagram: Detection-to-Alert Pipeline

```
                    ┌──────────────────┐
                    │   Camera Device  │
                    │   (VideoCapture) │
                    └────────┬─────────┘
                             │  Raw BGR Frame (640×480 or 1080p)
                             ▼
              ┌──────────────────────────────┐
              │    Video Inference Pool       │
              │    (2 daemon threads)         │
              │                              │
              │  ┌────────────────────────┐  │
              │  │  Frame Counter Check   │  │
              │  │  (every Nth frame?)    │  │
              │  └──────┬─────────┬───────┘  │
              │    YES  │         │  NO      │
              │         ▼         ▼          │
              │  ┌────────────┐  ┌────────┐  │
              │  │ YuNet DNN  │  │ KCF /  │  │
              │  │ Detection  │  │ CSRT   │  │
              │  │ (~2 ms)    │  │ Update │  │
              │  └──────┬─────┘  │(~0.3ms)│  │
              │         │        └────┬───┘  │
              │         ▼             │      │
              │  ┌─────────────┐     │      │
              │  │ Face Align  │     │      │
              │  │ (112×112)   │     │      │
              │  └──────┬──────┘     │      │
              └─────────┼────────────┼──────┘
                        │            │
         ┌──────────────▼────────────▼────────────────┐
         │     Recognition Inference Pool              │
         │     (4 daemon threads, CompletableFuture)   │
         │                                             │
         │  ┌─────────────┐    ┌───────────────────┐  │
         │  │ SFace DNN   │    │ OSNet DNN         │  │
         │  │ 128-dim     │    │ 512-dim body      │  │
         │  │ embedding   │    │ embedding         │  │
         │  └──────┬──────┘    └────────┬──────────┘  │
         │         │                    │              │
         │  ┌──────▼──────┐   ┌────────▼──────────┐  │
         │  │ Gallery     │   │ Body Lock         │  │
         │  │ Cosine      │   │ Fusion            │  │
         │  │ Matching    │   │ (α·face + β·body) │  │
         │  │ (≥ 0.363)   │   │                   │  │
         │  └──────┬──────┘   └────────┬──────────┘  │
         └─────────┼───────────────────┼──────────────┘
                   │  MATCH?           │
                   ▼ YES               │
    ┌──────────────────────────────────▼──────────────┐
    │          Alert Orchestration Layer               │
    │                                                  │
    │  ┌──────────┐  ┌──────────────┐  ┌───────────┐ │
    │  │ Audio    │  │ Telegram Bot │  │ Sidebar   │ │
    │  │ Alert    │  │ Push (async) │  │ Alert     │ │
    │  │ Pool     │  │ + Snapshot   │  │ Card      │ │
    │  │ (1 thd)  │  │              │  │ (UI thd)  │ │
    │  └──────────┘  └──────────────┘  └───────────┘ │
    │                                                  │
    │  ┌──────────────────────────────────────────┐   │
    │  │ Detection Log → MongoDB (async persist)  │   │
    │  └──────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────┘
```

### 3.6.2 Threading Architecture: The Five-Pool Contract

The DrishtiX threading model is designed to satisfy a single invariant: **DNN inference must never starve the JavaFX Application Thread of rendering cycles**. The five pools are isolated by strict contracts:

```
┌─────────────────────────────────────────────────────────────┐
│                   JavaFX Application Thread                  │
│  • Scene graph rendering (ImageView frame updates)          │
│  • Alert card injection (Platform.runLater())               │
│  • IntegerProperty counter updates                          │
│  • FXML event handlers                                      │
│  Contract: NO computation > 16ms per callback               │
├─────────────────────────────────────────────────────────────┤
│                   Video Inference Pool (2 threads)           │
│  • Camera frame capture (OpenCVFrameGrabber.grab())         │
│  • YuNet face detection (~2ms)                              │
│  • Tracker initialization & update (KCF/CSRT)              │
│  • Frame-skip decision logic                                │
│  Contract: Yield frames to UI at ≥ 15 FPS                  │
├─────────────────────────────────────────────────────────────┤
│              Recognition Inference Pool (4 threads)          │
│  • SFace embedding extraction (ThreadLocal model)           │
│  • OSNet body embedding extraction                          │
│  • Gallery cosine similarity scan                           │
│  • Body lock fusion (α·face + β·body)                      │
│  Contract: Independent per-face; never block capture        │
├─────────────────────────────────────────────────────────────┤
│                   Audio Alert Pool (1 thread)                │
│  • javax.sound.sampled WAV playback                         │
│  Contract: Fire-and-forget; never block inference           │
├─────────────────────────────────────────────────────────────┤
│                   Ingestion Pool (2 threads, MIN priority)   │
│  • FBI API REST polling                                     │
│  • CBI/TrackChild HTML scraping via JSoup                   │
│  • 2-second rate limiting between HTTP requests             │
│  Contract: MIN priority; never steal CPU from inference      │
├─────────────────────────────────────────────────────────────┤
│                   Scheduled Pool (1 thread)                  │
│  • Snapshot file cleanup                                    │
│  • Configuration periodic refresh                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.6.3 Entity Relationship Model

```
┌──────────────────┐       ┌──────────────────┐
│   targets         │       │  target_images    │
├──────────────────┤       ├──────────────────┤
│ targetId (PK)    │──┐    │ _id              │
│ fullName         │  │    │ targetId (FK)    │
│ category         │  ├───▶│ imagePath        │
│ caseNumber       │  │    │ embedding[128]   │
│ description      │  │    └──────────────────┘
│ profileImagePath │  │
│ isActive         │  │    ┌──────────────────┐
│ createdAt        │  │    │ person_embeddings │
└──────────────────┘  │    ├──────────────────┤
                      ├───▶│ targetId (FK)    │
                      │    │ embedding[128]   │
                      │    │ modelVersion     │
                      │    └──────────────────┘
                      │
                      │    ┌──────────────────┐
                      │    │  detection_logs   │
                      │    ├──────────────────┤
                      └───▶│ targetId (FK)    │
                           │ timestamp        │
                           │ confidence       │
                           │ snapshotPath     │
                           │ cameraId         │
                           └──────────────────┘

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   config          │   │   audit_log       │   │  camera_sources   │
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ key (PK)         │   │ action           │   │ cameraId (PK)    │
│ value            │   │ details          │   │ name             │
└──────────────────┘   │ timestamp        │   │ uri              │
                       │ userId           │   │ isActive         │
                       └──────────────────┘   └──────────────────┘
```

### 3.6.4 Use Case Summary

| Use Case | Primary Actor | Trigger | System Response |
|---|---|---|---|
| **UC-01**: Monitor Live Feed | Operator | Camera started | Render annotated video at 15+ FPS with bounding boxes |
| **UC-02**: Detect Known Target | System (auto) | Face matched ≥ 0.363 | Inject sidebar alert card + audio + Telegram push |
| **UC-03**: Register New Target | Operator | Click "Add Target" | Upload photo → extract embedding → store in gallery |
| **UC-04**: Search Targets | Operator | Type in search field | Filter target table by name or case number |
| **UC-05**: Deactivate Target | Operator | Click "Deactivate" | Mark target inactive; suppress future alerts |
| **UC-06**: Delete Target | Operator | Click "Delete" (2-step confirm) | Permanently remove target + embeddings + logs |
| **UC-07**: Adjust Threshold | Operator | Move confidence slider | Live-update recognition sensitivity |
| **UC-08**: Ingest FBI Data | System (scheduled) | 6-hour timer fires | Poll FBI API → download photos → auto-register |
| **UC-09**: Body Lock Tracking | System (auto) | Recognized face lost | OSNet handoff → KCF tracker → persistent lock |
| **UC-10**: View Detection History | Operator | Navigate to Registry | Display historical detection logs with timestamps |

---
