# DrishtiX — Master Blueprint

> **Version**: 4.0.0 (High-Capacity Inference & Data Sync)  
> **Architecture**: JavaFX MVC + Edge AI + Scheduled Scrapers + Python FastAPI ReID  
> **Database**: MongoDB 6.0+  
> **Build**: Maven (fat JAR)

---

## 1. Overall Architecture

**DrishtiX** is an advanced edge-native facial recognition and person tracking system designed for real-time inference on constrained local hardware. It combines hardware-accelerated DNN pipelines, multi-threaded video processing, and background scheduled web scrapers to create an autonomous, high-throughput surveillance node.

### High-Level Architecture Map

```mermaid
flowchart TD
    subgraph Presentation Layer
        UI[JavaFX UI <br/> Main, Dashboard, Settings]
        Notif[ControlsFX Desktop Notifications]
    end

    subgraph Controller Layer
        MC[MainController]
        DC[DashboardController <br/> Hero Loop & Tracking]
    end

    subgraph AI Inference 'C++ / Java'
        FP[FaceProcessingService]
        YuNet[FaceDetectorYN <br/> OpenVINO/CUDA]
        SFace[FaceRecognizerSF <br/> OpenVINO/CUDA]
        KCF[FaceTrackingManager <br/> KCF/CSRT Trackers]
    end

    subgraph Background Ingestion 'Web Scraping'
        Orch[BackgroundIngestionEngine]
        FBI[FbiWantedApiClient <br/> REST API]
        CBI[CbiWantedScraper <br/> JSoup HTML]
        TC[TrackChildScraper <br/> JSoup HTML]
    end

    subgraph Core Services
        AS[AlertService]
        ReIDSvc[ReIDService]
        TAS[TelegramAlertService]
        CS[ConfigurationService]
    end

    subgraph Microservice 'Python'
        FastAPI[ReID FastAPI Service]
        OSNet[OSNet PyTorch Model]
    end

    subgraph Data Layer 'MongoDB'
        DB[DatabaseManager]
        Mongo[(MongoDB 6.0+)]
    end

    %% Wiring
    UI --> MC --> DC
    DC --> FP & YuNet & SFace & KCF
    
    Orch --> FBI & CBI & TC
    Orch -.->|"Inject target via WriteLock"| SFace
    Orch --> Mongo
    
    FP -.->|"Person Crop Bytes"| ReIDSvc
    ReIDSvc == "HTTP POST" ==> FastAPI
    FastAPI --> OSNet
    
    DC --> AS
    AS --> Notif & TAS
    TAS == "HTTP POST" ==> TelegramAPI[(Telegram API)]
    
    Core Services & AI Inference --> DB --> Mongo
```

---

## 2. Core Subsystems

### 1. Multi-Threaded Inference Pipeline (Phase 3)
Designed to maintain 30+ FPS on UI while running heavy AI models in the background.
- **Frame-Skip Heuristic**: Full DNN inference (YuNet + SFace) runs only every Nth frame (default: every 3rd frame).
- **Parallel Embedding Extraction**: On inference frames, aligned face crops are sent to a 4-thread `CompletableFuture` pool (`RecognitionInferencePool`) for parallel SFace embedding extraction.
- **Inter-Frame Tracking**: Between inference frames, lightweight OpenCV `TrackerKCF` (or `TrackerCSRT`) interpolates face bounding boxes in <1ms via `FaceTrackingManager`.

### 2. Hardware-Native Model Acceleration (Phase 2)
The ONNX models (YuNet for detection, SFace for recognition) dynamically probe the host hardware during initialization via `DnnFaceDetectionService` and `DnnFaceRecognitionService`.
- **Priority 1**: Intel OpenVINO (iGPU/NPU target) — activated via `DNN_BACKEND_DEFAULT / DNN_TARGET_CPU` (auto-detected in OpenCV 4.9+).
- **Priority 2**: NVIDIA CUDA / TensorRT — activated via `DNN_BACKEND_CUDA`.
- **Priority 3**: Default ONNX Runtime on standard CPU fallback.

### 3. Background Ingestion Engine (Phase 1 & 4)
An autonomous, low-priority scheduled thread pool (`IngestionPool`) continuously synchronizes the local database with external watchlists without blocking the camera thread.
- **FBI REST API (`FbiWantedApiClient`)**: Parses paginated JSON data from `api.fbi.gov`.
- **CBI / TrackChild Scrapers (`CbiWantedScraper`, `TrackChildScraper`)**: Uses headless `JSoup` HTML parsing with robust multi-selector fallbacks to scrape government registries.
- **Anti-DDoS Mechanics**: Enforces a strict 2,000ms delay between all remote requests.
- **Thread-Safe Hot-Injection**: Uses `ReentrantReadWriteLock` to inject newly downloaded faces (`WantedProfile` embeddings) directly into the live camera `ConcurrentHashMap` gallery in real-time, requiring zero app restarts.

### 4. Person Re-Identification (ReID) Microservice
A standalone Python FastAPI service (`services/reid-service/main.py`) running PyTorch and `torchreid`.
- Loads the `osnet_x1_0` model to extract 512-dimensional feature embeddings from upper-body person crops.
- Java application uses `VectorMathUtil` to compute cosine similarity (>85% threshold) to track target individuals dynamically across multiple disparate camera feeds.

### 5. Multi-Channel Alert Push Engine
Orchestrated by `AlertService.triggerAlert()`, running on the `AudioAlertPool`:
- **Audio**: Plays category-specific WAV alarms (`TargetCategory.CRIMINAL` vs `MISSING_PERSON`).
- **Desktop**: Pushes non-blocking sliding toast notifications (`ControlsFX`).
- **Telegram**: Sends snapshot photo bytes + metadata via Telegram Bot API directly to field staff phones.

---

## 3. Thread Pool Architecture
The system aggressively segments workloads to prevent JavaFX UI freezing:
1. **JavaFX Application Thread**: UI rendering and bindings only.
2. **Video Inference Pool**: (CachedThreadPool) Captures camera frames, runs YuNet detection, and updates KCF trackers.
3. **Recognition Inference Pool**: (Fixed=4 Threads) Runs the heavy SFace embedding extraction in parallel `CompletableFuture` streams.
4. **Audio Alert Pool**: (Daemon) Asynchronous sound playback and Telegram network I/O.
5. **Ingestion Pool**: (Scheduled, 2 Threads, MIN_PRIORITY) Runs the web scrapers on a configurable 6-hour interval.

---

## 4. Current State & Immediate Next Steps

### Current State
- The v4.0 architecture is code-complete and fully compilable (`BUILD SUCCESS`).
- Frame skipping, hardware backend fallback, and the scheduled ingestion engine are fully integrated into `DashboardController`.
- Tracker implementation was fixed to correctly use the JavaCV `TrackerKCF` / `TrackerCSRT` APIs (using `Rect`, not `Rect2d`).

### Verification Steps
To verify the build and run the system:
1. **Compile Java App**: 
   ```bash
   cd services/drishtix-app
   ./mvnw clean compile
   ```
2. **Launch Java App**: 
   ```bash
   ./mvnw exec:java -Dexec.mainClass="com.drishtix.DrishtiXLauncher"
   ```
3. **Start Python ReID Service (Optional)**:
   ```bash
   cd services/reid-service
   uvicorn main:app --port 8100
   ```

### Known Pending Items & Future Enhancements
1. **Field Hardware Testing**: Verify OpenVINO activation logs on an Intel CPU/GPU, and verify CUDA logs on an NVIDIA machine.
2. **JSoup Anti-Scrape Evasion**: If CBI or TrackChild update their HTML layout heavily, the CSS selectors in the JSoup scrapers may need updating, though multiple fallbacks exist.
3. ~~**Dashboard Tracker UI Indicator**~~: ✅ **DONE** — Solid boxes = live DNN inference; dashed boxes with `[T]` suffix = tracker-predicted (interpolated) frames.
4. **Scraper Dashboard Settings**: Build out the settings UI panel to let users configure the scraping interval (currently stored in the database via `ConfigurationService`) instead of relying on defaults.
