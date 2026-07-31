# DrishtiX — Feature Update Spec v2.0

> **Date**: 2026-07-20  
> **Status**: PENDING APPROVAL  
> **Baseline**: Master Blueprint v1.2.0 (JavaFX MVC + MongoDB + OpenCV/JavaCV)

---

## Feature 1: Multi-Camera Person Re-Identification (ReID)

### Problem Statement
The current DrishtiX system identifies targets using LBPH facial recognition on a single camera feed. When a target moves from one camera's field of view to another, or when their face is not clearly visible (occluded, turned away), the system loses tracking entirely. Security operators have no way to correlate the same person across multiple camera streams based on body appearance.

### User Stories

#### US-1.1: Python ReID Microservice
> **As a** system operator,  
> **I want** a standalone Python microservice running alongside DrishtiX,  
> **So that** heavy AI processing (PyTorch/OSNet) stays out of the JVM and can be scaled independently.

**Acceptance Criteria:**
- [ ] A FastAPI microservice exists at `services/reid-service/` with a single `POST /extract` endpoint
- [ ] The endpoint accepts a JPEG/PNG image (person crop) as `multipart/form-data`
- [ ] It loads the OSNet model (`osnet_x1_0`) from the `torchreid` library on startup
- [ ] It returns a JSON response: `{ "embedding": [0.123, -0.456, ...], "dimensions": 512 }`
- [ ] The service starts on a configurable port (default: `8100`) and includes a health check at `GET /health`
- [ ] A `requirements.txt` and startup script are provided

#### US-1.2: JavaFX → Python HTTP Integration
> **As a** DrishtiX operator,  
> **I want** the app to automatically send detected person crops to the ReID service,  
> **So that** feature embeddings are extracted without blocking the video feed.

**Acceptance Criteria:**
- [ ] A new `ReIDService.java` singleton uses `java.net.http.HttpClient` (Java 11+) to POST image bytes to the Python service
- [ ] The HTTP call is executed asynchronously via `CompletableFuture` on the existing Video Inference thread pool
- [ ] The service gracefully handles connection failures (Python service down) — logs a warning and continues face recognition without crashing
- [ ] The ReID endpoint URL is configurable via `alert_config` collection (key: `reid_service_url`, default: `http://localhost:8100`)

#### US-1.3: Vector Storage in MongoDB
> **As a** system,  
> **I need to** persist the 512-dimensional embedding vector alongside each detection log,  
> **So that** future detections can be compared against historical sightings.

**Acceptance Criteria:**
- [ ] A new `person_embeddings` collection stores: `{ target_id, camera_id, embedding: [512 doubles], snapshot_path, timestamp }`
- [ ] A new `PersonEmbeddingDAO` handles CRUD operations for this collection
- [ ] Embeddings are stored as a BSON array of doubles in MongoDB
- [ ] The database init script `drishtix_init.js` is updated with the new collection and indexes (incremental, non-destructive)

#### US-1.4: Cosine Similarity Matching
> **As a** security operator,  
> **I want** the system to automatically match a new person sighting against all recent embeddings,  
> **So that** I can track a suspect across multiple camera feeds.

**Acceptance Criteria:**
- [ ] A `VectorMathUtil.java` utility provides a `cosineSimilarity(double[], double[])` method
- [ ] When a new embedding is obtained, the system compares it against the last N embeddings from different cameras (configurable window, default: last 100)
- [ ] A match is declared when cosine similarity exceeds 85% (configurable via `alert_config` key: `reid_similarity_threshold`, default: `0.85`)
- [ ] On a match, the system creates a `ReIDMatch` event linking the two sightings (camera A → camera B)
- [ ] A match triggers the existing alert pipeline (sound + visual popup + detection log)

---

## Feature 2: Multi-Channel Instant Push Engine

### Problem Statement
Currently, when a target is detected, the system plays an audio alert and shows an in-app popup overlay. However, field security staff who are not sitting at the DrishtiX workstation receive no notification. Additionally, the current popup overlay blocks the camera feed and requires manual dismissal.

### User Stories

#### US-2.1: Non-Blocking Desktop Notifications (ControlsFX)
> **As a** DrishtiX operator,  
> **I want** smooth sliding notification toasts that don't block the camera feed,  
> **So that** I can see alerts while continuing to monitor the live video.

**Acceptance Criteria:**
- [ ] ControlsFX library is added to `pom.xml`
- [ ] A new `NotificationService.java` singleton wraps `org.controlsfx.control.Notifications`
- [ ] Notifications display: target name, category (Criminal/Missing), confidence %, camera name, and a thumbnail of the snapshot
- [ ] Criminal alerts use a red-themed notification; Missing Person alerts use blue-themed
- [ ] Notifications auto-dismiss after 8 seconds but can be manually closed
- [ ] Notifications slide in from the bottom-right corner, stacking if multiple arrive
- [ ] The existing `showAlertPopup()` blocking overlay is preserved as a fallback but the default behavior switches to non-blocking toasts
- [ ] All UI updates are dispatched via `Platform.runLater()` to ensure thread safety

#### US-2.2: Telegram Bot Integration
> **As a** field security team member,  
> **I want to** receive Telegram messages with the suspect's photo and location details,  
> **So that** I can take immediate action even when I'm not at the DrishtiX workstation.

**Acceptance Criteria:**
- [ ] A new `TelegramAlertService.java` singleton uses `java.net.http.HttpClient` to call the Telegram Bot API
- [ ] The service sends a photo message via `POST https://api.telegram.org/bot<TOKEN>/sendPhoto` using `multipart/form-data`
- [ ] The message caption includes: Target Name, Category, Case #, Confidence %, Camera Name, Location Tag, and Timestamp
- [ ] The Telegram Bot Token and Chat ID are stored in `alert_config` collection:
  - `telegram_bot_token` — the bot API token
  - `telegram_chat_id` — the target chat/group ID
  - `telegram_enabled` — master switch (default: `false`)
- [ ] Telegram sending is fully asynchronous (does not block the video pipeline)
- [ ] If Telegram is disabled or fails, the system logs a warning and continues without crashing
- [ ] A "Test Telegram" button exists in the Settings UI to verify the bot configuration

#### US-2.3: Alert Pipeline Orchestration
> **As a** system operator,  
> **I want** all alert channels (Audio + Desktop Notification + Telegram) to fire simultaneously on detection,  
> **So that** no time is lost between detection and field response.

**Acceptance Criteria:**
- [ ] The `AlertService.triggerAlert()` method orchestrates all three channels in parallel
- [ ] Each channel is independent — one channel failing does not prevent others from firing
- [ ] The existing per-target cooldown applies uniformly across all channels
- [ ] Config keys `audio_enabled`, `telegram_enabled` independently toggle each channel

---

## Success Metrics

| Metric | Target |
|---|---|
| ReID vector extraction latency | < 200ms per crop (Python service) |
| ReID matching accuracy | > 85% cosine similarity for same-person across cameras |
| Telegram alert delivery time | < 3 seconds from detection to message receipt |
| Desktop notification display time | < 100ms from detection event |
| Zero regression on existing LBPH pipeline | All existing face detection/recognition flows unaffected |

---

## Non-Goals (Explicitly Out of Scope)
- Converting the JavaFX desktop app to Spring Boot or a web application
- Building a web dashboard (the frontend remains JavaFX)
- Multi-GPU inference optimization for the ReID service
- Real-time video streaming to Telegram (only snapshot photos)
- Person tracking within a single camera frame (only cross-camera ReID)
