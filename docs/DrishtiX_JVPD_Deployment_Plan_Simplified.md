<![CDATA[# DrishtiX — JVPD Deployment Plan (Simplified)

> **Project**: DX-JVPD-2026 | **Budget**: ₹4.2–5.8 Crore | **Timeline**: Sep 2026 – Jul 2027

---

## What Is This Plan About?

We're upgrading DrishtiX from a **single laptop prototype** into a **city-block surveillance grid** covering the JVPD Scheme in Vile Parle West, Mumbai (~3.2 km²). The system will use AI to automatically detect wanted criminals and missing persons across **58 cameras** in real-time.

### The Three Stakeholders

| Partner | Role |
|---------|------|
| **Mumbai Police** (Zone IX) | Legal authority, FIR watchlist, existing CCTV feeds |
| **JVPD Residents' Association** | Infrastructure access, residential zone permissions |
| **Private Security** (Star Guardians, SIS) | Existing camera systems, on-ground response |

---

## Where: 5 Deployment Zones

| Zone | Location | Cameras | Why It Matters |
|------|----------|---------|----------------|
| 🔴 **Z1** | Mithibai–NM College Corridor | 12 | 6,000+ students daily, chain-snatching hotspot. Main chokepoint from Vile Parle station |
| 🟠 **Z2** | Juhu Tara Road (Celebrity Row) | 8 | VIP corridor — celebrity homes (Jalsa, etc.). Stalking & trespassing risk. Includes ANPR |
| 🟡 **Z3** | Nanavati Hospital (SV Road) | 10 | Hospital entry — organized crime convergence, high daily footfall |
| 🔵 **Z4** | Infinity Mall (New Link Road) | 16 | 15,000+ daily visitors, retail crime, weekend crowd surges |
| 🟢 **Z5** | Juhu Beach Corridor | 12 | 50,000+ weekend visitors, missing persons, harshest environment (salt air, monsoon) |

**Total: 58 cameras + 11 edge compute nodes**

---

## What We're Using: Hardware at a Glance

### Edge Compute: NVIDIA Jetson AGX Orin 64GB (×11 units)

Each zone gets 1–3 of these small, powerful AI computers:

- **AI Power**: 275 TOPS each (1,008× faster than a laptop)
- **Runs all 3 AI models** simultaneously: YuNet (face detection), SFace (face recognition), OSNet (body tracking)
- **Handles**: 4–8 camera streams per node at 25–30 FPS
- **Enclosure**: IP67 weatherproof box with active cooling for Mumbai's 42°C summers

### Cameras

| Type | Spec | Used At |
|------|------|---------|
| **PTZ** (Pan-Tilt-Zoom) | 4MP, 25× zoom, 150m night vision | All zones |
| **Fixed Dome** | 8MP, 120° wide view | Zones 3, 4 |
| **Thermal** | Sees through rain & darkness | Zone 5 (beach) |
| **ANPR** | Reads license plates | Zone 2 (VIP corridor) |

---

## How It Works: Camera → Officer's Phone

```
Camera Feed → AI Detection → Match Found? → Alert Sent
   (2ms)        (0.5ms)       (3ms)         (50ms)

Total: ~60ms per face (under 100ms target ✅)
```

**Step by step:**

1. **Camera captures** frame via RTSP stream
2. **YuNet AI** detects all faces in frame (up to 200 faces, <1ms on GPU)
3. **SFace AI** converts each face into a 128-number fingerprint (~3ms on GPU)
4. **Gallery match** — compares fingerprint against 10,000+ wanted persons
5. **If match found** → encrypted alert sent via fiber/5G to Central Command
6. **Alert pushed** to Telegram, WhatsApp, Mobile App, and Video Wall simultaneously

> **Key rule**: Raw video never leaves the zone. Only small alert packets (~50 KB) are transmitted.

---

## Network: How Zones Connect

```
Zone 1─┐                              ┌─ Telegram Bot
Zone 2─┤                              ├─ WhatsApp Business
Zone 3─┼── Fiber Ring (1 Gbps) ──── Central Command ──┼─ Mobile App (PWA)
Zone 4─┤   + 5G Backup               (Juhu PS)       ├─ 8-Screen Video Wall
Zone 5─┘   (WireGuard VPN)                           └─ Grafana Dashboard
```

- **Primary**: Dedicated fiber ring (1 Gbps) connecting all zones
- **Backup**: Jio 5G (especially for Zone 5 where fiber is limited)
- **Security**: All connections encrypted with WireGuard VPN (AES-256)
- **Central DB**: PostgreSQL + pgvector (replaces MySQL for 10K+ target scale)
- **Event Bus**: Apache Kafka (if one alert channel is down, alerts queue up safely)

---

## Mumbai-Specific Challenges & Solutions

### 🌡️ Heat (32–42°C, 95% humidity)

| Problem | Solution |
|---------|----------|
| Electronics overheat | IP67 enclosures with thermoelectric coolers, keep internals ≤50°C |
| Humidity causes corrosion | Conformal coating on circuit boards, silica gel desiccant packs |

### 🌧️ Monsoon (June–September, 2000+ mm rain)

| Problem | Solution |
|---------|----------|
| Rain blocks cameras | Wiper-equipped PTZ cameras + thermal cameras (see through rain) |
| Waterlogging | Equipment mounted 3m+ above ground on steel poles |

### 👥 Dense Crowds (up to 200 faces per frame)

| Scenario | Solution |
|----------|----------|
| College fest (200 faces) | Run face recognition only on entry/exit zones (reduces to 30–50 faces) |
| Beach weekend (150 faces) | 30-second cooldown prevents repeat alerts for same person |

---

## What Needs to Change in DrishtiX Software

| Current Limitation | Upgrade Needed |
|-------------------|----------------|
| Single-process app (crash = total failure) | Split into 4 microservices: capture, inference, alerting, API gateway |
| MySQL can't search AI vectors efficiently | Migrate central DB to PostgreSQL + pgvector (keeps local MySQL as backup) |
| Each node runs independently | Add Kafka-based gallery sync + cross-zone person re-identification |
| Gallery rebuild loads everything at once | Incremental sync — only push new/changed entries |

---

## Legal Compliance: DPDP Act 2023

> ⚠️ **Facial data = Sensitive Personal Data. Penalty for violations: up to ₹250 Crore.**

| Requirement | How We Comply |
|-------------|---------------|
| **Legal authority** | MoU with Mumbai Police — processing is lawful under Section 17(2) for public safety |
| **Notice** | Signage at all zones: *"This area is under AI-assisted video surveillance"* |
| **Only match watchlist** | Unrecognized faces are discarded immediately — no mass storage |
| **No raw video leaves zone** | Edge nodes process locally; only alert metadata is transmitted |
| **Data retention** | Snapshots auto-deleted after 90 days; audit logs kept 3 years |
| **Celebrity protection** | Zone 2 treats all non-watchlist faces as unknown — immediately discarded |
| **Right to erasure** | Anyone can request deletion via admin interface (unless linked to active FIR) |
| **Oversight** | Designated DPO from Mumbai Police Cyber Cell + annual CERT-In audit |

---

## Deployment Timeline

```
Phase 0 ──────── Phase 1 ──────── Phase 2 ──────── Phase 3
Sep–Oct 2026     Nov 2026–Jan 27  Feb–Apr 2027     May–Jul 2027
(8 weeks)        (12 weeks)       (12 weeks)       (12 weeks)
```

| Phase | What Happens |
|-------|-------------|
| **Phase 0 — Foundation** | MoU with Mumbai Police, DPDP assessment, site surveys, network design |
| **Phase 1 — Pilot (Zone 1)** | Install 2 Jetson + 12 cameras at Mithibai/NM corridor. Refactor app to microservices. 2-week live test |
| **Phase 2 — Expansion** | Roll out to Zones 2–5 (9 more Jetson + 46 cameras). Enable cross-zone tracking |
| **Phase 3 — Go Live** | Central Command video wall, mobile app launch, operator training, security audit, Full Operational Capability |

---

## At a Glance: Laptop → Enterprise

| | 🖥️ Today (Laptop) | 🏛️ Target (JVPD Grid) |
|---|---|---|
| **Cameras** | 1 webcam | 58 IP cameras |
| **AI Power** | ~3 TOPS | 3,025 TOPS (**1,008× more**) |
| **Watchlist** | ~100 people | 10,000+ people |
| **Speed** | ≤150ms | ≤95ms (**1.6× faster**) |
| **Coverage** | 1 room | ~3.2 km² (**213,000× more**) |
| **Alerts** | Telegram only | Telegram + WhatsApp + App + Video Wall |
| **Uptime** | Manual | 24/7, UPS-backed, auto-failover |
| **Compliance** | None | DPDP Act 2023, CERT-In audited |
| **Monthly Cost** | ₹0 | ~₹8–12 Lakhs |

---

> ⛔ **#1 Priority**: Sign the MoU with Mumbai Police **before** buying any hardware. Without legal authorization under IT Act Section 69A and DPDP Section 17(2), the entire project is at risk of legal injunction.

---

*Project Code: DX-JVPD-2026 | DrishtiX Systems Architecture Division | August 2026*
]]>
