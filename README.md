# DrishtiX — Watchlist and Missing Person Alert System

![DrishtiX Logo](services/drishtix-app/src/main/resources/icons/logo.png)

DrishtiX is an advanced, JavaFX-based smart surveillance application designed to automatically identify registered criminals and missing persons in real-time. It leverages OpenCV (via JavaCV) for computer vision processing and maintains a clean, multi-threaded Model-View-Controller architecture.

## Key Features
- **Real-Time Identification:** Captures live webcam feeds and matches detected faces against a trained LBPH recognizer.
- **Unified Dashboard:** High-contrast, premium dark-themed UI built with JavaFX and modern CSS, featuring live telemetry (FPS, Active Cameras, Detections).
- **Target Registry:** Database management for uploading images, categorization (Criminal / Missing Person), and metadata tracking.
- **Asynchronous Audio Alerts:** Configurable, non-blocking audio alerts (Siren for criminals, Chimes for missing persons) with cooldown mechanics.
- **Reporting & Logging:** Automated detection logging, snapshot capturing, and CSV export capabilities.

## Architecture

The system operates across three strictly isolated thread pools to guarantee zero UI latency and maximum frame throughput:
1. **UI Thread (JavaFX):** Handles all visual rendering and pop-up overlays.
2. **Video Inference Thread:** Orchestrates the `OpenCVFrameGrabber`, Haar cascade face detection, and LBPH model prediction.
3. **Audio Alert Thread:** Dedicated to asynchronous WAV playback, preventing audio loading/playing from stalling the video feed.

## Technology Stack
- **Language:** Java 17+
- **GUI:** JavaFX 17
- **Computer Vision:** OpenCV (JavaCV / Bytedeco Wrappers)
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
java -jar target/drishtix-app-1.0.0.jar
```
*(The system will automatically synthesize necessary alert sounds into `src/main/resources/sounds` upon first boot if they are missing).*

## Usage Guide
- **Settings:** Navigate to the Configuration panel to set your minimum confidence threshold, cooldown duration, and audio preferences. You can also securely wipe all system data here if needed.
- **Registry:** Go to the Registry panel to register your first target. Upload a clear, frontal face photo, set their category (Criminal/Missing), and provide identifying metadata.
- **Dashboard:** Return to the Dashboard and click **Start**. The camera feed will initialize, and any registered faces entering the frame will instantly trigger bounding boxes, visual pop-ups, and audio alerts.
