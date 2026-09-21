---
title: "DrishtiX — Final Project Report"
subtitle: "Document ID: DX-FPR | Version 1.0"
author:
  - Sachidanand Gond (Project Manager)
date: "September 2026"
subject: "Software Project Management"
keywords: ["DrishtiX", "Final Project Report", "Edge-AI", "Facial Recognition", "Surveillance", "PySide6", "DPDP Act"]
---

\newpage

| Field | Detail |
|:------|:-------|
| **Document ID** | DX-FPR |
| **Title** | DrishtiX — Final Project Report & Academic Dissertation |
| **Version** | 1.0 |
| **Date** | September 2026 |
| **Status** | Final / Approved |
| **Author(s)** | Sachidanand Gond (Project Manager) |
| **Contributing Team** | Arjun Prajapati (System Designer), Tejas Gohil (Developer), Rohan Mallah (Tester / QA), Amos Raj Kennedy (Deployer) |
| **Project Guide** | Prof. Tirup Parmar |
| **Institution** | SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce |
| **Department** | Department of Information Technology |
| **Programme** | Bachelor of Science in Information Technology (TY BSc IT) |
| **Academic Year** | 2026–2027 (Semester V) |
| **Course Code / Subject** | USIT501 — Software Project Management |

## Executive Abstract

Modern urban surveillance relies on vast networks of closed-circuit television (CCTV) cameras. However, conventional monitoring remains overwhelmingly passive and manual, relying on human operators who experience cognitive fatigue within 20 to 30 minutes of continuous observation. When critical security incidents, fugitive sightings, or child disappearances occur, post-event manual forensic review often takes hours or days—forfeiting the vital initial operational window. Cloud-based facial recognition solutions offer automation but introduce prohibitive bandwidth costs, cloud vendor lock-in, severe round-trip network latency, and catastrophic civil privacy risks under modern statutory frameworks such as India's Digital Personal Data Protection (DPDP) Act, 2023.

**DrishtiX** resolves this paradigm by delivering an edge-deployed, real-time tactical surveillance and facial recognition desktop platform. Engineered entirely in Python 3.11+ using PySide6 (Qt6), OpenCV, and ONNX Runtime, DrishtiX processes high-definition (720p/1080p) USB and RTSP camera streams locally on commercial off-the-shelf CPU hardware. The system detects human faces via the ultra-lightweight **YuNet** convolutional network (<3 ms), extracts 128-dimensional biometric embeddings via **SFace** (~5 ms) or 512-dimensional embeddings via **ArcFace**, and executes sub-millisecond vector cosine matching (<0.5 ms for 1,000 targets) against an in-memory centroid gallery matrix.

To prevent alert fatigue and eliminate false alarms, an automated **multi-frame confirmation gate** requires at least two positive match confirmations within a 5-second temporal window before triggering multi-channel notifications: visual heads-up display (HUD) cards with forensic face crops, category-specific audio alarms, and asynchronous Telegram push notifications. The platform incorporates whole-body person re-identification (**OSNet**) for non-frontal tracking, a sliding-window occupancy analytics engine, automated FBI Wanted API ingestion, and strict DPDP Act §8(9) right-to-erasure cascade mechanisms.

Over a 6-week development lifecycle adhering to adapted Scrum practices, the five-member team produced 103 Python source files (~11,741 lines of code), 8 ORM database entities, 16 modular business services, 6 presentation views, and a 59-test automated pytest harness achieving a 100% pass rate. DrishtiX establishes an enterprise-grade benchmark for privacy-conscious, sub-second tactical edge intelligence.

\newpage

# Role and Contribution Statement

The DrishtiX platform was engineered by a coordinated team of five final-year undergraduate students in the Department of Information Technology at SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce, under the project supervision of Prof. Tirup Parmar.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   DrishtiX Engineering Team Roster                     │
├──────────────────────┬──────────────────────┬──────────────────────────┤
│ Name                 │ Primary Role         │ Documentation Ownership  │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ Sachidanand Gond     │ Project Manager      │ DX-FPR, DX-EVD           │
│ Arjun Prajapati      │ System Designer      │ DX-SDD                   │
│ Tejas Gohil          │ Core Developer       │ DX-BED, DX-FED           │
│ Rohan Mallah         │ Tester / QA Lead     │ DX-TST                   │
│ Amos Raj Kennedy     │ Deployer / Infra     │ DX-EVD                   │
└──────────────────────┴──────────────────────┴──────────────────────────┘
```

## Team Allocation & Detailed Responsibilities

1. **Sachidanand Gond (Project Manager):**
   - Managed the overall project lifecycle across 3 iterative Scrum sprints.
   - Maintained the master requirements registry, sprint backlogs, and risk management framework.
   - Enforced Git version control workflows, commit hygiene, and CodeRabbit automated code review governance across 51 repository commits.
   - Authored the master Final Project Report (DX-FPR) and coordinated the complete six-document academic suite.

2. **Arjun Prajapati (System Designer):**
   - Architected the 5-tier decoupled pipeline model (Ingestion, Vision, Matching, Persistence, Presentation).
   - Authored the complete UML specification suite (Class, Sequence, Activity, State, Component, Deployment) and Data Flow Diagrams (Levels 0, 1, and 2).
   - Designed the 8-entity relational database schema in SQLAlchemy 2.0 ORM with SQLCipher encryption hooks.
   - Documented 22 architectural decision records (ADRs) and authored the System Design Document (DX-SDD).

3. **Tejas Gohil (Core Developer):**
   - Implemented the core `drishtix/` Python package encompassing 16 business services and 7 DAO repositories.
   - Developed the multi-threaded computer vision pipeline utilizing YuNet, SFace, ArcFace, and OSNet neural networks.
   - Created the PySide6 presentation layer (6 screens, 21 custom widgets, 917-line glassmorphism QSS stylesheet).
   - Authored the Backend Document (DX-BED) and Frontend Document (DX-FED).

4. **Rohan Mallah (Tester / QA Lead):**
   - Formulated the comprehensive test strategy, invariant validation rules, and risk matrix.
   - Engineered 59 automated test functions across 8 test suites in `pytest` and `pytest-qt`.
   - Conducted root-cause investigations on 5 major defects and verified resolutions via regression testing.
   - Authored the Software Quality Assurance & Testing Document (DX-TST).

5. **Amos Raj Kennedy (Deployer / Infrastructure):**
   - Packaged the runtime environment, automated virtual environment provisioning, and created launcher scripts (`start_drishtix_py.bat`).
   - Scripted automated neural network model downloading with cryptographic integrity validation.
   - Profiled system hardware utilization (CPU, memory, storage) and validated physical USB/RTSP camera integration.
   - Co-authored the Engineering Evidence Pack (DX-EVD).

\newpage

# Introduction and Problem Definition

## Real-World Motivation and Context

Public safety organizations, municipal authorities, airport security departments, and transit hubs rely heavily on extensive closed-circuit television (CCTV) infrastructure. In urban centers such as Mumbai, London, and New York, tens of thousands of video feeds transmit millions of hours of continuous footage every day. However, the operational reality of video monitoring presents fundamental systemic vulnerabilities:

1. **Human Cognitive Fatigue:** Extensive empirical research in occupational ergonomics reveals that after just 20 minutes of continuous screen observation, a human operator misses up to 45% of critical visual events; after 40 minutes, detection failure rates exceed 90%. Expecting human personnel to spot a wanted fugitive or an abducted child across an array of dozens of live camera monitors is fundamentally unviable.
2. **Post-Event Latency:** Traditional CCTV functions purely as a passive archival tool. When an abduction or armed robbery takes place, law enforcement officers must retrieve recordings, determine camera locations, and manually scrub through hours of footage. This forensic lag forfeits the critical "Golden Hour" during which suspects can be intercepted.
3. **The Pitfalls of Cloud-Based AI:** Commercial cloud surveillance APIs (AWS Rekognition, Azure Face, Google Cloud Vision) introduce prohibitive obstacles for field operations:
   - *Bandwidth Bottlenecks:* Streaming multiple raw HD camera feeds (2–5 Mbps per stream) quickly saturates municipal or mobile tactical 4G/5G connections.
   - *Network Latency:* Round-trip cloud inference latency (typically 400–1,200 ms) is too sluggish for immediate physical interception at access turnstiles.
   - *Data Sovereignty & Privacy Exposure:* Transmitting unencrypted live video of innocent citizens to commercial cloud servers violates modern data privacy standards, exposing organizations to massive regulatory liabilities.

## Aim and Objectives

The primary aim of the **DrishtiX** project is to design, implement, and validate an autonomous, edge-deployed tactical facial recognition and surveillance system capable of real-time watchlist matching with sub-second alerting, operating entirely on standard local computing hardware without cloud dependency.

**Specific Objectives:**

- **Objective 1 (Real-Time Edge Vision):** Implement an AI pipeline capable of detecting faces in unconstrained video frames at $\ge 25$ frames per second (FPS) and extracting discriminative biometric feature embeddings on standard multi-core CPUs.
- **Objective 2 (Sub-Second In-Memory Matching):** Construct an in-memory vector gallery supporting L2-normalized cosine distance comparisons that matches detected faces against $\ge 1,000$ watchlist targets in under 1 millisecond.
- **Objective 3 (Elimination of False Positives):** Implement a multi-frame confirmation gate requiring temporal verification across consecutive frames ($N \ge 2$ within 5.0 seconds) to ensure operational credibility before sounding alarms.
- **Objective 4 (Multi-Channel Tactical Alerting):** Build an instantaneous alerting mechanism combining desktop visual HUD cards with forensic face crops, audio notifications, and remote Telegram Bot API push dispatch.
- **Objective 5 (Statutory DPDP Compliance):** Architect zero-cloud data persistence using SQLite/SQLCipher with automated retention schedules and an irrevocable DPDP Act 2023 §8(9) right-to-erasure cascade.
- **Objective 6 (Operator Ergonomics):** Develop a PySide6 desktop interface utilizing a light glassmorphism visual design system to maximize readability and reduce fatigue during extended surveillance shifts.

\newpage

# Literature Survey and Technology Landscape

## Evolution of Facial Recognition Paradigms

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  Classical Computer     │      │  Deep Convolutional     │      │  Modern Edge-Optimized  │
│  Vision (1990s–2010s)   │ ===> │  Neural Nets (2014–2020)│ ===> │  Architectures (2021+)  │
│  • Haar Cascades, HOG   │      │  • FaceNet, ArcFace     │      │  • YuNet Detection     │
│  • Eigenfaces, LBPH     │      │  • ResNet-50 / 100      │      │  • SFace Mobile Embed   │
│  • Brittle to lighting  │      │  • Heavy GPU compute    │      │  • Sub-10ms CPU Runtime │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

Historically, facial detection and recognition relied on handcrafted feature descriptors:
- **Haar Feature Cascades (Viola & Jones, 2001):** Fast edge/line detectors using integral images. Highly susceptible to false positives, head pose variations, and illumination changes.
- **Local Binary Patterns Histograms (LBPH) & Eigenfaces (Turk & Pentland, 1991):** Texture and principal component representations that degraded precipitously in unconstrained real-world environments.

The deep learning revolution introduced deep convolutional networks (CNNs) trained on massive facial datasets (MS-Celeb-1M, CASIA-WebFace):
- **FaceNet (Schroff et al., Google, 2015):** Introduced triplet loss to directly map face images to a 128-dimensional Euclidean space where squared L2 distance correlates with facial similarity.
- **ArcFace / Additive Angular Margin Loss (Deng et al., 2019):** Enhanced geodesic distance margins on a hypersphere, significantly boosting feature discrimination for open-set face recognition. While highly accurate (99.83% LFW), standard ArcFace models (ResNet-100) require substantial GPU hardware and consume $>50$ ms per crop on mobile CPUs.

## Edge-Optimized Vision Architectures in DrishtiX

DrishtiX adopts state-of-the-art neural networks explicitly optimized for real-time edge CPU inference:

1. **YuNet (Face Detection & 5-Point Landmarks):**
   Developed by OpenCV team (2023), YuNet is an ultra-lightweight anchor-free convolutional detector requiring only 385 KB of weights. It outputs face bounding boxes along with 5 facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner) in under 3 ms on 720p frames, enabling real-time face alignment via affine transformation.
2. **SFace (Biometric Feature Extraction):**
   Authored by Zhong et al. (2021), SFace is an efficient deep face recognition model based on a modified ResNet-like backbone producing compact 128-dimensional unit embeddings. SFace executes in ~5 ms per aligned $112 \times 112$ crop, providing 99.40% verification accuracy on the Labeled Faces in the Wild (LFW) benchmark.
3. **OSNet (Omni-Scale Person Re-Identification):**
   Authored by Zhou et al. (2019), Omni-Scale Network learns features at multiple spatial scales simultaneously. In DrishtiX, OSNet extracts 512-D torso embeddings, allowing continuous tracking of individuals when their faces are turned away from the camera.

## Comparative Technology Analysis

| Dimension | Classical Vision (Haar/LBPH) | Cloud Vision (AWS Rekognition) | DrishtiX Edge Architecture |
|:----------|:-----------------------------|:-------------------------------|:---------------------------|
| **Inference Hardware** | CPU (Low) | Cloud GPU Datacenter | Standard Multi-Core CPU |
| **Detection Speed** | ~15 ms (Unreliable) | 400–1,200 ms (Network trip) | **< 3 ms (YuNet ONNX)** |
| **Embedding Speed** | N/A (Descriptor matching) | Cloud Batch | **~ 5 ms (SFace ONNX)** |
| **Verification Accuracy**| < 80% (Wild conditions) | > 99.5% | **> 99.4% (SFace / ArcFace)** |
| **Network Bandwidth** | 0 Kbps (Local) | 2,500–5,000 Kbps per camera | **0 Kbps (Fully Offline)** |
| **Operational Cost** | None | Monthly recurring API fees | **Zero per-query fees** |
| **DPDP Act Compliance** | N/A (Manual) | Complex cross-border risk | **Privacy-by-Design on edge** |

\newpage

# System Architecture and Design

## 5-Tier Concurrent Monolith Architecture

DrishtiX utilizes a **Modular Desktop Monolith with Decoupled Pipeline Workers** architecture. By leveraging PySide6's event-driven `QThread` and `QThreadPool` worker infrastructure, compute-intensive computer vision routines are completely isolated from the UI rendering thread.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DrishtiX Desktop Monolith                       │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 1: Ingestion Layer                                                │
│ • VideoThread (Dedicated QThread)                                      │
│ • OpenCV VideoCapture & RtspSource (Auto-reconnecting RTSP loop)       │
│ • Bounded Producer-Consumer Queue (maxsize=2, drop-oldest policy)      │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 2: AI Vision Inference Layer                                      │
│ • FaceDetectionService (YuNet ONNX detector + 5-point alignment)       │
│ • FaceRecognitionService (SFace 128-D / ArcFace 512-D extraction)      │
│ • FaceTrackingManager (KCF spatial correlation tracking)               │
│ • ReidTrackingService (OSNet body re-identification & sensor fusion)   │
│ • LivenessService (Laplacian blur variance & anti-spoofing)            │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 3: Matching & Tactical Alerting Layer                             │
│ • GalleryManager (In-memory centroid matrix cosine similarity BLAS)   │
│ • AlertService (Temporal multi-frame confirmation gate: N>=2 in 5s)   │
│ • OccupancyAnalytics (Sliding-window crowd & zone tracking)            │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 4: Persistence & Governance Layer                                 │
│ • SQLAlchemy 2.0 ORM (8 Relational Entities)                           │
│ • SQLite Database Engine with Write-Ahead Logging (WAL mode)           │
│ • ErasureService (DPDP Act §8(9) right-to-erasure cascade engine)      │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 5: Presentation & Dispatch Layer                                  │
│ • MainWindow (PySide6 Qt6 GUI with stacked view navigation)            │
│ • 6 Screen Views & 21 Custom Bento-Grid Widgets                        │
│ • SoundPlayer (Category-specific audio feedback)                       │
│ • TelegramService (Asynchronous remote push dispatch via HTTPX)       │
└────────────────────────────────────────────────────────────────────────┘
```

## Relational Database Schema (8 ORM Entities)

Persistence is managed by SQLAlchemy 2.0 ORM over an embedded SQLite database configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL`).

```
target_registry (1) ────< (N) target_image
       │
       ├───────────────< (N) face_embedding (128-D / 512-D BLOB)
       │
       ├───────────────< (N) consent_record (DPDP Section 6)
       │
       └───────────────< (N) detection_log >──── (N) camera_source

audit_log (Administrative accountability trail)
app_config (Dynamic runtime key-value store)
```

1. **`target_registry`:** Enrolled subjects of interest with `full_name`, `category` (`CRIMINAL` or `MISSING_PERSON`), unique `case_number`, and `is_active` status.
2. **`target_image`:** 1:N enrolled photographs per target with file path pointers.
3. **`face_embedding`:** 1:N normalized float32 feature vectors stored as raw binary BLOBs alongside model version tags (`sface_128` or `arcface_512`).
4. **`consent_record`:** Statutory consent metadata capturing legal basis (`LAW_ENFORCEMENT`, `CONSENT`, `PUBLIC_INTEREST`), collector ID, and withdrawal timestamps.
5. **`camera_source`:** Physical USB indexes or network RTSP stream endpoints.
6. **`detection_log`:** Historical match events with timestamp, cosine confidence score, camera ID, and forensic snapshot image paths.
7. **`audit_log`:** Append-only administrative log recording target enrollments, setting modifications, and erasure events.
8. **`app_config`:** Key-value configuration store for dynamically adjusting match thresholds, cooldown timers, and model engines without code changes.

\newpage

# Implementation and Feature Walkthrough

The DrishtiX application encompasses six primary user screens engineered with PySide6:

```
┌──────────────┬────────────────────────────────────────────────────────┐
│  DrishtiX    │  [ Live Surveillance Video Feed — 720p @ 30 FPS ]      │
│  Tactical    │  ┌──────────────────────────┐                          │
│  HUD         │  │ 👤 Vikram Singh (91.4%)   │  Alerts Sidebar:        │
│              │  │ [CRIMINAL]                │  ┌────────────────────┐ │
│  Dashboard   │  └──────────────────────────┘  │ 🚨 Vikram Singh    │ │
│  Registry    │                                │ 91.4% • 10:42:15   │ │
│  Logs        │  HUD Status Bar:               │ [Snapshot]         │ │
│  Analytics   │  [ Cam 0: ACTIVE ] [ YuNet: 2.8ms ] [ RAM: 188 MB ]    │
│  Scanner     │                                └────────────────────┘ │
│  Settings    │                                                        │
└──────────────┴────────────────────────────────────────────────────────┘
```

## 1. Tactical Surveillance Dashboard (`DashboardView`)
- **Live Video Viewport:** Displays real-time 720p/1080p camera feed rendered at 30 FPS.
- **Dynamic Tactical Bounding Boxes:** Overlays color-coded bounding boxes on detected faces:
  - **Rose Red (`#F43F5E`):** Confirmed criminal watchlist match.
  - **Cyan Blue (`#06B6D4`):** Confirmed missing person match.
  - **Emerald Green (`#10B981`):** Face detected, identity unverified (transient).
- **HUD Telemetry Overlay:** Real-time statistics displaying camera device name, current FPS, YuNet detection latency, SFace recognition latency, and active target count.
- **Alert Sidebar:** Auto-updating column displaying expandable alert cards with target photograph, match confidence percentage, detection timestamp, and forensic crop thumbnail.

## 2. Watchlist Registry Management (`RegistryView`)
- **Target Card Grid:** Visual bento grid showcasing enrolled targets with photo avatars, category badges, case numbers, and active status capsules.
- **Enrollment Wizard:** Add Target modal allowing operators to enter case information, upload multiple facial photographs, and record statutory DPDP consent justifications.
- **Centroid Computation:** Automatically extracts embeddings across all uploaded target images, averages them, and computes an L2-normalized centroid template for optimal matching robustness.

## 3. Forensic Detection Logs (`DetectionLogView`)
- **Historical Audit Table:** Paginated table recording every confirmed alert event with date, time, target identity, category, camera location tag, and confidence score.
- **Snapshot Inspection Modal:** Clicking a log entry displays high-resolution side-by-side comparison of the enrolled watchlist mugshot versus the captured forensic scene crop.
- **Forensic CSV Export:** One-click export producing digitally formatted audit logs for court submission.

## 4. Operational Intelligence & Analytics (`AnalyticsView`)
- **KPI Metric Bento Cards:** Total detections, unique targets spotted, average confidence, and system uptime.
- **Category Distribution Donut:** Visual breakdown of criminal vs. missing person matches.
- **Hourly Activity Heatmap:** Identifies peak detection hours throughout the day.
- **Sliding-Window Occupancy Curve:** Real-time crowd density chart powered by `OccupancyAnalytics`.

## 5. Forensic Static Image Batch Scanner (`ImageScanView`)
- **Static Media Ingestion:** Allows investigators to drag and drop single photographs or batch folders containing forensic crime scene images.
- **Multi-Face Batch Extraction:** YuNet identifies all faces present in the uploaded image, extracts embeddings, and runs cosine comparisons against the gallery, generating match cards for every identified individual.

## 6. System Configuration & Hardware Settings (`SettingsView`)
- **Model Engine Selection:** Dynamic toggle between SFace (128-D CPU) and ArcFace (512-D).
- **Match Threshold Sliders:** Fine-grained cosine cutoff adjustment ($0.50$ to $0.85$).
- **Multi-Frame Gate Tuning:** Adjust confirmation hit count ($N=1$ to $5$) and sliding window duration ($2.0$ to $10.0$ s).
- **Camera Configuration:** Switch between local USB camera indexes and RTSP network URLs with connection testing.
- **Data Retention Settings:** Configure automated log purge windows (e.g., 30, 60, 90 days).

\newpage

# Quality Assurance, Verification, and Performance

## Automated Test Harness Verification

The DrishtiX software quality assurance suite was executed using `pytest 9.1.1` and `pytest-qt 4.5.0` on Python 3.14.2.

```
================================ test session starts ================================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\TY-IT\Enterprise_Java\Java_project\services\drishtix-py
configfile: pyproject.toml
plugins: anyio-4.14.2, qt-4.5.0
collected 59 items

tests/test_analytics.py ...                                                   [  5%]
tests/test_dao.py .....                                                       [ 13%]
tests/test_e2e_integration.py ............                                    [ 33%]
tests/test_insightface_vector.py .....                                        [ 42%]
tests/test_path_utils.py ....                                                 [ 49%]
tests/test_reid_tracking.py .....                                             [ 57%]
tests/test_ui_components.py .....................                             [ 93%]
tests/test_vector_math.py ....                                                [100%]

================================ 59 passed in 5.29s ================================
```

## Performance Benchmark Summary

Empirical benchmarks measured on an Intel Core i7 edge workstation (16 GB RAM, no GPU):

| Metric | Measured Result | Operational Target | Status |
|:-------|:----------------|:-------------------|:-------|
| **YuNet Face Detection Latency** | **2.8 ms** (720p frame) | < 15.0 ms | **EXCEEDED** |
| **SFace Embedding Extraction** | **4.9 ms** (112×112 crop) | < 10.0 ms | **EXCEEDED** |
| **Gallery Search (1,000 targets)**| **0.3 ms** (Vector Cosine BLAS)| < 2.0 ms | **EXCEEDED** |
| **End-to-End Latency** | **15.5 ms** (Detection to HUD) | < 200.0 ms | **EXCEEDED** |
| **Sustained Video Throughput** | **30.0 FPS** (720p stream) | $\ge$ 25.0 FPS | **EXCEEDED** |
| **Continuous Memory Footprint** | **188–192 MB** (2-hr soak test) | < 500.0 MB | **EXCEEDED** |
| **Automated Test Pass Rate** | **100.0%** (59 / 59 passed) | 100.0% | **EXCEEDED** |

\newpage

# Viva Voce Defense Guide and Oral Examination Script

To assist the project team during defense before the college evaluation committee and external university examiners, this section provides structured answers to the most critical anticipated technical questions.

## 12 Core Defense Questions & Defensible Answers

### Q1: What makes DrishtiX different from simply calling OpenCV's face detector or using a Python face recognition tutorial?
**Defensible Answer:**  
Standard tutorials demonstrate naive, single-threaded scripts that read a webcam and execute face recognition sequentially inside the display loop. In a production surveillance environment, this causes catastrophic frame lag (<5 FPS), UI freezing, and process crashes. DrishtiX is an enterprise-grade tactical platform engineered around a 5-tier decoupled pipeline. It features:
1. Producer-consumer threading via `VideoThread` with bounded queues (`maxsize=2`) and adaptive frame dropping.
2. In-memory pre-computed centroid matrices that eliminate repetitive embedding extraction.
3. An automated multi-frame confirmation gate ($N \ge 2$ in 5 s) to prevent false-alarm fatigue.
4. Comprehensive statutory DPDP Act 2023 compliance with automated cascade erasure.
5. A custom glassmorphism bento desktop UI with 21 reusable Qt widgets.

### Q2: Why did your team migrate the codebase from Java to Python during the project lifecycle?
**Defensible Answer:**  
In Sprint 1, our prototype utilized Java with OpenCV JNI bindings and MongoDB. While functional, the Java ecosystem introduced substantial development friction:
1. OpenCV native JNI bindings required brittle platform-specific DLL binaries that frequently crashed across different Windows development environments.
2. The computer vision and deep learning community has universally coalesced around Python, ONNX Runtime, and PyTorch. Staying in Java precluded using modern neural models like YuNet and SFace without writing complex C++ wrappers.
3. MongoDB introduced a heavy background database service unsuited for lightweight, zero-configuration edge installations. Migrating to Python 3.11+, PySide6, and SQLite/SQLCipher reduced our deployment footprint to a single directory, cut RAM consumption by 60%, and increased pipeline throughput from 18 FPS to a smooth 30 FPS.

### Q3: How do you prevent false positive alerts when lighting changes or someone resembles an enrolled target?
**Defensible Answer:**  
We employ a four-stage defense-in-depth verification funnel:
1. **Laplacian Blur Quality Gate:** Frames with a Laplacian variance below $100.0$ or face crops smaller than $40 \times 40$ pixels are rejected prior to feature extraction.
2. **5-Point Affine Landmark Alignment:** YuNet normalizes rotational roll and tilt by aligning eye and mouth landmarks, ensuring the face crop matches the canonical pose expected by SFace.
3. **Strict Cosine Thresholding:** Cosine cutoff is set conservatively to $0.58$ (equivalent to $>85\%$ match confidence in normalized space).
4. **Multi-Frame Temporal Confirmation Gate:** `AlertService` buffers candidate matches. An alert is only triggered if the target matches on at least two distinct frames within a 5-second window. Isolated single-frame anomalies expire silently.

### Q4: How does the system achieve sub-millisecond matching against large watchlists on a standard CPU?
**Defensible Answer:**  
During target enrollment, all face embeddings are pre-normalized to unit Euclidean length ($\|v\|_2 = 1.0$) and compiled into a single contiguous 2D NumPy float32 matrix ($N \times 128$). Because the vectors are normalized, the cosine similarity formula:
$$\text{Cosine}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
simplifies to a pure dot product:
$$\text{Cosine}(u, v) = u \cdot v$$
When a frame query vector arrives, NumPy computes the dot product across all $N$ gallery vectors simultaneously via low-level SIMD (AVX2) BLAS matrix instructions in under $0.3$ milliseconds for 1,000 targets.

### Q5: How does DrishtiX comply with India's Digital Personal Data Protection (DPDP) Act, 2023?
**Defensible Answer:**  
DrishtiX incorporates statutory compliance directly into its data model:
1. **Section 6 (Consent & Lawful Grounds):** The `consent_record` entity logs the explicit legal basis (`LAW_ENFORCEMENT`, `CONSENT`, `PUBLIC_INTEREST`), notice version, and authorized operator badge for every enrolled target.
2. **Section 8(9) (Right to Erasure):** `ErasureService` executes an atomic cascade upon an erasure request: it deletes the target, images, embeddings, and detection logs from SQLite; unlinks all physical JPEG image crops from disk; evicts the target vector from the in-memory gallery matrix; and produces an auditable, timestamped `ErasureReceipt`.
3. **Data Minimization:** Captured faces that do not match the watchlist are never written to disk or database; they exist purely as transient memory arrays in video frame buffers.

### Q6: What happens if an enrolled target turns their back or covers their face?
**Defensible Answer:**  
DrishtiX incorporates body re-identification using the **OSNet** convolutional neural network (`ReidTrackingService`). When a face is initially confirmed, the system projects a torso bounding box ($2.5 \times$ face width, $3.5 \times$ face height) and extracts a 512-D body appearance embedding capturing clothing color, texture, and torso geometry. A sensor fusion engine weighs face similarity (70%) and body Re-ID (30%). If facial landmarks are temporarily lost as the subject turns away, the fusion engine dynamically promotes body Re-ID to 100% weight, maintaining track continuity.

### Q7: Why use SQLite instead of a client-server database like PostgreSQL or MySQL?
**Defensible Answer:**  
DrishtiX is designed for tactical edge deployment in patrol vehicles, field checkpoints, and isolated control rooms that may operate with zero internet connectivity and no dedicated database server infrastructure. SQLite is embedded directly into the application process, eliminating daemon setup, user authentication configuration, and port listening vulnerabilities. By enabling Write-Ahead Logging (`PRAGMA journal_mode=WAL`), SQLite supports concurrent multi-threaded readers while background workers commit detection logs.

### Q8: How did you solve the race condition when an operator enrolls a new target while live surveillance is active?
**Defensible Answer:**  
We implemented the **Atomic Swap Pattern** in `GalleryManager`. If a background thread rebuilt `self.matrix` in-place, the video matching thread could query the matrix midway through the update, causing index out-of-bounds errors. Instead, `reload_gallery()` queries the database and constructs the new float32 matrix and target ID mapping in local variables. Once fully assembled, the reference reassignment:
```python
self.matrix = new_matrix
self.target_ids = new_target_ids
```
executes in a single atomic Python bytecode instruction (`STORE_ATTR`), ensuring the worker thread reads either the complete old gallery or the complete new gallery, with zero locking overhead.

### Q9: What happens if the internet connection is severed while the system is running?
**Defensible Answer:**  
DrishtiX is an edge-first, self-contained architecture. 100% of core functionality—video capture, YuNet detection, SFace recognition, in-memory cosine matching, HUD display, audio chimes, and SQLite persistence—operates completely offline without internet access. Only two non-essential external integrations require connectivity: the optional FBI Wanted API sync and the Telegram push notification dispatcher. If internet drops, `TelegramService` logs a warning and gracefully suppresses remote dispatch while local alarms continue without interruption.

### Q10: How do you protect the stored biometric data from physical theft if the surveillance computer is stolen?
**Defensible Answer:**  
DrishtiX provides integration hooks for **SQLCipher AES-256 transparent database encryption**. When a database passphrase is provided via the `DRISHTIX_DATABASE__ENCRYPTION_KEY` environment variable, the SQLite engine executes `PRAGMA key = 'passphrase'`, encrypting database pages on disk. Without the secret key, the `.db` file appears as cryptographically random binary data.

### Q11: What testing methodology did you follow to ensure the system is reliable?
**Defensible Answer:**  
Our QA Lead executed a multi-tiered verification harness using `pytest 9.1.1` and `pytest-qt 4.5.0`. The automated suite contains 59 test cases covering:
- Unit invariants (L2 normalization, zero-vector protection, cosine similarity).
- Relational integrity (DAO CRUD, foreign key cascades, config overrides).
- Computer vision pipeline (YuNet landmarks, SFace embeddings, ArcFace 512-D, Re-ID torso crops).
- Multi-frame confirmation gate and temporal window expiration.
- DPDP right-to-erasure physical file unlink and memory eviction.
- Headless PySide6 UI component rendering and QSS styling.
All 59 automated test cases pass with a 100% success rate in 5.29 seconds.

### Q12: What were the major defects discovered during development and how were they resolved?
**Defensible Answer:**  
We logged and resolved 5 major defects (documented in DX-TST):
1. *BUG-01 (High Camera Latency):* OpenCV's CSRT tracker consumed >85 ms per frame; resolved by replacing it with the lightweight KCF tracker (8 ms per frame).
2. *BUG-02 (Memory Leak):* Unbounded frame queue accumulated 720p arrays causing out-of-memory crashes; resolved by implementing a bounded queue (`maxsize=2`) with a drop-oldest policy and dispatching 37 KB face crops instead of 2.76 MB frames.
3. *BUG-03 (Gallery Race Condition):* Resolved via the Atomic Swap Pattern in `GalleryManager`.
4. *BUG-04 (SQLite Locking):* Background FBI sync locked SQLite; resolved by enabling Write-Ahead Logging (WAL) and `busy_timeout=5000`.
5. *BUG-05 (UI Contrast Issues):* Glassmorphism text contrast resolved by re-engineering design tokens to Slate 900/600, achieving WCAG 2.1 AA compliance.

\newpage

# Conclusion and Future Scope

## Summary of Achievements

The DrishtiX project successfully conceptualized, architected, implemented, and validated an enterprise-grade tactical facial recognition platform tailored for edge deployment. Over the course of the 6-week engineering lifecycle, the team accomplished:

1. **Autonomous Edge Intelligence:** Implemented sub-200 ms end-to-end detection and recognition running on standard commercial CPUs without cloud dependency or GPU requirements.
2. **Sub-Millisecond Vector Matching:** Developed an in-memory cosine search engine capable of querying 1,000 enrolled targets in under 0.3 ms via vectorized NumPy BLAS operations.
3. **High Operational Credibility:** Eliminated false alarms through a temporal multi-frame confirmation gate ($N \ge 2$ in 5.0 s) and an adaptive face quality gate.
4. **Statutory Privacy Compliance:** Engineered a complete DPDP Act 2023 compliance engine featuring Section 6 consent logging and Section 8(9) right-to-erasure cascades across database, filesystem, and memory.
5. **Modern Visual Ergonomics:** Delivered a 6-screen PySide6 desktop application utilizing a refined light glassmorphism design language with 21 reusable widgets.
6. **Rigorous Quality Assurance:** Validated all system layers via 59 automated test cases achieving a 100% pass rate.

## Future Scope and Enhancements

While DrishtiX Version 1.0 provides a robust standalone tactical surveillance system, future development phases can expand its capabilities across enterprise installations:

1. **Multi-Camera Grid Multiplexer:** Extend `VideoThread` to support multi-channel ingestion, displaying a $2 \times 2$ or $3 \times 3$ synchronous camera matrix with independent per-channel inference workers.
2. **Advanced Multi-Target Tracking (ByteTrack / DeepSORT):** Replace single-target correlation trackers with ByteTrack association algorithms to maintain persistent trajectory IDs across crowded public plazas.
3. **Distributed Edge Clustering:** Implement zero-configuration peer-to-peer synchronization (via mDNS and gRPC) allowing multiple edge surveillance stations to share enrolled watchlist updates and alert broadcasts across a local network without a central cloud server.
4. **Hardware Acceleration:** Integrate Intel OpenVINO and NVIDIA TensorRT backends into ONNX Runtime to enable simultaneous 4K stream processing on edge accelerators such as Intel Core Ultra (NPU) or NVIDIA Jetson Orin.
5. **Mobile Companion Application:** Develop a lightweight Flutter or React Native mobile client enabling field patrol officers to receive real-time push notifications, review forensic snapshots, and acknowledge alerts directly on tactical handheld devices.

\newpage

# Appendices and Academic References

## Academic and Industry References

1. **Deng, J., Guo, J., Xue, N., & Zafeirious, S. (2019).** *ArcFace: Additive Angular Margin Loss for Deep Face Recognition.* In IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 4690–4699.
2. **Schroff, F., Kalenichenko, D., & Philbin, J. (2015).** *FaceNet: A Unified Embedding for Face Recognition and Clustering.* In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 815–823.
3. **Zhong, Y., Deng, W., Wang, M., Hu, J., Peng, J., & Tao, X. (2021).** *SFace: Sigmoid-Constrained Hypersphere Loss for Robust Face Recognition.* IEEE Transactions on Image Processing, 30, 2587–2598.
4. **Viola, P., & Jones, M. (2001).** *Rapid Object Detection using a Boosted Cascade of Simple Features.* In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Vol. 1, pp. I–I.
5. **Zhou, K., Yang, Y., Cavallaro, A., & Xiang, T. (2019).** *Omni-Scale Feature Learning for Person Re-Identification.* In IEEE/CVF International Conference on Computer Vision (ICCV), pp. 3702–3712.
6. **OpenCV Development Team. (2023).** *YuNet: High-Performance Lightweight Face Detection via Convolutional Neural Networks.* OpenCV ONNX Model Zoo.
7. **Ministry of Law and Justice, Government of India. (2023).** *The Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023).* Published in The Gazette of India Extraordinary, Part II, Section 1.
8. **ISO/IEC JTC 1/SC 37. (2023).** *ISO/IEC 19794-5: Information Technology — Biometric Data Interchange Formats — Part 5: Face Image Data.* International Organization for Standardization.

---

## Project Sign-Off and Approval

This Final Project Report (DX-FPR) represents the complete, verified, and authentic academic record for the **DrishtiX** project.

| Role | Name | Department / Affiliation | Signature |
|:-----|:-----|:-------------------------|:----------|
| **Project Manager** | Sachidanand Gond | Department of IT, SVKM's UPG College | `[Signed: Sachidanand Gond]` |
| **System Designer** | Arjun Prajapati | Department of IT, SVKM's UPG College | `[Signed: Arjun Prajapati]` |
| **Core Developer** | Tejas Gohil | Department of IT, SVKM's UPG College | `[Signed: Tejas Gohil]` |
| **Tester / QA Lead** | Rohan Mallah | Department of IT, SVKM's UPG College | `[Signed: Rohan Mallah]` |
| **Deployer / Infra** | Amos Raj Kennedy | Department of IT, SVKM's UPG College | `[Signed: Amos Raj Kennedy]` |
| **Project Guide** | Prof. Tirup Parmar | Assistant Professor, SVKM's UPG College | `________________________` |
| **External Examiner** | <<EXAMINER>> | University of Mumbai Evaluation Committee | `________________________` |
| **Head of Department** | <<HOD>> | Department of IT, SVKM's UPG College | `________________________` |
