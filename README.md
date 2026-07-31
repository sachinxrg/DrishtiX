# DrishtiX — Watchlist and Missing Person Alert System

![DrishtiX Logo](services/drishtix-app/src/main/resources/icons/logo.png)

> **Current Version**: `2.0.0-SNAPSHOT` (active development on `feature/v2.0` branch)
> **Stable Release**: `v1.0.0` (tagged on `main`)

DrishtiX is an advanced, JavaFX-based smart surveillance application designed to automatically identify registered criminals and missing persons in real-time. It leverages OpenCV (via JavaCV) for computer vision processing and maintains a clean, multi-threaded Model-View-Controller architecture.

---

## Version History & Branching

| Version | Branch | Status | Highlights |
|---------|--------|--------|------------|
| **v1.0.0** | `main` (tag: `v1.0.0`) | ✅ Stable Release | YuNet/SFace DNN pipeline, CSRT/OSNet body tracking handoff, multi-channel alerts, background ingestion, 80 tests |
| **v2.0.0-SNAPSHOT** | `feature/v2.0` | 🚧 Active Development | Next-generation features in progress |

To switch to the stable release:
```bash
git checkout v1.0.0
```

To switch to the development branch:
```bash
git checkout feature/v2.0
```

---

## Key Features
- **Real-Time DNN Identification:** YuNet face detection (~2ms) + SFace recognition (128-dim embeddings) running on a 4-thread inference pool.
- **Facial-to-Spatial Tracking Handoff:** Persistent CSRT body locks + OSNet whole-body Re-ID maintain bounding boxes when targets turn away from the camera.
- **Unified Dashboard:** High-contrast, premium dark-themed UI built with JavaFX and modern CSS, featuring live telemetry (FPS, Active Cameras, Detections).
- **Target Registry:** Database management for uploading images, categorization (Criminal / Missing Person), and metadata tracking.
- **Multi-Channel Alerts:** Simultaneous audio alarms, ControlsFX desktop toasts, and Telegram push notifications to field staff.
- **Background Ingestion Engine:** Automated FBI/CBI/TrackChild scraping with hot-injection into the live recognition gallery.
- **Reporting & Logging:** Automated detection logging, snapshot capturing, and CSV export capabilities.

## Architecture

The system operates across five strictly isolated thread pools to guarantee zero UI latency and maximum frame throughput:
1. **UI Thread (JavaFX):** Handles all visual rendering and bindings.
2. **Video Inference Pool (Cached):** Captures frames, runs YuNet detection, updates KCF/CSRT trackers.
3. **Recognition Inference Pool (Fixed=4):** Parallel SFace embedding extraction via CompletableFuture.
4. **Audio Alert Pool (Daemon):** Asynchronous sound playback and Telegram network I/O.
5. **Ingestion Pool (Scheduled, MIN_PRIORITY):** Background web scraping on configurable intervals.

## Technology Stack
- **Language:** Java 17+
- **GUI:** JavaFX 21.0.2
- **Computer Vision:** OpenCV 4.9.0 (JavaCV / Bytedeco), YuNet ONNX, SFace ONNX, OSNet ONNX
- **Database:** MongoDB 6.0+ + MongoDB Java Driver
- **Logging:** SLF4J + Logback

## Prerequisites
1. **Java 17+ JDK** installed.
2. **MongoDB 6.0+** installed and running locally on `localhost:27017`.
3. **Webcam** connected to your system (defaulting to device index 0).

## Setup & Installation

### 1. Database Configuration
Initialize the MongoDB collections and defaults using the provided mongosh script:
```bash
mongosh drishtix_db database/drishtix_init.js
```

*(Note: Default URI is `mongodb://localhost:27017`. Modify this in `src/main/resources/config.properties` if your local setup differs.)*

### 2. Build the Application
Navigate to the application directory and compile the fat JAR using the provided Maven wrapper:
```powershell
cd services/drishtix-app
.\mvnw.cmd clean package
```

### 3. Run the Application
Start the system via the shaded JAR file:
```powershell
java -jar target/drishtix-app-2.0.0-SNAPSHOT.jar
```
*(The system will automatically synthesize necessary alert sounds into `src/main/resources/sounds` upon first boot if they are missing).*

## Usage Guide
- **Settings:** Navigate to the Configuration panel to set your minimum confidence threshold, cooldown duration, and audio preferences. You can also securely wipe all system data here if needed.
- **Registry:** Go to the Registry panel to register your first target. Upload a clear, frontal face photo, set their category (Criminal/Missing), and provide identifying metadata.
- **Dashboard:** Return to the Dashboard and click **Start**. The camera feed will initialize, and any registered faces entering the frame will instantly trigger bounding boxes, visual pop-ups, and audio alerts.

