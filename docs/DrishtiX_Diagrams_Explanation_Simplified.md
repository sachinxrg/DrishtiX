# DrishtiX v3.0 — Architectural Diagrams Explained Simply

> A plain-language guide to understanding all 7 system diagrams for DrishtiX v3.0.
> Written for non-technical stakeholders, law enforcement officers, and project managers.

---

## 1. System Flowchart (Video Capture to UI Alert)

### 💡 In Plain Terms
This diagram shows the complete step-by-step journey of a single video frame: from the exact millisecond the camera records a person to when an alert pops up on the screen and sends a photo to an officer's phone.

### 🔄 How Data Flows
1. **Camera Capture**: The camera captures a frame from the live video stream.
2. **AI Engine Selection**: The system checks if it is running in modern **DNN Mode** (YuNet + SFace) or legacy **Haar Mode**.
3. **Face Detection (YuNet)**: The YuNet AI scans the photo in ~2 milliseconds, finds all faces (up to 200 per frame), and crops each face into a standardized 112×112 pixel box.
4. **Facial Fingerprinting (SFace)**: The cropped face is passed asynchronously to background AI threads. The SFace model extracts a **128-number mathematical fingerprint** representing facial geometry (eye spacing, nose angle, jawline).
5. **Gallery Comparison**: The fingerprint is compared against all registered suspects in memory using **cosine similarity**.
6. **Match Check**: If similarity is **≥ 36.3%**, a positive match is declared.
7. **Cooldown Check**: The system checks if an alert for this target was already sent in the last 30 seconds. If yes, it suppresses the duplicate alert to prevent operator alert fatigue.
8. **4-Channel Push Alert**: If cooldown has expired, 4 parallel channels trigger instantly:
   - 🔊 **Audio Alarm**: Plays a category-specific WAV sound.
   - 💻 **Desktop Toast**: Slides a notification onto the screen.
   - 📱 **Telegram Bot**: Sends a direct message with target details & snapshot photo to officers.
   - 📧 **Email Dispatch**: Sends an email report for legal logging.
9. **UI Drawing**: Draws a colored box around the suspect on screen (Red = Criminal, Blue = Missing Person, Green = Civilian) with high-contrast, readable text labels.

---

## 2. ER Diagram (MongoDB Database Structure)

### 💡 In Plain Terms
This is the database blueprint — a visual map showing how all 8 data tables (MongoDB collections) store information and connect to one another.

### 🔗 Key Data Relationships
- **`targets` (The Master Watchlist)**: Stores profile information for wanted suspects and missing persons (Name, FIR number, category, primary photo).
  - One target can have up to 5 reference photos stored in **`target_images`** (helps AI recognize them from different angles).
  - Every time a target is spotted on camera, a record is added to **`detection_logs`**.
  - Their AI facial and body vectors are stored in **`person_embeddings`**.
  - Any administrative changes (added, updated, deactivated, deleted) are logged in **`audit_log`**.
- **`camera_sources`**: Stores registered CCTV camera locations and stream URLs, linked directly to detection logs.
- **`counters`**: Automatically generates sequential primary key numbers (1, 2, 3...) for new records.

---

## 3. Table Design Specifications

### 💡 In Plain Terms
This table gives the exact technical specifications for every field in the database — what kind of data it holds, whether it is required, and how it is used.

### 📋 Highlights
- **`targets`**: Stores `full_name`, `category` (`CRIMINAL` or `MISSING_PERSON`), `case_number` (unique FIR ID), `profile_image_path`, and `is_active` status.
- **`target_images`**: Manages multi-photo enrollment (1 to 5 images per target).
- **`detection_logs`**: Stores the exact match timestamp, confidence score percentage, source camera ID, and path to the saved visual frame snapshot.
- **`alert_config`**: Contains all system configuration key-values (confidence thresholds, cooldown durations, video FPS targets, and notification toggles).

---

## 4. Process Flow (Background Ingestion Engine)

### 💡 In Plain Terms
This diagram explains how DrishtiX automatically fetches new wanted criminal profiles and missing children reports from official government databases without any human manual work.

### 🔄 How Automated Sync Works
1. **Startup Delay**: Waits 60 seconds after application launch to ensure the live camera feed and UI initialize smoothly first.
2. **Scheduled Cycle**: Executes automatically every **6 hours** (configurable).
3. **Source 1 — FBI API**: Queries `api.fbi.gov` via REST JSON requests for international wanted profiles.
4. **Source 2 — CBI Portal**: Scrapes `cbi.gov.in` for national most-wanted suspects.
5. **Source 3 — TrackChild Portal**: Scrapes `trackthemissingchild.gov.in` for missing children records.
6. **Face Validation & Ingestion**:
   - For every scraped photo, YuNet verifies that a human face is present.
   - SFace extracts the 128-dim embedding fingerprint.
   - The target is saved to MongoDB and immediately injected into the live camera recognition gallery in memory — meaning the camera can spot them right away without restarting the system.

---

## 5. Data Flow Diagram (DFD Level 0 — Context Diagram)

### 💡 In Plain Terms
The 30,000-foot view showing DrishtiX in the center and every external person, hardware device, database, and cloud service that talks to it.

### 🌐 System Boundaries & Connections
- **Surveillance Operator**: Inputs target photos, adjusts confidence thresholds, and reviews live alerts.
- **CCTV Cameras**: Streams raw 1080p–4K video frames over RTSP/USB.
- **MongoDB Database**: Persists targets, camera configs, detection history, and audit trails.
- **Telegram & Email**: Receives instant push notifications for field officers.
- **Government Portals (FBI, CBI, TrackChild)**: Feeds official wanted and missing person data.
- **Python ReID Service**: Provides cross-camera body tracking across different camera angles.
- **Investigating Officer**: Searches historical logs and exports RFC 4180-compliant CSV evidence files for court filings.

---

## 6. Data Flow Diagram (DFD Level 1 — Module Architecture)

### 💡 In Plain Terms
Opening up the main DrishtiX application to show how code is divided into 3 major layers: UI (what you see), Vision Engines (the AI brains), and Data Access (database storage).

### 🧩 Module Hierarchy
1. **UI Layer (Presentation)**:
   - `MainController`: Navigation between views.
   - `DashboardController`: Hero screen displaying live feed, alert queue, and reactive stats.
   - `RegistryController`: Suspect profile creation, editing, and photo management.
   - `DetectionLogController`: Historical search, date filtering, and CSV export.
2. **Vision & Intelligence Engines**:
   - `DnnFaceDetectionService`: YuNet ONNX face detection (~2ms).
   - `DnnFaceRecognitionService`: SFace ONNX facial fingerprint extraction & gallery matching.
   - `FaceTrackingManager`: KCF/CSRT body-lock tracking via OSNet.
   - `AlertService`: 4-channel alert orchestration.
   - `BackgroundIngestionEngine`: Government portal synchronization.
3. **Data Layer**:
   - DAO classes managing CRUD operations on MongoDB collections.

---

## 7. Data Flow Diagram (DFD Level 2 — Multi-Threaded AI Pipeline)

### 💡 In Plain Terms
A deep technical look at how DrishtiX uses **6 separate thread pools** working simultaneously in parallel so that heavy AI calculations never cause the live camera feed to freeze or drop frames.

### ⚡ The 6 Thread Pools Explained

| Pool | Threads | Primary Responsibility | Why It Needs Its Own Pool |
|------|---------|------------------------|---------------------------|
| **Pool 1: JavaFX UI Thread** | 1 | Renders camera feed, animates alert queue cards, updates stat counters. | JavaFX is single-threaded; background threads must use `Platform.runLater()` to update UI safely. |
| **Pool 2: Video Inference Pool** | 2 | Frame capture (`OpenCVFrameGrabber`), YuNet face detection (~2ms), frame annotation, snapshot disk writes. | Keeps camera capture running smoothly at 15–30 FPS without waiting for face recognition to complete. |
| **Pool 3: Recognition Inference Pool** | 4 | SFace 128-dim embedding extraction & cosine similarity matching against 10,000+ targets. | SFace takes ~35ms per face on CPU. Running on 4 dedicated threads allows processing multiple faces in parallel. |
| **Pool 4: Audio Alert Pool** | 1 | WAV sound playback (`javax.sound.sampled`), Telegram HTTP requests, Email SMTP sending. | Sound playback and network I/O take time. Running on a separate thread ensures network delays never slow down video capture. |
| **Pool 5: Background Ingestion Pool** | 2 | Scheduled web scraping and REST API requests (FBI/CBI/TrackChild). | Set to `MIN_PRIORITY` so background downloading never steals CPU power from live video scanning. |
| **Pool 6: Scheduled Pool** | 1 | Periodic disk cleanup (purging old 90-day snapshots) and configuration refresh. | Offloads administrative maintenance tasks. |

---

*Summary prepared for DrishtiX v3.0 Architecture Documentation.*
