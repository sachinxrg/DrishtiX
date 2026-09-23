---
title: "DrishtiX — Evidence Pack"
subtitle: "Document ID: DX-EVD | Version 1.0"
author:
  - Sachidanand Gond (Project Manager)
  - Amos Raj Kennedy (Deployer)
date: "September 2026"
subject: "Software Project Management"
keywords: ["DrishtiX", "Evidence Pack", "Agile", "Jira", "Git", "Deployment", "CodeRabbit"]
---

\newpage

| Field | Detail |
|:------|:-------|
| **Document ID** | DX-EVD |
| **Title** | DrishtiX — Engineering Evidence Pack & Deployment Audit |
| **Version** | 1.0 |
| **Date** | September 2026 |
| **Status** | Final / Approved |
| **Author(s)** | Sachidanand Gond (Project Manager), Amos Raj Kennedy (Deployer) |
| **Reviewer** | Prof. Tirup Parmar (Project Guide) |
| **Institution** | SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce |
| **Programme** | TY BSc IT, Semester V, 2026–27 |
| **Subject** | Software Project Management |

## At a Glance

The Engineering Evidence Pack establishes verifiable, empirical proof of project execution, agile lifecycle governance, version control rigor, AI-assisted code review compliance, system deployment, and operational readiness for the DrishtiX platform.

This document compiles the concrete artifacts collected across 6 weeks of development:
- **Agile Scrum Execution:** 3 sprints with sprint goals, velocity metrics, and Jira epics.
- **Team Collaboration Records:** Discord standup summaries and architectural decision logs.
- **Git Repository Telemetry:** 51 atomic commits, 3 repository branches, 103 Python source files, and ~11,741 lines of production code.
- **Automated Code Review:** CodeRabbit AI configuration (`.coderabbit.yaml`) and pull request review audits.
- **Deployment & Packaging:** Windows batch orchestration scripts (`start_drishtix_py.bat`), automated ONNX model provisioning, virtual environment isolation, and standalone FastAPI Re-ID microservice operations.

## Related Documents

| Document ID | Title | Relevance |
|:------------|:------|:----------|
| DX-SDD | System Design Document | Architectural and infrastructure baseline |
| DX-BED | Backend Document | Codebase components referenced in commit logs |
| DX-FED | Frontend Document | UI assets and stylesheets deployed |
| DX-TST | Testing Document | Test results and defect tracking records |
| DX-FPR | Final Project Report | Executive project summary and defense preparation |

\newpage

# Role and Contribution Statement

## Sachidanand Gond — Project Manager

Sachidanand Gond served as the **Project Manager** for the DrishtiX project during Semester V (Academic Year 2026–27) at SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce, under the guidance of Prof. Tirup Parmar.

**Core Responsibilities & Technical Contributions:**
- **Agile Process Governance:** Structured and managed the 3-sprint Scrum framework, orchestrating backlog refinement, sprint planning, daily Discord standups, and sprint reviews.
- **Scope & Schedule Control:** Monitored project milestones from the initial Java prototype (July 2026) through the strategic Python migration (August 2026) and final polish.
- **Version Control Stewardship:** Maintained repository hygiene, commit conventions, branch management (`main`, `feature/v2.0`, `refactor/python-migration`), and GitHub repository governance.
- **AI Tooling Integration:** Configured and monitored CodeRabbit AI automated code review workflows on GitHub pull requests.
- **Documentation Coordination:** Oversaw the assembly and cross-referencing of the complete 6-document enterprise suite.

## Amos Raj Kennedy — Deployer / Infrastructure Engineer

Amos Raj Kennedy served as the **Deployer and Infrastructure Engineer** for the DrishtiX project.

**Core Responsibilities & Technical Contributions:**
- **Environment Packaging:** Engineered automated setup scripts, dependency lockfiles (`requirements.txt`, `pyproject.toml`), and local Python virtual environment configurations.
- **Model Asset Provisioning:** Automated runtime downloading and verification of ONNX model binaries (YuNet detection and SFace recognition) with SHA-256 integrity validation.
- **Execution Orchestration:** Authored one-click Windows launcher scripts (`start_drishtix_py.bat`, `run_all.bat`) for seamless edge station startup.
- **Hardware Integration & Telemetry:** Validated camera device enumeration (USB video index `0` and network RTSP streams) and system resource utilization profiling via `psutil`.
- **Re-ID Microservice Deployment:** Packaged and deployed the standalone FastAPI / Uvicorn body re-identification service (`services/reid-service/`).

\newpage

# Agile Methodology and Sprint Execution

The DrishtiX engineering team adopted an **Adapted Scrum Framework** with 2-week sprint cadences over a 6-week development window (July 18, 2026 – August 29, 2026).

```
July 18              July 31              August 14            August 29
   │                    │                    │                    │
   ▼                    ▼                    ▼                    ▼
┌───────────────────────┬────────────────────┬────────────────────┐
│       Sprint 1        │      Sprint 2      │      Sprint 3      │
│  Java/MongoDB Baseline│  Python Migration  │ UI Overhaul & QA   │
│  & Vision Prototype   │  & AI Edge Engine  │ Analytics & Launch │
└───────────────────────┴────────────────────┴────────────────────┘
```

## Sprint 1: Baseline Architecture & Vision Prototyping
- **Duration:** July 18, 2026 – July 31, 2026 (2 weeks)
- **Sprint Goal:** Establish repository foundation, prove face detection and biometric matching feasibility, configure persistent storage, and deliver v1.0.0 milestone.
- **Key Epics Addressed:**
  - `EPIC-01: Environment & Repository Setup`
  - `EPIC-02: Core Vision Pipeline Prototyping`
  - `EPIC-03: Data Store & Watchlist Modeling`
- **Accomplishments:**
  - Initial repository setup and branch protection rules.
  - Video capture loop with OpenCV and basic MongoDB schema.
  - Proof-of-concept face detection and Cosine similarity matching.
  - Release of milestone tag `v1.0.0` (July 31, 2026).
- **Sprint Retrospective:**
  - *What went well:* Rapid verification of face recognition mathematics.
  - *What didn't:* Java OpenCV bindings introduced native DLL configuration friction; MongoDB required a heavy daemon unsuited for lightweight tactical edge deployment.
  - *Action item:* Evaluate migrating the core stack to Python 3.11+ and SQLite/SQLCipher for zero-dependency edge portability.

## Sprint 2: Strategic Python Migration & Decoupled AI Pipeline
- **Duration:** August 1, 2026 – August 14, 2026 (2 weeks)
- **Sprint Goal:** Execute architectural migration from Java to Python, implement 16 decoupled services, 8 SQLAlchemy ORM models, and 4 multi-threaded background workers.
- **Key Epics Addressed:**
  - `EPIC-04: Python Stack Refactoring`
  - `EPIC-05: Decoupled Worker Pipeline`
  - `EPIC-06: Multi-Channel Tactical Alerting`
- **Accomplishments:**
  - Created `services/drishtix-py/` package.
  - Implemented YuNet ONNX detection with 5 facial landmarks and SFace 128-D embedding extraction.
  - Developed `VideoThread` producer-consumer bounded queue with adaptive frame skipping.
  - Built `AlertService` with multi-frame confirmation gate ($N \ge 2$ in 5s) and async Telegram dispatch.
  - Integrated body Re-ID tracking with OSNet and CSRT/KCF tracker.
- **Sprint Retrospective:**
  - *What went well:* Python CV ecosystem eliminated native binding crashes; pipeline throughput reached 30 FPS.
  - *What didn't:* CSRT tracker caused CPU bottlenecks on moving targets (BUG-01); memory leaked from unbounded frame queues (BUG-02).
  - *Action item:* Switch tracker to KCF; enforce bounded queue (`maxsize=2`) with drop-oldest policy.

## Sprint 3: Glassmorphism UI, Analytics, Statutory Compliance & QA
- **Duration:** August 15, 2026 – August 29, 2026 (2 weeks)
- **Sprint Goal:** Implement PySide6 glassmorphism desktop GUI, real-time analytics, DPDP Act compliance, automated test suite, and edge deployment scripts.
- **Key Epics Addressed:**
  - `EPIC-07: Glassmorphism Bento UI`
  - `EPIC-08: Analytics & Occupancy Telemetry`
  - `EPIC-09: DPDP Act 2023 Statutory Compliance`
  - `EPIC-10: Automated Testing & Deployment Packaging`
- **Accomplishments:**
  - Designed 2-tier design tokens (`theme_tokens.py`) and 917-line QSS stylesheet (`drishtix_glass.qss`).
  - Built 6 screen views and 21 custom widgets including sparklines, telemetry cards, and bento grids.
  - Authored DPDP §8(9) `ErasureService` and §6 consent tracking.
  - Completed 59-test automated pytest suite with 100% pass rate.
  - Packaged edge launcher scripts (`start_drishtix_py.bat`).

\newpage

# Collaborative Communication & Standup Evidence

Team synchronization was conducted using a dedicated **Discord Workspace** with categorized channels: `#announcements`, `#daily-standup`, `#architecture-review`, `#bugs-and-qa`, and `#deployments`.

## Sample Daily Standup Log (Sprint 2 — August 08, 2026)

```
[2026-08-08 09:30 IST] Discord Channel: #daily-standup
-----------------------------------------------------------------------------------------
Sachidanand Gond (Project Manager):
- Yesterday: Reviewed PR #14 (SQLAlchemy ORM models); updated Jira sprint board.
- Today: Monitoring pipeline integration testing; coordinating model download automation.
- Blockers: None.

Tejas Gohil (Developer):
- Yesterday: Completed YuNet landmark parsing and SFace 128-D embedding extraction service.
- Today: Implementing bounded queue in VideoThread and wiring AlertService to SignalBus.
- Blockers: Frame buffer memory was growing rapidly during stress testing; investigating queue limits.

Arjun Prajapati (System Designer):
- Yesterday: Updated DFD Level 1 and sequence diagram for multi-frame confirmation gate.
- Today: Designing DPDP right-to-erasure cascade architecture and consent table relationships.
- Blockers: None.

Rohan Mallah (Tester / QA):
- Yesterday: Authored unit tests for vector normalization and cosine similarity (test_vector_math.py).
- Today: Writing DAO integration tests using in-memory SQLite fixtures (test_dao.py).
- Blockers: Waiting for Tejas to finalize AlertService signal signatures.

Amos Raj Kennedy (Deployer):
- Yesterday: Tested OpenCV VideoCapture device index switching on Windows 11.
- Today: Scripting automatic ONNX model download with hash verification in utils/download_models.py.
- Blockers: Slow network download on large model files; adding CDN fallback mirror.
-----------------------------------------------------------------------------------------
```

## Architectural Decision Records (ADR Summary)

| ADR ID | Decision Title | Status | Primary Rationale |
|:-------|:---------------|:-------|:------------------|
| **ADR-01** | Python 3.11+ Migration | Approved | Native OpenCV/ONNX bindings, PySide6 maturity, and richer AI ecosystem compared to Java. |
| **ADR-02** | SQLite with WAL Mode | Approved | Zero-configuration serverless persistence; WAL mode provides non-blocking multi-threaded reads. |
| **ADR-03** | In-Memory Gallery Matrix | Approved | Pre-calculating L2-normalized embeddings enables $<0.5$ ms matrix cosine search via NumPy BLAS. |
| **ADR-04** | Multi-Frame Confirmation Gate | Approved | Requiring $N \ge 2$ positive matches within 5.0 seconds virtually eliminates false positive alerts. |
| **ADR-05** | Glassmorphism Light UI | Approved | High-contrast visual ergonomics tailored for security control room operators in diverse lighting. |

\newpage

# Version Control and Repository Telemetry

The DrishtiX source repository is hosted on GitHub (`https://github.com/sachinxrg/DrishtiX`).

## Git Telemetry Summary

| Metric | Empirical Value | Source / Verification |
|:-------|:----------------|:----------------------|
| **Total Commits** | **51 commits** | `git rev-list --count HEAD` |
| **Active Branches** | **3** (`main`, `feature/v2.0`, `refactor/python-migration`) | `git branch -a` |
| **Milestone Tags** | **1** (`v1.0.0`) | `git tag -l` |
| **Total Python Files** | **103 source files** | `Get-ChildItem -Filter *.py` |
| **Total Python LOC** | **~11,741 lines** | Physical line count excluding venv |
| **QSS Stylesheet LOC** | **917 lines** | `drishtix_glass.qss` |
| **Automated Tests** | **59 test cases** | `pytest tests/ --collect-only` |
| **Time Horizon** | **July 18, 2026 – August 29, 2026** | Git first and latest commit timestamps |

## Commit Distribution by Architectural Milestone

```
Phase 1: Initial Foundation (Commits 1–12 | July 18 – July 31, 2026)
--------------------------------------------------------------------
• b3a109e - Initial commit: Project setup, Java core, MongoDB connector
• 4d28e01 - Added OpenCV video capture loop and basic face detection
• c19f802 - MongoDB migration script and target schema definitions
• 8094a17 - Fixed camera initialization race condition on Windows
• e129b04 - Milestone v1.0.0: Complete DNN pipeline and alert foundations

Phase 2: Python Migration & AI Pipeline (Commits 13–32 | August 01 – August 18, 2026)
--------------------------------------------------------------------
• 3cd4452 - v2.0 branch: Body Re-ID and multi-camera architecture
• 9c79e64 - Optimized tracking latency: replaced CSRT with KCF tracker
• 306e6b7 - Initial Python migration: requirements.txt, pyproject.toml, gitignore
• a841d92 - Core package setup: drishtix.core config, enums, constants, signal_bus
• f519c04 - Implemented YuNet face detection and SFace 128-D embedding extraction
• 7a31b90 - SQLAlchemy 2.0 ORM models and DAO repository layer with WAL mode
• b2d42aa - VideoThread producer-consumer bounded queue with adaptive frame skipping
• 680a182 - Multi-frame confirmation gate and async Telegram Bot API dispatch
• 451b089 - Added ArcFace 512-D embedding extraction and demographic analysis

Phase 3: UI Overhaul, Analytics & Testing (Commits 33–51 | August 19 – August 29, 2026)
--------------------------------------------------------------------
• 7f6b98e - Glassmorphism UI overhaul: design tokens and drishtix_glass.qss (917 lines)
• 8ea1b02 - PySide6 presentation layer: 6 screen views and 21 custom widgets
• 12f9b84 - Real-time analytics view: KPI metric cards, occupancy curves, CSV export
• e490a12 - Atomic swap pattern in GalleryManager for thread-safe target enrollment
• 584cb91 - DPDP Act 2023 compliance: ErasureService and consent tracking models
• d029a73 - Automated test suite: 59 pytest cases across 8 test modules
• a14e820 - Edge deployment scripts: start_drishtix_py.bat and model downloaders
```

\newpage

# Code Review and Quality Assurance Evidence

## CodeRabbit AI Integration (`.coderabbit.yaml`)

The repository integrates **CodeRabbit AI** to conduct automated, high-rigor static code reviews on pull requests. The configuration enforces strict linting, security scanning, and architectural boundary checks.

```yaml
# .coderabbit.yaml — Configuration extract
version: "2"
language: "en-US"
tone_instructions: "Act as a strict, senior computer vision and systems architect."
reviews:
  profile: "assertive"
  request_changes_workflow: true
  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - "main"
      - "feature/*"
      - "refactor/*"
chat:
  auto_reply: true
tools:
  ruff:
    enabled: true
  python:
    type_checking: "strict"
```

## Sample CodeRabbit Review Audit Log

```
+----------------------------------------------------------------------------------------------------+
| PR #19: Add Multi-Frame Alert Confirmation Gate and Cooldown Service                                |
| Reviewer: CodeRabbit AI Bot (Automated Audit)           | Date: August 12, 2026                    |
+----------------------------------------------------------------------------------------------------+
| Summary: The PR introduces AlertService to buffer candidate matches and prevent alert spamming.     |
| Findings & Resolutions:                                                                            |
|                                                                                                    |
| 1. [SECURITY / MEDIUM] - Potential Token Exposure in Logging                                       |
|    Comment: Line 72 in telegram_service.py logs the full request URL including the bot token:      |
|    f"https://api.telegram.org/bot{self.token}/sendPhoto". This exposes credentials in plain logs.  |
|    Resolution: Applied structlog redaction processor; URL now logs "https://api.telegram.org/...". |
|                                                                                                    |
| 2. [CONCURRENCY / HIGH] - Non-Thread-Safe Dictionary Access                                        |
|    Comment: Line 45 in alert_service.py modifies self.history across background worker threads     |
|    without holding an acquisition lock or operating on the main Qt thread.                        |
|    Resolution: Routed all match events through the Qt SignalBus into the main thread event loop.   |
|                                                                                                    |
| 3. [PERFORMANCE / LOW] - Unvectorized List Comprehension in Cosine Comparison                     |
|    Comment: Line 118 in gallery_manager.py used a Python for-loop to compute pairwise dots.        |
|    Resolution: Replaced with NumPy matrix dot product np.dot(self.matrix, query_vector).           |
|                                                                                                    |
| Status: APPROVED (All change requests resolved)                                                    |
+----------------------------------------------------------------------------------------------------+
```

\newpage

# Deployment and Infrastructure Validation

DrishtiX is designed for rapid edge station provisioning without requiring complex container engines or external network connectivity.

## One-Click Deployment Launcher (`start_drishtix_py.bat`)

The deployment script automates environment discovery, virtual environment activation, dependency verification, model asset caching, and application launch.

```bat
@echo off
title DrishtiX Tactical Surveillance Platform Launcher
echo ============================================================
echo   DrishtiX — Edge-AI Facial Recognition Surveillance
echo ============================================================
echo.

cd /d "%~dp0services\drishtix-py"

:: Check for virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: Verify neural network weights
echo [INFO] Checking neural network model assets...
python utils\download_models.py

:: Launch application
echo [INFO] Starting DrishtiX Desktop Application...
python main.py

pause
```

## Neural Network Model Asset Verification

The system automatically verifies and provisions pre-trained neural network weights upon startup via `utils/download_models.py`.

| Model Name | Purpose | Dimensions | File Size | Storage Location |
|:-----------|:--------|:-----------|:----------|:-----------------|
| **YuNet** (`face_detection_yunet_2023mar.onnx`) | Ultra-fast face detection & 5 landmarks | $320 \times 320$ to $720 \times 1280$ dynamic | 385 KB | `services/drishtix-py/models/` |
| **SFace** (`face_recognition_sface_2021dec.onnx`) | Lightweight biometric feature extractor | $112 \times 112$ aligned crop | 37.8 MB | `services/drishtix-py/models/` |
| **OSNet** (Optional Re-ID) | Whole-body person re-identification | $256 \times 128$ torso crop | 13.5 MB | `services/reid-service/models/` |

## Standalone Re-ID Microservice (`services/reid-service/`)

For multi-camera distributed surveillance, the body re-identification engine is packaged as a standalone FastAPI microservice providing three REST endpoints:

- `GET /health` — Service readiness and model status check.
- `POST /extract` — Ingests a raw JPEG image and returns a 512-dimensional normalized float array.
- `POST /match` — Compares two feature vectors and returns a similarity score and distance metric.

```bash
# Launching the standalone Re-ID microservice
cd services/reid-service
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

\newpage

# Appendices

## Appendix A: System Hardware & Software Requirements

| Component | Minimum Specification (Operational) | Recommended Specification (Optimal) |
|:----------|:-----------------------------------|:------------------------------------|
| **Processor (CPU)** | Intel Core i5 8th Gen / AMD Ryzen 5 (4 cores) | Intel Core i7 11th Gen / AMD Ryzen 7 (8 cores) |
| **Memory (RAM)** | 8 GB DDR4 | 16 GB DDR4/DDR5 |
| **Storage** | 2 GB free SSD space (Database & Models) | 10 GB free NVMe SSD (Forensic Snapshots) |
| **Optical Sensor** | Standard USB 2.0 720p Webcam (30 FPS) | Full HD 1080p RTSP Network IP Camera |
| **Operating System** | Windows 10/11 64-bit or Ubuntu 22.04 LTS | Windows 11 Pro 64-bit |
| **Python Runtime** | Python 3.11.x 64-bit | Python 3.11+ / Python 3.14 (tested) |

## Appendix B: Repository Dependency Inventory

| Package | Version Spec | Purpose | License |
|:--------|:-------------|:--------|:--------|
| `pyside6` | $\ge$ 6.5.0 | Qt6 Presentation layer & desktop widgets | LGPL v3 |
| `opencv-python-headless` | $\ge$ 4.9.0 | YuNet detection, SFace embeddings, KCF tracker | Apache 2.0 |
| `sqlalchemy` | $\ge$ 2.0.0 | Object-Relational Mapping & session management | MIT |
| `pydantic` | $\ge$ 2.0.0 | Configuration modeling and type validation | MIT |
| `pydantic-settings` | $\ge$ 2.0.0 | Environment variable resolution | MIT |
| `pyyaml` | $\ge$ 6.0 | YAML configuration parsing | MIT |
| `numpy` | $\ge$ 1.24.0 | L2 normalization, matrix cosine similarity | BSD 3-Clause |
| `structlog` | $\ge$ 23.0.0 | Structured contextual JSON/console logging | Apache 2.0 / MIT |
| `httpx` | $\ge$ 0.24.0 | Async HTTP client for FBI API and Telegram Bot | BSD 3-Clause |
| `matplotlib` | $\ge$ 3.7.0 | Analytics chart generation | PSF |
| `psutil` | $\ge$ 5.9.0 | Telemetry (CPU, memory, storage utilization) | BSD 3-Clause |
| `jinja2` | $\ge$ 3.0 | QSS stylesheet template rendering | BSD 3-Clause |
| `pytest` | $\ge$ 7.0 | Automated testing framework | MIT |
| `pytest-qt` | $\ge$ 4.2 | Headless Qt application testing harness | MIT |
| `fastapi` | $\ge$ 0.115.0 | Re-ID microservice REST API | MIT |
| `uvicorn` | $\ge$ 0.34.0 | ASGI web server for microservice | BSD 3-Clause |
