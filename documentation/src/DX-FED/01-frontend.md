---
title: "DrishtiX — Frontend Document"
subtitle: "Document ID: DX-FED | Version 1.0"
author:
  - Tejas Gohil (Developer)
date: "September 2026"
subject: "Software Project Management"
keywords: ["DrishtiX", "Frontend", "PySide6", "Qt6", "UI/UX", "Glassmorphism"]
---

\newpage

| Field | Detail |
|:------|:-------|
| **Document ID** | DX-FED |
| **Title** | DrishtiX — Frontend Document |
| **Version** | 1.0 |
| **Date** | September 2026 |
| **Status** | Final |
| **Author(s)** | Tejas Gohil (Developer) |
| **Reviewer** | Prof. Tirup Parmar (Project Guide) |
| **Institution** | SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce |
| **Programme** | TY BSc IT, Semester V, 2026–27 |

## At a Glance

This document details the frontend architecture, design system, screen walkthrough, widget catalogue, user flows, and accessibility provisions of the DrishtiX desktop application. The presentation layer comprises 6 screen views, 21 custom widgets, a 917-line glassmorphism QSS stylesheet, and a 275-line design token architecture — delivering a modern, Apple/Figma-calibre user interface built entirely with PySide6 (Qt6).

## Related Documents

| Document ID | Title | Relevance |
|:------------|:------|:----------|
| DX-SDD | System Design Document | UI component hierarchy, use cases |
| DX-BED | Backend Document | Services and signal bus consumed by UI |
| DX-TST | Testing Document | UI component test cases |
| DX-FPR | Final Project Report | Overall summary |

\newpage

# Role and Contribution Statement

Tejas Gohil served as the **Developer** (covering both backend and frontend responsibilities) for the DrishtiX project during Semester V (Academic Year 2026–27) at SVKM's Usha Pravin Gandhi College of Arts, Science and Commerce.

**Frontend-specific responsibilities:**

- Designed and implemented the 6-screen PySide6 desktop interface with stacked view navigation
- Created the complete design token architecture (275 lines) with 2-tier Primitive/Semantic system
- Built 21 reusable custom Qt widgets (glass cards, KPI cards, charts, sparklines, etc.)
- Developed the 917-line glassmorphism QSS stylesheet (`drishtix_glass.qss`)
- Implemented responsive bento-grid layouts with ambient gradient mesh backgrounds
- Built real-time telemetry status bar with animated health indicators
- Connected all UI components to the backend SignalBus for thread-safe updates

**Tools used:** PySide6, Qt Designer (reference), Jinja2 (QSS generation), Python, Git.

\newpage

# Design System

## Design Philosophy

DrishtiX's UI is designed around three principles:

1. **Tactical clarity** — critical information (alerts, camera status, match confidence) is immediately visible without cognitive load
2. **Modern aesthetics** — glassmorphism, soft neumorphism, and ambient gradient mesh backgrounds create a premium, contemporary feel
3. **Operational efficiency** — one-click navigation, auto-refreshing views, and keyboard-friendly controls minimise friction

## Design Token Architecture

The design system is defined in `theme_tokens.py` (275 lines) using a 2-tier architecture:

### Primitive Layer (Raw Values)

| Token Family | Examples | Usage |
|:-------------|:---------|:------|
| Warm Slate scale | `SLATE_25` (#FAFBFC) through `SLATE_900` (#0F172A) | Text hierarchy, neutral surfaces |
| Indigo Accent | `INDIGO_500` (#4F6BFB) through `INDIGO_800` (#283593) | Interactive elements, active states |
| Emerald | `EMERALD_500` (#10B981) through `EMERALD_700` (#047857) | Safe/active status indicators |
| Amber | `AMBER_500` (#F59E0B) through `AMBER_700` (#B45309) | Warning indicators |
| Rose/Crimson | `ROSE_500` (#F43F5E) through `ROSE_900` (#7F1D1D) | Critical alerts, criminal category |
| Cyan/Sky | `CYAN_500` (#06B6D4) through `CYAN_DARK` (#0C4A6E) | Info indicators, missing person category |
| Mesh Gradients | `MESH_PURPLE` (#F0ECF8), `MESH_BLUE` (#ECEEFB) | Ambient background anchors |

### Semantic Layer (Named Tokens)

| Token Group | Tokens | Purpose |
|:------------|:-------|:--------|
| `Color.CANVAS` | Canvas, Canvas Alt | Application background (#F7F8FA) |
| `Color.SURFACE_*` | Glass, Glass Heavy, Glass Sidebar, Card | Semi-transparent card backgrounds |
| `Color.TEXT_*` | Primary, Body, Secondary, Muted, Placeholder | 5-level text hierarchy |
| `Color.ACCENT*` | Accent, Hover, Pressed, Soft, Tint, Border, Focus | Interactive element states |
| `Color.SAFE*` | Safe, Safe Bold, Safe BG, Safe Border | Emerald status indicators |
| `Color.WARNING*` | Warning, Warning Bold, Warning BG | Amber status indicators |
| `Color.CRITICAL*` | Critical, Critical Bold, Critical BG | Rose alert indicators |
| `Color.INFO*` | Info, Info Bold, Info BG | Cyan info indicators |
| `Color.ALERT_CRIMINAL_*` | 7 tokens | Criminal alert card colour set |
| `Color.ALERT_MISSING_*` | 8 tokens | Missing person alert card colour set |

### Additional Token Groups

| Group | Class | Tokens |
|:------|:------|:-------|
| Elevation | `Elevation` | `FLAT`, `RESTING`, `RAISED`, `HOVER`, `OVERLAY` (blur, offset, alpha) |
| Border Radius | `Radius` | `TILE` (22px), `CARD` (20px), `CONTROL` (12px), `PILL` (999px), `SMALL` (8px) |
| Spacing | `Spacing` | 8px-base scale: `XS` (4), `SM` (8), `MD` (12), `LG` (16), `XL` (20), `XXL` (24) |
| Breakpoints | `Breakpoint` | `COMPACT` (1100px), `MEDIUM` (1320px), `WIDE` (1500px) |
| Typography | `Typography` | 7-stop scale: Display (28), H1 (22), H2 (18), H3 (15), Body (13), Caption (11), Micro (10) |
| Animation | `Animation` | `FAST` (120ms), `NORMAL` (200ms), `SLOW` (320ms) |

## Glassmorphism QSS Stylesheet

The `drishtix_glass.qss` file (917 lines) is **auto-generated** from `theme_tokens.py` via `tools/generate_qss.py` (Jinja2 template). It styles all standard Qt widgets with:

| Technique | Implementation |
|:----------|:--------------|
| **Glassmorphism** | Semi-transparent `rgba(255,255,255,0.78–0.96)` backgrounds with white-border highlights |
| **Soft neumorphism** | Inset shadow variants for sunken controls (status bar capsules, inputs) |
| **Bento cards** | Rounded 20px containers with subtle hover border transitions |
| **Responsive typography** | Inter font family with -apple-system fallback chain |
| **State transitions** | Hover, pressed, checked, and disabled states for all interactive elements |
| **Category colouring** | Criminal (Rose) and Missing Person (Cyan) visual coding throughout |

**Font stack:** `"Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif`

**Code font:** `"JetBrains Mono", "Consolas", monospace`

\newpage

# Screen Walkthrough

## Application Shell

The main window (`MainWindow`, 244 lines) uses a 3-zone layout:

| Zone | Size | Content |
|:-----|:-----|:--------|
| Left sidebar | Fixed 240px | Brand logo, navigation buttons (6), version badge |
| Content area | Flexible, fills remaining space | `QStackedWidget` with 6 views |
| Status bar | Fixed 36px | Camera status, FPS, gallery count, RAM usage |

The content area optionally renders an `AmbientBackground` widget — an animated gradient mesh using two anchor colours (`MESH_PURPLE`, `MESH_BLUE`) — controlled by the `ENABLE_BENTO_UI` feature flag.

## Screen 0: Dashboard View

**Class:** `DashboardView` (8,329 bytes)

**Purpose:** Real-time CCTV monitoring with live video feed, detection overlay, and alert sidebar.

**Layout:**

| Component | Widget | Description |
|:----------|:-------|:------------|
| Video panel | `VideoLabel` | Renders annotated frames from `frame_ready` signal; displays bounding boxes with category-coloured borders and confidence labels |
| Alert sidebar | `AlertSidebar` | Sliding panel showing `AlertCard` widgets for each confirmed match |
| Metrics row | `KPICard` × 3 | Total detections, active targets, system uptime |
| System health | `SystemHealthCard` | Camera status, FPS counter, memory usage |

**Signal connections:**

- `signal_bus.frame_ready` → `VideoLabel.update_frame()`
- `signal_bus.alert_created` → `AlertSidebar.add_alert()`
- `signal_bus.fps_updated` → StatusBar FPS capsule

## Screen 1: Target Registry View

**Class:** `RegistryView` (18,951 bytes — largest UI view)

**Purpose:** Watchlist management with CRUD operations.

**Layout:**

| Component | Description |
|:----------|:------------|
| Header | "Target Registry" title with search bar and "Add Target" button |
| Filter bar | Category filter pills (All, Criminal, Missing Person), active/inactive toggle |
| Target grid | Responsive grid of glass cards, each showing: profile photo, name, category pill badge, case number, photo count, creation date |
| Add/Edit dialog | Modal with fields: full name, category dropdown, case number, description, photo upload zone with drag-and-drop |

**Key interactions:**

- **Add Target** → opens modal dialog → validates input → calls `TargetDAO.create_target()` → extracts embeddings → reloads gallery
- **Delete Target** → confirmation dialog → calls `TargetDAO.delete_target()` → emits `targets_changed`
- **Search** → real-time text filter on name, case number, description

## Screen 2: Detection Logs View

**Class:** `DetectionLogView` (10,271 bytes)

**Purpose:** Historical audit log of all detection events.

**Layout:**

| Component | Description |
|:----------|:------------|
| Filter bar | Date range picker, category filter, target search |
| Table | Columns: Timestamp, Target Name, Category, Confidence, Snapshot, Camera |
| Snapshot modal | Click-to-expand snapshot with full detection details |
| Export button | CSV export via `ExportService` |
| Pagination | Page controls for large result sets |

## Screen 3: Analytics & KPIs View

**Class:** `AnalyticsView` (7,845 bytes)

**Purpose:** Visual analytics dashboard with KPI metrics and detection charts.

**Layout (bento grid):**

| Component | Widget | Description |
|:----------|:-------|:------------|
| KPI row | `KPICard` × 4 | Total detections, unique targets, detection rate, avg confidence |
| Category chart | `ChartWidget` | Pie/bar chart: Criminal vs Missing Person breakdown |
| Timeline chart | `ChartWidget` | Line chart: detections over time |
| Hourly heat | `ActivityHeatmap` | Hour-of-day detection heatmap |
| Top targets | Table | Most frequently detected targets |

## Screen 4: Forensic Scanner View

**Class:** `ImageScanView` (10,798 bytes)

**Purpose:** Batch static image recognition against the enrolled watchlist.

**Workflow:**

1. User uploads one or more images via drag-and-drop or file browser
2. System runs YuNet face detection on each image
3. For each detected face: extract embedding, match against gallery
4. Results displayed in a grid: face crop, match/no-match status, target name, confidence

## Screen 5: Settings & Configuration View

**Class:** `SettingsView` (12,877 bytes)

**Purpose:** Runtime system configuration.

**Sections:**

| Section | Controls |
|:--------|:---------|
| Camera | Source selector (device index / RTSP URL), resolution, FPS target |
| Detection | Score threshold slider (0.0–1.0), NMS threshold, inference interval |
| Recognition | Engine selector (SFace / InsightFace), match threshold slider |
| Alerts | Cooldown seconds spinner, Telegram enable toggle, bot token, chat ID |
| Database | Encryption key input, retention days spinner |
| System | Log level selector, feature flags |

All settings are validated via Pydantic and emit `config_changed` signal for live updates.

\newpage

# Widget Catalogue

DrishtiX includes 21 custom PySide6 widgets in the `ui/widgets/` package:

| Widget | Lines | Purpose |
|:-------|:------|:--------|
| `VideoLabel` | 135 | High-performance video frame renderer with aspect-ratio scaling |
| `AlertCard` | 154 | Individual alert notification card with snapshot thumbnail and metadata |
| `AlertSidebar` | 130 | Scrollable container for alert cards with "Clear All" action |
| `GlassCard` | 93 | Reusable glassmorphic container with elevation states |
| `KPICard` | 141 | Metric display card with title, value, trend indicator, and sparkline |
| `NavButton` | 28 | Sidebar navigation button with icon, label, and active-state highlight |
| `PillBadge` | 128 | Status indicator pill with 4 status variants (Safe, Warning, Critical, Info) |
| `StatusBar` | 165 | Real-time telemetry bar: camera, FPS, gallery size, RAM, latency |
| `BentoGrid` | 129 | Responsive grid layout manager for dashboard tiles |
| `ChartWidget` | 189 | Matplotlib-backed chart with glass card integration |
| `Sparkline` | 114 | Miniature inline line chart for trend indication |
| `CircularProgress` | 94 | Animated circular progress indicator |
| `ConfidenceBar` | 75 | Horizontal bar showing match confidence with colour gradient |
| `SectionHeader` | 72 | Section title with optional subtitle and divider line |
| `FrostedPanel` | 128 | Frosted-glass background panel with blur effect |
| `SystemHealthCard` | 148 | Combined health indicators (camera, DB, memory) |
| `ActivityHeatmap` | 103 | Hour-of-day activity heatmap visualisation |
| `TimelineStrip` | 117 | Horizontal timeline of detection events |
| `EmptyState` | 99 | Placeholder shown when views have no data (icon + message + action) |
| `AmbientBackground` | 57 | Animated gradient mesh background widget |

## Key Widget: VideoLabel

The `VideoLabel` widget handles high-frequency frame rendering (30 FPS) with minimal allocation:

```python
class VideoLabel(QLabel):
    def update_frame(self, pixmap: QPixmap, detections: list):
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)
        self.setPixmap(scaled)
```

Connected to `signal_bus.frame_ready` — Qt automatically marshals the call to the UI thread.

## Key Widget: AlertCard

Displays a confirmed match alert with:

- **Snapshot thumbnail** (52×52 px) with category-coloured border
- **Target name** and **category pill** (Criminal = Rose, Missing = Cyan)
- **Confidence percentage** with colour-coded bar
- **Timestamp** (relative format: "2m ago")
- **Case number** (if available)

\newpage

# Navigation Model

## View Router

The `MainWindow._select_view(index)` method handles all navigation:

1. Sets `content_stack.setCurrentIndex(index)` — O(1) switch
2. Updates navigation button states (`setChecked`)
3. Triggers data refresh for the target view:
   - Index 0 (Dashboard): `refresh_metrics()`
   - Index 1 (Registry): `load_targets()`
   - Index 2 (Logs): `load_logs()`
   - Index 3 (Analytics): `refresh_dashboard()`

## User Journey: Target Enrolment

1. User clicks "Target Registry" in sidebar → view 1 activates
2. User clicks "Add Target" → registration dialog opens
3. User fills name, selects category, uploads photo(s)
4. User clicks "Save" → system validates, extracts embedding, persists
5. Dialog closes → registry refreshes → new target card appears
6. User returns to Dashboard → gallery is already reloaded in background

## User Journey: Alert Response

1. Dashboard is active with live feed
2. Face is detected and matched (confidence > threshold)
3. Multi-frame confirmation achieved (2 hits in 5 seconds)
4. Alert sound plays → AlertCard slides into sidebar → Telegram notification fires
5. User clicks AlertCard → snapshot modal opens with full details
6. User navigates to Detection Logs → event appears in chronological table

\newpage

# Responsive Layout and Breakpoints

The UI uses 3 responsive breakpoints:

| Breakpoint | Width | Layout |
|:-----------|:------|:-------|
| **Compact** | < 1100px | Single-column, stacked cards |
| **Medium** | 1100–1500px | 6-column bento grid |
| **Wide** | > 1500px | 12-column full bento grid |

The `BentoGrid` widget dynamically recalculates column spans based on the parent widget's width, using the `Breakpoint` tokens from `theme_tokens.py`.

**Minimum window size:** 1080 × 700 px (set in `MainWindow.__init__`)

**Default window size:** 1380 × 880 px

\newpage

# Accessibility

| Feature | Implementation |
|:--------|:--------------|
| Font sizing | Configurable via Qt stylesheet; minimum 10px (Micro) |
| Colour contrast | All text tokens satisfy WCAG AA on glass surfaces (Slate 600 on white = 5.74:1) |
| Category coding | Colour is paired with text labels ("CRIMINAL", "MISSING PERSON") for colour-blind accessibility |
| Empty states | Descriptive placeholder messages with action buttons (not blank screens) |
| Status bar | Real-time telemetry in text format, not icon-only |
| Sound alerts | Visual alert cards always accompany audio alerts |

\newpage

# UI Testing

The frontend is tested via `test_ui_components.py` (12,207 lines) using `pytest-qt`. Key test categories:

| Category | Tests | Description |
|:---------|:------|:------------|
| Widget instantiation | 21 | Verify all custom widgets can be created without errors |
| Signal-slot wiring | 8 | Verify SignalBus connections update UI state correctly |
| View navigation | 6 | Verify QStackedWidget transitions and data refresh calls |
| Data binding | 5 | Verify DAO data renders correctly in table and card views |
| Theme application | 3 | Verify QSS stylesheet loads without parse errors |
| Empty states | 6 | Verify placeholder widgets appear when no data is available |

See DX-TST for the complete test plan.

\newpage

# Screenshots

> **Note:** DrishtiX is a PySide6 desktop application that requires a camera device, ONNX model files, and a display server to run. Screenshots cannot be generated programmatically in a headless environment. See `MANUAL_ACTIONS.md` for capture instructions.

**Planned screenshot inventory:**

| ID | Screen | State | Capture Instructions |
|:---|:-------|:------|:--------------------|
| SS-01 | Dashboard | Camera active with live feed | Start app with camera connected; wait for feed |
| SS-02 | Dashboard | Alert triggered | Present an enrolled target's face to camera |
| SS-03 | Dashboard | Alert sidebar with cards | After multiple matches, capture sidebar state |
| SS-04 | Target Registry | Grid with targets | Enrol 3+ targets; capture the grid view |
| SS-05 | Target Registry | Add Target dialog | Click "Add Target"; capture the open dialog |
| SS-06 | Detection Logs | Table with entries | After some detections, navigate to Logs view |
| SS-07 | Analytics | KPI cards and charts | Navigate to Analytics after 10+ detections |
| SS-08 | Forensic Scanner | Scan results | Upload test images; capture results view |
| SS-09 | Settings | Configuration panel | Navigate to Settings view |
| SS-10 | Status Bar | Telemetry indicators | Capture the bottom status bar while camera is active |

\newpage

# Challenges and Solutions

| Challenge | Solution |
|:----------|:---------|
| Qt thread safety for UI updates | Used `SignalBus` with `AutoConnection` — Qt automatically marshals cross-thread signals to the receiver's event loop |
| Glassmorphism in Qt (no CSS backdrop-filter) | Achieved via QSS `rgba()` backgrounds with carefully calibrated opacity values; `FrostedPanel` adds manual blur |
| High-frequency frame rendering (30 FPS) | `VideoLabel` uses `setPixmap()` on pre-scaled QPixmaps; no intermediate buffer copies |
| Responsive layout without CSS flexbox/grid | Custom `BentoGrid` widget computes column spans based on parent width and breakpoint tokens |
| QSS maintenance across 917 lines | Auto-generated from `theme_tokens.py` via Jinja2 template — single source of truth prevents style drift |
| Alert card memory management | AlertCards are capped at 50 instances; oldest cards are removed when limit is reached |
