<div align="center">
  <img src="DRISHTIX logo.png" alt="DrishtiX Logo" width="300"/>

  # DrishtiX 
  **The Edge-AI Smart Surveillance & Facial Recognition Ecosystem**

  [![Java Version](https://img.shields.io/badge/Java-17%2B-blue.svg)](https://adoptium.net/)
  [![JavaFX Version](https://img.shields.io/badge/JavaFX-21-orange.svg)](https://openjfx.io/)
  [![OpenCV Version](https://img.shields.io/badge/OpenCV-4.9.0-green.svg)](https://opencv.org/)
  [![MongoDB Version](https://img.shields.io/badge/MongoDB-5.1.0%2B-brightgreen.svg)](https://www.mongodb.com/)
  [![Maven Build](https://img.shields.io/badge/Build-Maven-C71A22.svg)]()
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

  *Next-Generation Real-Time Anomaly Detection, Criminal Identification, and Automated Alerting for Enterprise Security.*
</div>

---

## 📑 Table of Contents
- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Tech Stack & Architecture](#-tech-stack--architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running Locally](#running-locally)
- [Usage](#-usage)
- [Roadmap / Future Scope](#-roadmap--future-scope)
- [Contributing](#-contributing)
- [License & Contact](#-license--contact)

---

## 🎯 About the Project

**DrishtiX** transforms ordinary camera feeds into proactive security perimeters. Traditional surveillance is passive—requiring human operators to monitor screens continuously. DrishtiX bridges this gap by leveraging advanced Deep Neural Networks (YuNet & SFace) directly at the edge to instantly cross-reference live video feeds against local and global registries (including automated ingestion of the FBI Wanted API). 

Whether deployed in corporate environments, retail sectors, or law enforcement scenarios, DrishtiX delivers sub-second facial recognition, tracks individuals using Re-ID bounding boxes, and automatically triggers multi-channel alerts (Telegram, Audio, and Desktop Toasts) the moment a high-value target or missing person is identified.

---

## ✨ Key Features

- **Real-Time Edge AI:** Blazing fast YuNet face detection coupled with SFace 128-dimensional facial embeddings for high-precision matching.
- **Background Global Ingestion:** Configurable background daemons automatically scrape and sync wanted profiles from the **FBI Wanted API** and other registries directly into your local MongoDB.
- **Ambient Glassmorphism UI:** A modern, highly responsive JavaFX Bento Grid dashboard providing live telemetry (FPS, Active Cameras, Detection Logs) without stuttering the inference thread.
- **Multi-Channel Alert Orchestration:** Seamless, fire-and-forget push notifications sent directly to field officers via Telegram bots, complete with live snapshot frames, case IDs, and confidence scores.
- **Zero-Latency Concurrency:** Engineered with a strict 5-tier isolated threading architecture ensuring that network I/O, database polling, and UI rendering never block the live video feed.

---

## 🏗️ Tech Stack & Architecture

### **Core Stack**
- **Language:** Java 17+
- **Build Tool:** Apache Maven
- **GUI:** JavaFX 21.0.2 (with ControlsFX for native toast notifications)
- **Computer Vision:** OpenCV 4.9.0 / JavaCV (YuNet, SFace, OSNet)
- **Database:** MongoDB (Sync Driver 5.1.0)
- **Web/Scraping:** JSoup & Java 11 `HttpClient`

### **System Architecture**
DrishtiX runs on a highly concurrent architecture to guarantee maximum frame throughput:
1. **JavaFX Application Thread:** Dedicated strictly to rendering the ambient UI.
2. **Video Inference Pool:** Captures frames and runs YuNet detection.
3. **Recognition Pool (Fixed=4):** Computes SFace embeddings via `CompletableFuture`.
4. **Audio & Telegram Daemon Pool:** Executes asynchronous sound playback and network REST calls.
5. **Ingestion Engine Pool (Scheduled):** Periodically polls external APIs (like FBI/CBI) in the background.

---

## 🚀 Getting Started

Follow these instructions to set up the DrishtiX development environment locally.

### Prerequisites

Ensure you have the following installed on your machine:
- [Java 17 JDK](https://adoptium.net/) (or higher)
- [MongoDB Community Server (v6.0+)](https://www.mongodb.com/try/download/community) running on port `27017`.
- [Git](https://git-scm.com/)
- A connected USB Webcam or integrated camera.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sachinxrg/DrishtiX.git
   cd DrishtiX
   ```

2. **Configure your Environment:**
   Copy the example properties file and insert your API keys:
   ```bash
   cp services/drishtix-app/config.properties.example services/drishtix-app/config.properties
   ```
   > **Note:** Open `config.properties` and replace `[Add your MongoDB URI here]`, your Telegram Bot credentials, and your FBI API key.

3. **Initialize the Database (Optional but recommended):**
   ```bash
   mongosh [Add your database URI here] database/drishtix_init.js
   ```

4. **Build the Application:**
   Use the included Maven wrapper to compile the source code and build the fat JAR.
   ```bash
   cd services/drishtix-app
   ./mvnw clean package
   ```

### Running Locally

To spin up the application locally using the compiled JAR:
```bash
java -jar target/drishtix-app-2.0.0-SNAPSHOT.jar
```
*(On the first boot, the system will automatically synthesize necessary audio files and establish a connection to your webcam).*

---

## 📖 Usage

### **Registering a Target**
Before DrishtiX can alert you, you must populate the registry.
1. Navigate to the **Target Index** tab in the UI.
2. Click **Add New Target** and provide a high-quality, frontal facial image.
3. Select a category (e.g., `CRIMINAL` or `MISSING_PERSON`).

*(Insert Screenshot here: Target Registry Interface)*

### **Monitoring the Dashboard**
1. Switch to the **Dashboard** view.
2. Click the **Start Camera** (circular toggle) button.
3. As registered individuals step into the frame, DrishtiX instantly outlines their faces, calculates the confidence score, and triggers the configured alerts.

*(Insert Screenshot here: Active Dashboard with Bounding Boxes)*

### **Handling FBI API Ingestion**
If `ingestion.enabled=true` is set in your config, DrishtiX will automatically poll the FBI Wanted API. You can manually inspect the logs to see the targets being injected into your live MongoDB registry.

---

## 🗺️ Roadmap / Future Scope

- [ ] **Multi-Camera Support:** RTSP stream multiplexing to support multiple IP cameras simultaneously.
- [ ] **Dockerization:** Package the entire application and MongoDB into an easily deployable `docker-compose` environment.
- [ ] **Advanced Re-ID Tracking:** Enhance OSNet spatial tracking for individuals across different camera zones.
- [ ] **Cloud Dashboard:** A web-based Next.js portal to remotely view detection logs from the edge devices.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License & Contact

Distributed under the MIT License. See `LICENSE` for more information.

**Project Maintainer:** Sachin  
**Project Link:** [https://github.com/sachinxrg/DrishtiX](https://github.com/sachinxrg/DrishtiX)

<div align="center">
  <i>Developed with precision for advanced security ecosystems.</i>
</div>
