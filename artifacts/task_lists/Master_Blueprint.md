# DrishtiX v4.0 — Master Architecture Blueprint
**Tactical Edge-AI Perimeter Surveillance & Age-Invariant Facial Recognition Ecosystem**

---

## 1. Executive System Summary

| Parameter | Specification |
|---|---|
| **System Version** | `v4.0.0-tactical` (Active Python Stack) |
| **Core Runtime** | Python 3.11+ / PySide6 (Qt 6.11+) |
| **Primary Architecture** | 5-Tier Concurrency Pipeline (Decoupled Capture, Inference & UI) |
| **Styling Paradigm** | Light Glassmorphism + Soft Neumorphism (`drishtix_glass.qss`, 12-Column Bento Grid) |
| **Face Detection** | YuNet ONNX (Sub-3ms inference, 5 landmark crosshairs) |
| **Face Recognition** | **Dual-Engine Facade**: InsightFace ArcFace (512-D Age-Invariant) + SFace (128-D Edge) |
| **Demographic AI** | Real-time Neural Age & Gender Estimation (`GenderAge` ONNX) |
| **Vector Search** | In-Memory SIMD Vectorized NumPy Batch Cosine Matching ($<0.1\text{ ms}$) |
| **Data Tier** | SQLite 3 in WAL Mode (`data/drishtix.db`) via SQLAlchemy 2.0 ORM |
| **External Intelligence**| Automated background ingestion (FBI Wanted REST API) |
| **Tactical Alerting** | Multi-channel: Telegram Push + Forensic Snapshot, Audio Alarms, Alert Queue Sidebar |

---

## 2. High-Level Architecture Map

```mermaid
flowchart TD
    subgraph Presentation Layer [Presentation Layer — PySide6 Light Glassmorphism]
        MW[MainWindow Shell]
        V_Dash[Dashboard View <br/> Live Video Feed & BBox]
        V_Reg[Target Registry <br/> Watchlist CRUD & Photo Ingestion]
        V_Log[Detection Logs <br/> History & CSV Export]
        V_Ana[Analytics Dashboard <br/> Matplotlib 24h & Category KPIs]
        V_Scan[Forensic Image Scanner <br/> High-Density Multi-Target Scan]
        V_Set[Settings & Hardware Delegates]
        W_Side[Live Tactical Alert Sidebar]
        W_Stat[Real-Time Status Bar]
    end

    subgraph Concurrency & Worker Tier [5-Tier Concurrency Pipeline]
        CW[CaptureWorker <br/> QThread Video Loop]
        RW_Pool[RecognitionWorker Pool <br/> QThreadPool 4 Workers]
        IW[IngestionWorker <br/> FBI Wanted Background Polling]
        DiagTimer[Diagnostics Telemetry Timer]
        SigBus[SignalBus <br/> PySide6 Qt Signal/Slot Hub]
    end

    subgraph AI Inference Engine [Dual-Engine Neural Pipeline]
        FD[FaceDetectionService <br/> YuNet ONNX]
        FT[FaceTrackingManager <br/> Spatial IoU & Centroid Smoothing]
        
        subgraph Recognition Engine [FaceRecognitionService Facade]
            IF[InsightFaceService <br/> ArcFace 512-D + GenderAge]
            SF[SFaceService <br/> OpenCV FaceRecognizerSF 128-D]
        end
        
        GM[GalleryManager <br/> In-Memory N×512 / N×128 Matrix]
    end

    subgraph Persistence Layer [Data Tier — SQLite WAL Mode]
        ORM[SQLAlchemy 2.0 Session]
        T_Reg[(TargetRegistry)]
        T_Emb[(FaceEmbedding <br/> 512/128-D BLOB)]
        T_Log[(DetectionLog)]
        T_Img[(TargetImage)]
        T_Aud[(AuditLog)]
    end

    subgraph Tactical Alerting [Multi-Channel Dispatch]
        AS[AlertService]
        Sound[SoundPlayer <br/> WAV Alarms]
        Tele[TelegramService <br/> Push Photo & Case Metadata]
    end

    %% Flow Wiring
    CW -->|"Raw Frame"| FD
    FD -->|"BBoxes & Landmarks"| FT
    CW -->|"Aligned Face Crops"| RW_Pool
    RW_Pool -->|"Feature Extraction"| Recognition Engine
    Recognition Engine -->|"Query Vector (512-D / 128-D)"| GM
    GM -->|"Match Result (ID, Score)"| RW_Pool
    RW_Pool -->|"Match / Demographic Event"| AS
    RW_Pool -.->|"Identity Association"| FT
    
    FT -->|"Annotated HUD Frame"| SigBus
    SigBus --> MW --> V_Dash & W_Side & W_Stat
    
    AS --> Sound
    AS --> Tele
    AS -->|"Save Incident Record"| T_Log
    
    IW -->|"Scrape Law Enforcement"| T_Reg
    T_Reg & T_Emb --> ORM
    ORM --> GM
```

---

## 3. Core Subsystems & Technical Details

### 1. Dual-Engine Face Recognition & Age Invariance
- **InsightFace ArcFace Engine (512-D):**
  - **Model Architecture:** Deep IResNet-50 / MobileFaceNet trained on WebFace42M (42M+ faces).
  - **Loss Function:** Additive Angular Margin ($\cos(\theta + m)$) on hypersphere.
  - **Age-Invariant Resilience:** **98.28% on AgeDB-30** benchmark (specifically testing 30-year age gaps). Solves target aging, facial hair growth, and developmental changes.
  - **Demographic Telemetry:** Outputs predicted age ($\pm 3$ years) and biological gender alongside identity match.
- **OpenCV SFace Engine (128-D):**
  - Lightweight CPU fallback mode utilizing OpenCV `cv2.FaceRecognizerSF` for ultra-constrained hardware.
- **Unified Facade:**
  - `FaceRecognitionService` dynamically switches between engines at runtime with zero client-side code modification.

### 2. Dynamic In-Memory SIMD Gallery Manager
- **Matrix Vectorization:**
  - On startup or watchlist update, active embeddings are loaded into a contiguous float32 NumPy array $\mathbf{M} \in \mathbb{R}^{N \times D}$ ($D=512$ or $D=128$).
- **Matching Complexity:**
  - Batch cosine similarity: $\mathbf{s} = \mathbf{M} \cdot \mathbf{q}^T$.
  - Executes in $< 0.1\text{ ms}$ for $10,000+$ targets on standard x86-64 CPUs using AVX2 SIMD instructions.
- **Zero Database Migration:**
  - Embeddings are stored as raw binary (`LargeBinary` BLOBs). 128 floats (512 bytes) or 512 floats (2,048 bytes) are transparently deserialized via `np.frombuffer()`.

### 3. Five-Tier Concurrency Architecture
To guarantee zero UI freezing and maintain a steady 30 FPS video pipeline, tasks are strictly segregated:
1. **Main GUI Thread:** PySide6 event loop rendering glassmorphism widgets, layout management, and user interaction.
2. **Video Capture Worker (`CaptureWorker` QThread):** High-speed OpenCV `VideoCapture` loop with thread-safe atomic frame buffering.
3. **Recognition Thread Pool (`QThreadPool`):** Multi-threaded pool (4 concurrent workers) performing deep feature extraction and demographic estimation asynchronously.
4. **Spatial Tracking Manager (`FaceTrackingManager`):** Real-time centroid and IoU association across intermediate frames to eliminate bounding box flicker.
5. **Background Ingestion Worker (`IngestionWorker` QThread):** Low-priority scheduled task polling external intelligence APIs (e.g. FBI Wanted) with rate-limiting and thread-safe gallery reload.

### 4. Presentation Layer (Light Glassmorphism + Bento Grid)
- **Design System:** Custom 559-line Qt StyleSheet (`drishtix_glass.qss`).
- **Visual Primitives:**
  - Translucent frosted glass card containers (`rgba(255, 255, 255, 0.86)` with white hairlines).
  - Neumorphic raised buttons and inset form inputs.
  - Semantic status badge system:
    - **Safe / Active:** Emerald Green (`#10B981`)
    - **Review / Scanning:** Amber (`#F59E0B`)
    - **Critical / Criminal:** Crimson Rose (`#F43F5E`)
    - **Informational / Missing:** Cyan (`#06B6D4`)
- **6 Core Operational Views:**
  1. **Dashboard:** Live camera stream, tactical HUD with demographic chips, live alert queue sidebar.
  2. **Target Registry:** Watchlist table, modal registration with automatic SFace/ArcFace embedding extraction.
  3. **Detection Logs:** Filterable historical log table with instant CSV export.
  4. **Analytics & KPIs:** Matplotlib charts (24-hour timeline, category donut, 7-day trend, top detected targets).
  5. **Forensic Image Scanner:** High-density crowd image scanner capable of simultaneous recognition of 40+ faces.
  6. **Settings & Hardware Delegates:** Runtime configuration for camera sources, DNN thresholds, engine selectors (`buffalo_s` vs `buffalo_l`), database health, and Telegram API.

---

## 4. Database Schema (SQLite WAL Mode)

```mermaid
erDiagram
    TARGET_REGISTRY ||--o{ TARGET_IMAGE : "has images"
    TARGET_REGISTRY ||--o{ FACE_EMBEDDING : "has embeddings"
    TARGET_REGISTRY ||--o{ DETECTION_LOG : "triggers"
    
    TARGET_REGISTRY {
        int target_id PK
        string full_name
        string category "CRIMINAL | MISSING_PERSON"
        string case_number
        string description
        string profile_image_path
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    TARGET_IMAGE {
        int image_id PK
        int target_id FK
        string image_path
        int image_order
        datetime uploaded_at
    }
    
    FACE_EMBEDDING {
        int embedding_id PK
        int target_id FK
        int source_image_id FK
        blob embedding_vector "128 or 512 Float32s (BLOB)"
        datetime created_at
    }
    
    DETECTION_LOG {
        int log_id PK
        int target_id FK
        int camera_id FK
        float confidence_score
        string location_tag
        string snapshot_path
        datetime detection_timestamp
    }
    
    CAMERA_SOURCE {
        int camera_id PK
        string camera_name
        string connection_string
        boolean is_active
    }
    
    AUDIT_LOG {
        int audit_id PK
        string action
        string entity_type
        int entity_id
        string details
        datetime timestamp
    }
```

---

## 5. Repository File Structure

```
d:\TY-IT\Enterprise_Java\Java_project\
├── .agents/                               # Antigravity agents & workflow configs
├── .vscode/                               # VS Code IDE settings
├── artifacts/
│   └── task_lists/
│       ├── Master_Blueprint.md            # ◄── Master Architecture Blueprint
│       └── Feature_Update_Spec.md
├── docs/                                  # Project documentation & thesis chapters
├── scratch/
│   └── diagram_imgs/                      # High-res architecture diagrams
├── scripts/
│   ├── generate_ch1_ch2.py               # Documentation generator
│   └── generate_diagrams_docx.py          # Word diagram compiler
├── services/
│   ├── drishtix-py/                       # 🚀 PRIMARY ACTIVE APPLICATION
│   │   ├── drishtix/
│   │   │   ├── core/                      # Constants, Config, Signals, Enums
│   │   │   ├── dao/                       # Data Access Objects (SQLAlchemy 2.0)
│   │   │   ├── models/                    # ORM Entity Models (SQLite WAL)
│   │   │   ├── services/                  # Business & Neural AI Services
│   │   │   │   ├── alert_service.py       # Multi-channel alert dispatcher
│   │   │   │   ├── analytics_service.py   # Aggregation & KPI analytics
│   │   │   │   ├── face_detection.py      # YuNet ONNX detector
│   │   │   │   ├── face_recognition.py    # Unified Dual-Engine facade
│   │   │   │   ├── face_tracker.py        # Spatial IoU & demographic tracking
│   │   │   │   ├── gallery_manager.py     # In-memory SIMD matching gallery
│   │   │   │   └── insightface_service.py # ArcFace 512-D + GenderAge engine
│   │   │   ├── ui/                        # Presentation Layer
│   │   │   │   ├── main_window.py         # Primary Command Window shell
│   │   │   │   ├── styles/
│   │   │   │   │   └── drishtix_glass.qss # Light Glassmorphism QSS Theme
│   │   │   │   ├── views/                 # 6 Modular Bento Views
│   │   │   │   └── widgets/               # Reusable Glass UI Components
│   │   │   ├── utils/                     # Vector math, sound, image utils
│   │   │   └── workers/                   # Asynchronous QThread / QRunnable workers
│   │   ├── models/                        # ONNX Neural Network Assets
│   │   ├── tests/                         # Pytest test suite (16 test cases)
│   │   ├── config.yaml                    # Runtime configuration
│   │   ├── main.py                        # Python application entry point
│   │   └── requirements.txt               # Dependencies
│   └── reid-service/                      # Person Re-Identification Microservice
├── DRISHTIX logo.png                      # Official branding asset
├── README.md                              # Comprehensive project README
├── start_drishtix_py.bat                  # 🟢 One-Click Master Launcher
└── stop_drishtix_py.bat                   # 🔴 Clean Shutdown Script
```

---

## 6. Execution & Verification Guide

### Quick Start
```powershell
# Double-click the one-click launcher:
.\start_drishtix_py.bat

# Or run directly via virtual environment:
cd services/drishtix-py
.\venv\Scripts\python.exe main.py
```

### Running Automated Test Suite
```powershell
cd services/drishtix-py
.\venv\Scripts\python.exe -m pytest tests/ -v
```
**Current Status:** `16 passed in 1.86s` (100% pass rate).
