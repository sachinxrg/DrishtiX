# DrishtiX v3.0 — Repository-Accurate Architectural Diagrams

> All diagrams are based on a complete scan of the DrishtiX repository at `d:\TY-IT\Enterprise_Java\Java_project\services\drishtix-app\`.
> Every class name, method call, thread pool name, and collection field is traced directly to source code.

---

## 1. System Flowchart — Video Capture to UI Alert

> Source files: `DashboardController.java`, `DnnFaceDetectionService.java`, `DnnFaceRecognitionService.java`, `AlertService.java`

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontSize": "24px", "fontFamily": "arial", "nodePadding": 15}}}%%
flowchart TD
    A["OpenCVFrameGrabber.grab()"] -->|"Frame object"| B["converter.convert(frame) → Mat"]
    B --> C{"configService.isDnnMode()?"}

    C -->|"DNN Mode"| D["processFrameDnn(mat)"]
    C -->|"Legacy Mode"| E["processFrameLbph(mat)"]

    D --> F["DnnFaceDetectionService.detectFaces(mat)<br/>YuNet ONNX ~2ms<br/>Up to DNN_MAX_FACES=200"]
    F --> G["FaceProcessingService.alignFaceForDnn()<br/>Crop 112×112 BGR"]
    G --> H["alignedFace.clone()"]
    H --> I["CompletableFuture.supplyAsync()<br/>→ RecognitionInferencePool (4 threads)"]
    I --> J["DnnFaceRecognitionService.predictDnn()<br/>extractEmbedding() → 128-dim float[]<br/>matchAgainstGallery() → cosine similarity"]
    J --> K{".thenAcceptAsync()<br/>→ VideoInferencePool"}
    K --> L["handleRecognitionResult()"]
    L --> M{"result.isMatched()?"}
    M -->|"Yes: similarity ≥ 0.363"| N["AlertService.triggerAlert()"]
    M -->|"No"| O["drawBoundingBox()<br/>COLOR_UNKNOWN_BGR"]

    N --> P["shouldAlert(targetId)?<br/>ConcurrentHashMap cooldown check"]
    P -->|"Cooldown Active"| Q["Alert Suppressed (DEBUG log)"]
    P -->|"Cooldown Expired"| R["4 Parallel Alert Channels"]

    R --> S1["Channel 1: playSound(category)<br/>AudioAlertPool (1 thread)"]
    R --> S2["Channel 2: NotificationService<br/>.showDetectionAlert()<br/>Platform.runLater() toast"]
    R --> S3["Channel 3: TelegramAlertService<br/>.sendDetectionAlert()<br/>AudioAlertPool (async I/O)"]
    R --> S4["Channel 4: EmailAlertService<br/>.sendOfficerDispatchEmail()<br/>AudioAlertPool (async I/O)"]

    L --> T["drawBoundingBox(frame, rect)<br/>Semi-transparent dark label bg<br/>WCAG AA compliant"]
    T --> U["Platform.runLater()<br/>cameraFeed.setImage()"]
    U --> V["refreshStats()<br/>IntegerProperty bindings update"]

    E --> W["FaceProcessingService.detectFaces()<br/>Haar Cascade + Histogram Eq"]
    W --> X["extractFaceROI() → 200×200 Gray"]
    X --> Y["RecognitionService.predict()<br/>LBPH distance-based matching"]
    Y --> L
```

---

## 2. ER Diagram — MongoDB Schema

> Source files: `drishtix_init.js`, `TargetDAO.java`, `DetectionLogDAO.java`, `PersonEmbeddingDAO.java`

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontSize": "24px", "fontFamily": "arial", "nodePadding": 15}}}%%
erDiagram
    targets ||--o{ target_images : "has_photos (1..5)"
    targets ||--o{ detection_logs : "triggers_alerts"
    targets ||--o{ person_embeddings : "reid_vectors"
    targets ||--o{ audit_log : "audits_changes"
    camera_sources ||--o{ detection_logs : "captures_on"
    camera_sources ||--o{ person_embeddings : "source_camera"
    counters ||--|| targets : "auto_increment"
    counters ||--|| target_images : "auto_increment"
    counters ||--|| detection_logs : "auto_increment"
    counters ||--|| audit_log : "auto_increment"
    counters ||--|| person_embeddings : "auto_increment"

    targets {
        int _id PK "Auto-increment via counters"
        string full_name "NOT NULL, Text Index"
        string category "CRIMINAL | MISSING_PERSON"
        string case_number "UNIQUE Index"
        string description "Text Index"
        string profile_image_path "NOT NULL"
        boolean is_active "Default true, Index"
        int recognizer_label "UNIQUE Index"
        date created_at
        date updated_at
    }

    target_images {
        int _id PK "Auto-increment via counters"
        int target_id FK "Index"
        string image_path "Original upload path"
        string template_path "200x200 grayscale ROI"
        int image_order "1-5"
        date uploaded_at
    }

    camera_sources {
        int _id PK
        string camera_name
        string source_uri "Device index or RTSP URL"
        boolean is_active "Index"
        date created_at
    }

    detection_logs {
        long _id PK "Auto-increment via counters"
        int target_id FK "Index"
        date detection_timestamp "Descending Index"
        double match_confidence_score "Index"
        string snapshot_path
        int camera_id FK "Index"
        string location_tag
        date created_at
    }

    alert_config {
        string config_key "UNIQUE Index"
        string config_value
        string description
        date updated_at
    }

    audit_log {
        long _id PK "Auto-increment via counters"
        string action_type "Index"
        int target_id "Nullable"
        string performed_by "Default SYSTEM"
        string details "JSON-serialized"
        date performed_at "Descending Index"
    }

    person_embeddings {
        long _id PK "Auto-increment via counters"
        int target_id FK "Index, Nullable"
        int camera_id "Index"
        array embedding "512-dim double array"
        string snapshot_path
        date timestamp "Descending Index"
    }

    counters {
        string _id PK "Collection name"
        int seq "Current sequence value"
    }
```

---

## 3. Table Design — Complete Field Specifications

### Collection: `targets`

| Field | BSON Type | Constraint | Index | Source: `TargetDAO.mapDocument()` |
|-------|-----------|-----------|-------|----------------------------------|
| `_id` | Integer | PK (auto-increment via `counters`) | Primary | `doc.getInteger("_id")` |
| `full_name` | String | NOT NULL | Text Index (compound with `description`) | `doc.getString("full_name")` |
| `category` | String | Enum: `"CRIMINAL"`, `"MISSING_PERSON"` | Secondary | `TargetCategory.fromDbValue(doc.getString("category"))` |
| `case_number` | String | UNIQUE | Unique Index | `doc.getString("case_number")` |
| `description` | String | Nullable | Text Index (compound) | `doc.getString("description")` |
| `profile_image_path` | String | NOT NULL | — | `doc.getString("profile_image_path")` |
| `is_active` | Boolean | Default: `true` | Secondary | `doc.getBoolean("is_active", true)` |
| `recognizer_label` | Integer | UNIQUE | Unique Index | `doc.getInteger("recognizer_label", 0)` |
| `created_at` | Date | Auto-populated | — | `doc.getDate("created_at")` |
| `updated_at` | Date | Auto-populated | — | `doc.getDate("updated_at")` |

### Collection: `target_images`

| Field | BSON Type | Constraint | Index | Source: `TargetImageDAO` |
|-------|-----------|-----------|-------|--------------------------|
| `_id` | Integer | PK (auto-increment) | Primary | Auto-generated |
| `target_id` | Integer | FK → `targets._id` | Secondary | Application-managed cascade |
| `image_path` | String | NOT NULL | — | Original uploaded image |
| `template_path` | String | NOT NULL | — | 200×200 grayscale ROI |
| `image_order` | Integer | Range: 1–5 | — | `MAX_PHOTOS_PER_TARGET = 5` |
| `uploaded_at` | Date | Auto-populated | — | |

### Collection: `detection_logs`

| Field | BSON Type | Constraint | Index | Source: `DetectionLogDAO` |
|-------|-----------|-----------|-------|--------------------------|
| `_id` | Long | PK (auto-increment) | Primary | `getNextSequenceLong("detection_logs")` |
| `target_id` | Integer | FK → `targets._id` | Secondary | |
| `detection_timestamp` | Date | NOT NULL | Descending | Sorted newest-first |
| `match_confidence_score` | Double | NOT NULL | Secondary | LBPH distance or cosine similarity |
| `snapshot_path` | String | Nullable | — | Annotated frame PNG |
| `camera_id` | Integer | FK → `camera_sources._id` | Secondary | |
| `location_tag` | String | Nullable | — | Optional geolocation |
| `created_at` | Date | Auto-populated | — | |

---

## 4. Process Flow — Background Ingestion Engine

> Source: `BackgroundIngestionEngine.java`, `FbiWantedApiClient.java`, `CbiWantedScraper.java`, `TrackChildScraper.java`

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontSize": "26px", "fontFamily": "arial", "nodePadding": 18}}}%%
flowchart LR
    subgraph ENGINE["1. Master Scheduler (BackgroundIngestionEngine)"]
        direction TB
        START(["start()<br/>IngestionPool: 2 threads, MIN_PRIORITY"])
        DELAY["Initial Delay: 60 Seconds<br/>(Wait for UI & Camera Initialization)"]
        CYCLE["runIngestionCycle()<br/>scheduleAtFixedRate(Interval: 6 Hours)"]
        LOG["Log Cycle Summary:<br/>Total Profiles Ingested & Elapsed Seconds"]
        
        START --> DELAY --> CYCLE
        CYCLE -.->|"Cycle Complete"| LOG
        LOG -.->|"Wait 6 Hours"| CYCLE
    end

    subgraph SOURCES["2. Multi-Source Ingestion Sequence"]
        direction TB
        subgraph SRC1["FBI Wanted API"]
            FBI["FbiWantedApiClient.fetchWantedProfiles()<br/>REST API: api.fbi.gov/wanted/v1/list"]
        end
        subgraph SRC2["CBI Most Wanted"]
            CBI["CbiWantedScraper.scrapeWantedProfiles()<br/>HTML Scrape: cbi.gov.in/wanted-persons"]
        end
        subgraph SRC3["TrackChild Missing Children"]
            TC["TrackChildScraper.scrapeMissingChildren()<br/>HTML Scrape: trackthemissingchild.gov.in"]
        end

        FBI -->|"2000ms Rate Limit Pause"| CBI
        CBI -->|"2000ms Rate Limit Pause"| TC
    end

    subgraph PIPELINE["3. Per-Profile Processing Pipeline (processProfiles)"]
        direction TB
        DEDUP{"1. External ID Check:<br/>processedExternalIds.contains()?"}
        VAL_IMG{"2. Local Image Check:<br/>imagePath exists?"}
        
        subgraph AI_VAL["3. Face Validation & Feature Extraction"]
            direction TB
            SCALE["a. imread() & Scale Image to Max 640px Width"]
            YUNET["b. YuNet FaceDetectorYN.detectFaces()"]
            SFACE["c. alignFaceForDnn() & SFace 128-dim Embedding"]
            SCALE --> YUNET --> SFACE
        end
        
        SUB_REG["4. MongoDB Target Registration<br/>TargetDAO.insert() & TargetImageDAO.insert()"]
        INJECT["5. Live Gallery Embedding Injection<br/>DnnFaceRecognitionService.injectEmbedding()"]
        MARK["6. Mark ID as Processed<br/>processedExternalIds.add(externalId)"]
        
        DEDUP -->|"New Profile"| VAL_IMG
        VAL_IMG -->|"Image Found"| SCALE
        SFACE -->|"Face Verified"| SUB_REG
        SUB_REG --> INJECT --> MARK
        
        DEDUP -->|"Already Ingested"| SKIP1["Skip Profile"]
        VAL_IMG -->|"Image Missing"| SKIP2["Skip Profile"]
        YUNET -->|"No Face Found"| SKIP3["Skip Profile"]
    end

    CYCLE --> FBI
    SRC1 -->|"List<WantedProfile>"| PIPELINE
    SRC2 -->|"List<WantedProfile>"| PIPELINE
    SRC3 -->|"List<WantedProfile>"| PIPELINE
    MARK -.->|"Next Profile"| DEDUP
```

---

## 5. DFD Level 0 — Context Diagram

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontSize": "24px", "fontFamily": "arial", "nodePadding": 15}}}%%
flowchart TD
    subgraph EXTERNAL_ENTITIES["External Entities & System Interfaces"]
        OP["Operator / Security Personnel"]
        CAM["CCTV Cameras (USB / RTSP)"]
        IO["Investigating Officer"]
        TG["Telegram Bot API"]
        EM["Email SMTP Server"]
        FBI["FBI Wanted API"]
        CBI["CBI Most Wanted Portal"]
        TCH["TrackChild Missing Children"]
        REID["ReID Microservice (OSNet)"]
    end

    subgraph DATA_STORAGE["Data Store"]
        DB[("MongoDB 6.0 Database")]
    end

    DX(("0.0 DrishtiX v3.0<br/>Facial Recognition<br/>& Alert System"))

    OP -->|"Target Photos & Watchlist Entries<br/>Configuration Parameters<br/>Alert Acknowledgments"| DX
    DX -->|"Live Annotated Video Feed<br/>Real-Time Alert Toasts<br/>System Metrics & Status"| OP

    CAM -->|"Raw Video Stream (USB/RTSP @ 15-30 FPS)"| DX

    DX -->|"Persist Target Records, Logs,<br/>Audit Trails & Embeddings"| DB
    DB -->|"Load Target Profiles, Gallery Embeddings,<br/>Alert Configs & Camera Sources"| DX

    DX -->|"Photo & Metadata Alert Messages"| TG
    DX -->|"Officer Dispatch Email Alerts"| EM

    FBI -->|"REST JSON Wanted Profiles"| DX
    CBI -->|"Scraped HTML Suspect Records"| DX
    TCH -->|"Scraped HTML Missing Children Records"| DX

    DX -->|"Person Bounding Box Crops"| REID
    REID -->|"512-dim OSNet Body Embeddings"| DX

    IO -->|"Log Search Queries & Date Filters"| DX
    DX -->|"Exported CSV Evidence Files & Snapshots"| IO
```

---

## 6. DFD Level 1 — Module Decomposition

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontSize": "24px", "fontFamily": "arial", "nodePadding": 15}}}%%
flowchart TB
    subgraph UI_LAYER["UI / Presentation Layer (JavaFX)"]
        P1["1.0 Main View & Navigation<br/>(MainController)"]
        P2["2.0 Live Dashboard & Feed<br/>(DashboardController)"]
        P3["3.0 Target Registry Management<br/>(RegistryController)"]
        P4["4.0 Detection Logs & Export<br/>(DetectionLogController)"]
    end

    subgraph ENGINE_LAYER["Core Vision & Intelligence Engines"]
        P5["5.0 Face Detection Engine<br/>(DnnFaceDetectionService / YuNet)"]
        P6["6.0 Face Recognition Engine<br/>(DnnFaceRecognitionService / SFace)"]
        P7["7.0 Body Lock & Tracking<br/>(FaceTrackingManager / OSNet)"]
        P8["8.0 Multi-Channel Alert Engine<br/>(AlertService)"]
        P9["9.0 Background Ingestion Engine<br/>(BackgroundIngestionEngine)"]
    end

    subgraph DATA_LAYER["Data Access & Storage Layer"]
        D1[("D1: targets")]
        D2[("D2: target_images")]
        D3[("D3: detection_logs")]
        D4[("D4: alert_config")]
        D5[("D5: person_embeddings")]
    end

    P2 <--> P5
    P5 --> P6
    P6 <--> P7
    P6 --> P8
    P8 --> D3
    P8 --> D4
    P3 <--> D1
    P3 <--> D2
    P4 <--> D3
    P9 --> D1
    P9 --> D2
    P9 --> P6
```

---

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontSize": "26px", "fontFamily": "arial", "nodePadding": 18}}}%%
flowchart LR
    subgraph POOL2["Pool 2: Video Inference (2 Threads, Daemon)"]
        direction TB
        VI1["1. OpenCVFrameGrabber.grab()<br/>Capture RTSP/USB Frame"]
        VI2["2. DnnFaceDetectionService.detectFaces()<br/>YuNet ONNX Detection (~2ms)"]
        VI3["3. FaceProcessingService.alignFaceForDnn()<br/>Crop & Align 112×112 BGR"]
        VI4["4. drawBoundingBox() & putText()<br/>Annotate Frame with WCAG Label"]
        VI5["5. imwrite() Snapshot to Disk"]
        VI6["6. DetectionLogService.logDetection()"]
        
        VI1 --> VI2 --> VI3
        VI4 --> VI5 --> VI6
    end

    subgraph POOL3["Pool 3: Recognition Inference (4 Threads, Daemon)"]
        direction TB
        RI1["1. extractEmbedding()<br/>SFace 128-dim Float Vector<br/>(ThreadLocal Model Instance)"]
        RI2["2. matchAgainstGallery()<br/>ConcurrentHashMap Gallery<br/>(ReentrantReadWriteLock)"]
        RI3["3. VectorMathUtil.cosineSimilarity()<br/>Match Threshold ≥ 0.363"]
        
        RI1 --> RI2 --> RI3
    end

    subgraph POOL1["Pool 1: JavaFX Application Thread (1 Thread)"]
        direction TB
        UI1["1. cameraFeed.setImage(frame)<br/>Update 70% Viewport"]
        UI2["2. alertQueueBox.getChildren().add(0, card)<br/>Prepend Alert (Cap: 50)"]
        UI3["3. IntegerProperty.set()<br/>Reactive Stat Bindings"]
        UI4["4. Notifications.create().show()<br/>ControlsFX Sliding Toast"]
        
        UI1 --> UI2 --> UI3 --> UI4
    end

    subgraph POOL4["Pool 4: Audio & Push Alert (1 Thread, Daemon)"]
        direction TB
        AA1["1. AlertService.playSound()<br/>Category WAV Playback"]
        AA2["2. TelegramAlertService.send()<br/>HTTP POST Snapshot Photo"]
        AA3["3. EmailAlertService.send()<br/>SMTP Officer Dispatch"]
        
        AA1 --> AA2 --> AA3
    end

    subgraph BACKGROUND["Background Auxiliary Pools"]
        direction TB
        subgraph POOL5["Pool 5: Ingestion Pool (2 Threads, MIN_PRIORITY)"]
            IG1["BackgroundIngestionEngine<br/>FBI API + CBI + TrackChild Sync"]
        end
        subgraph POOL6["Pool 6: Scheduled Pool (1 Thread)"]
            SC1["Periodic Snapshot Purge (90 Days)<br/>Configuration Refresh"]
        end
    end

    VI3 -->|"Async Handoff:<br/>CompletableFuture.supplyAsync()"| RI1
    RI3 -->|"Result Callback:<br/>.thenAcceptAsync()"| VI4

    VI4 -->|"Platform.runLater()"| UI1
    VI6 -->|"Async Push:<br/>CompletableFuture.runAsync()"| AA1

    IG1 -->|"Inject Embedding"| RI2
```
