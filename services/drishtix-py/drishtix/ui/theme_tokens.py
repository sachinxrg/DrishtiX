"""
DrishtiX v5.0 — Design Token Architecture.

Single source of truth for all visual tokens. Two-tier system:
  Primitive layer → raw color/spacing values (private to this file)
  Semantic layer  → named tokens that widgets, views, and QSS templates import

Light theme with Apple/Figma-caliber glassmorphism, soft neumorphism,
subtle mesh backgrounds, and rich visual telemetry.
"""

from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════════════════
#  PRIMITIVE LAYER — Raw values.
# ═══════════════════════════════════════════════════════════════════════════

class Primitive:
    """Raw palette values. Internal only — use the Semantic layer below."""

    # Warm Slate scale (refined for light theme warmth)
    SLATE_25  = "#FAFBFC"
    SLATE_50  = "#F7F8FA"
    SLATE_100 = "#F0F2F6"
    SLATE_150 = "#EAEFF5"
    SLATE_200 = "#E1E5EC"
    SLATE_300 = "#CAD1DC"
    SLATE_400 = "#94A0B2"
    SLATE_500 = "#64748B"
    SLATE_600 = "#475569"   # WCAG AA on glass surfaces
    SLATE_700 = "#334155"
    SLATE_800 = "#1E293B"
    SLATE_900 = "#0F172A"

    # Indigo Accent (Vibrant, modern)
    INDIGO_500 = "#4F6BFB"
    INDIGO_600 = "#3E56E0"
    INDIGO_700 = "#3347C7"
    INDIGO_800 = "#283593"
    INDIGO_50  = "#EEF2FF"
    INDIGO_100 = "#E0E7FF"
    INDIGO_200 = "#C7D2FE"

    # Semantic: Safe / Active (Emerald)
    EMERALD_500 = "#10B981"
    EMERALD_600 = "#059669"
    EMERALD_700 = "#047857"
    EMERALD_50  = "#ECFDF5"
    EMERALD_100 = "#D1FAE5"
    EMERALD_200 = "#A7F3D0"

    # Semantic: Warning / Alert (Amber)
    AMBER_500   = "#F59E0B"
    AMBER_600   = "#D97706"
    AMBER_700   = "#B45309"
    AMBER_50    = "#FFFBEB"
    AMBER_100   = "#FEF3C7"
    AMBER_200   = "#FDE68A"

    # Semantic: Critical / Danger (Rose / Crimson)
    ROSE_500    = "#F43F5E"
    ROSE_600    = "#DC2626"
    ROSE_700    = "#B91C1C"
    ROSE_800    = "#991B1B"
    ROSE_900    = "#7F1D1D"
    ROSE_50     = "#FFF1F2"
    ROSE_100    = "#FEE2E2"
    ROSE_200    = "#FECDD3"
    ROSE_300    = "#FDA4AF"
    ROSE_400    = "#FCA5A5"

    # Semantic: Info / Missing (Cyan / Sky)
    CYAN_500    = "#06B6D4"
    CYAN_600    = "#0891B2"
    CYAN_700    = "#0E7490"
    CYAN_800    = "#0369A1"
    CYAN_SKY    = "#0284C7"
    CYAN_50     = "#ECFEFF"
    CYAN_100    = "#E0F2FE"
    CYAN_200    = "#BAE6FD"
    CYAN_300    = "#7DD3FC"
    CYAN_VIVID  = "#00D4FF"
    CYAN_DARK   = "#0C4A6E"
    CYAN_DEEP   = "#075985"
    CYAN_LIGHT  = "#38BDF8"
    CYAN_A5F3FC = "#A5F3FC"

    # Mesh Gradient Anchors
    MESH_PURPLE = "#F0ECF8"
    MESH_BLUE   = "#ECEEFB"

    # Pure
    WHITE = "#FFFFFF"
    BLACK = "#000000"


# ═══════════════════════════════════════════════════════════════════════════
#  SEMANTIC LAYER
# ═══════════════════════════════════════════════════════════════════════════

class Color:
    """Named semantic colors."""

    # Canvas / Background
    CANVAS              = Primitive.SLATE_50
    CANVAS_ALT          = Primitive.SLATE_100
    CANVAS_MESH_A       = Primitive.MESH_BLUE
    CANVAS_MESH_B       = Primitive.MESH_PURPLE

    # Glass Surfaces (rgba strings for QSS)
    SURFACE_GLASS        = "rgba(255,255,255,0.78)"
    SURFACE_GLASS_HEAVY  = "rgba(255,255,255,0.88)"
    SURFACE_GLASS_SIDEBAR = "rgba(255,255,255,0.96)"
    SURFACE_CARD         = "rgba(255,255,255,0.82)"

    # Borders
    BORDER_HAIRLINE      = "rgba(255,255,255,0.92)"
    BORDER_HAIRLINE_INK  = "rgba(15,23,42,0.06)"
    BORDER_SUBTLE        = Primitive.SLATE_200
    BORDER_MUTED         = Primitive.SLATE_300

    # Text hierarchy
    TEXT_PRIMARY         = Primitive.SLATE_900
    TEXT_BODY            = Primitive.SLATE_700
    TEXT_SECONDARY       = Primitive.SLATE_600   # AA-safe on glass
    TEXT_MUTED           = Primitive.SLATE_500
    TEXT_PLACEHOLDER     = Primitive.SLATE_400

    # Accent
    ACCENT               = Primitive.INDIGO_600  # #3E56E0 (5.62:1 on white, passes WCAG AA)
    ACCENT_HOVER         = Primitive.INDIGO_700  # #3347C7
    ACCENT_PRESSED       = Primitive.INDIGO_800  # #283593
    ACCENT_SOFT          = Primitive.INDIGO_50
    ACCENT_TINT          = Primitive.INDIGO_100
    ACCENT_BORDER        = Primitive.INDIGO_200
    ACCENT_FOCUS         = "rgba(62,86,224,0.30)"
    ACCENT_GRADIENT_START = "#4F6BFB"
    ACCENT_GRADIENT_END   = "#3E56E0"

    # Neumorphic surfaces
    NEU_SURFACE          = Primitive.SLATE_100
    NEU_HIGHLIGHT        = Primitive.WHITE
    NEU_SHADOW           = Primitive.SLATE_300

    # Status: Safe / Active
    SAFE                 = Primitive.EMERALD_500
    SAFE_BOLD            = Primitive.EMERALD_700  # #047857
    SAFE_BG              = Primitive.EMERALD_50
    SAFE_BORDER          = Primitive.EMERALD_200

    # Status: Review / Warning
    WARNING              = Primitive.AMBER_500
    WARNING_BOLD         = Primitive.AMBER_700   # #B45309
    WARNING_BG           = Primitive.AMBER_50
    WARNING_BORDER       = Primitive.AMBER_200

    # Status: Critical / Danger
    CRITICAL             = Primitive.ROSE_500
    CRITICAL_BOLD        = Primitive.ROSE_600    # #DC2626
    CRITICAL_DARK        = Primitive.ROSE_700
    CRITICAL_BG          = Primitive.ROSE_50
    CRITICAL_BORDER      = Primitive.ROSE_200

    # Status: Info / Missing
    INFO                 = Primitive.CYAN_500
    INFO_BOLD            = Primitive.CYAN_600
    INFO_SKY             = Primitive.CYAN_800    # #0369A1
    INFO_BG              = Primitive.CYAN_50
    INFO_BORDER          = Primitive.CYAN_A5F3FC
    INFO_LIGHT_BG        = Primitive.CYAN_100
    CYAN_VIVID           = Primitive.CYAN_VIVID

    # Alert card specifics (criminal)
    ALERT_CRIMINAL_FG        = Primitive.ROSE_800
    ALERT_CRIMINAL_CASE      = Primitive.ROSE_900
    ALERT_CRIMINAL_THUMB_BG  = Primitive.ROSE_50
    ALERT_CRIMINAL_THUMB_BD  = "rgba(239,68,68,0.45)"
    ALERT_CRIMINAL_MATCH_BD  = "#F87171"
    ALERT_CRIMINAL_DEMO_BG   = Primitive.ROSE_100
    ALERT_CRIMINAL_DEMO_BD   = Primitive.ROSE_300

    # Alert card specifics (missing)
    ALERT_MISSING_FG         = Primitive.CYAN_DARK
    ALERT_MISSING_CASE       = Primitive.CYAN_800
    ALERT_MISSING_THUMB_BG   = Primitive.CYAN_50
    ALERT_MISSING_THUMB_BD   = "rgba(6,182,212,0.45)"
    ALERT_MISSING_MATCH_BD   = Primitive.CYAN_LIGHT
    ALERT_MISSING_DEMO_BG    = Primitive.CYAN_100
    ALERT_MISSING_DEMO_BD    = Primitive.CYAN_200
    ALERT_MISSING_TS         = Primitive.CYAN_DEEP

    # Pure
    WHITE                    = Primitive.WHITE


@dataclass(frozen=True)
class ShadowPreset:
    """Drop shadow configuration for elevation tier."""
    blur: int
    y_offset: int
    alpha: float


class Elevation:
    """4-tier elevation scale for depth hierarchy."""
    FLAT    = ShadowPreset(blur=0,  y_offset=0,  alpha=0.00)
    RESTING = ShadowPreset(blur=14, y_offset=2,  alpha=0.05)
    RAISED  = ShadowPreset(blur=22, y_offset=4,  alpha=0.09)
    HOVER   = ShadowPreset(blur=22, y_offset=4,  alpha=0.09)  # Backward compat alias
    OVERLAY = ShadowPreset(blur=38, y_offset=10, alpha=0.15)


class Radius:
    """Border radius scale."""
    TILE     = 22   # Hero panels / bento tiles
    CARD     = 20   # Standard glass cards
    CONTROL  = 12   # Buttons, inputs, tables
    PILL     = 999  # Status badges, pill buttons
    SMALL    = 8    # Tabs, tooltips
    CAPSULE  = 8    # Status bar telemetry capsules
    CHECKBOX = 4    # Checkbox indicators


class Spacing:
    """8px-base layout spacing constants."""
    XS            = 4
    SM            = 8
    MD            = 12
    LG            = 16
    XL            = 20
    XXL           = 24
    BENTO_GAP     = 16   # Gap between bento tiles (px)
    BENTO_GAP_LG  = 18   # Large gap variant
    CARD_PADDING  = 16   # Internal card padding
    VIEW_MARGIN   = 16   # View-level margin


class Breakpoint:
    """Responsive layout breakpoints (widget width in px)."""
    COMPACT = 1100   # Single-column bento
    MEDIUM  = 1320   # 6-column bento
    WIDE    = 1500   # 12-column full bento


@dataclass(frozen=True)
class TypeStyle:
    """Typography style definition."""
    size: int
    weight: int
    line_height: float
    letter_spacing: float


class Typography:
    """Font family stacks and 7-stop type scale."""
    SANS  = '"Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif'
    MONO  = '"JetBrains Mono", "Consolas", monospace'

    # 7-Stop Type Scale
    DISPLAY = TypeStyle(size=28, weight=700, line_height=1.2, letter_spacing=-0.5)
    H1      = TypeStyle(size=22, weight=700, line_height=1.25, letter_spacing=-0.3)
    H2      = TypeStyle(size=18, weight=700, line_height=1.3, letter_spacing=-0.2)
    H3      = TypeStyle(size=15, weight=600, line_height=1.35, letter_spacing=-0.1)
    BODY    = TypeStyle(size=13, weight=500, line_height=1.4, letter_spacing=0.0)
    CAPTION = TypeStyle(size=11, weight=500, line_height=1.35, letter_spacing=0.2)
    MICRO   = TypeStyle(size=10, weight=600, line_height=1.3, letter_spacing=0.4)


class Animation:
    """Micro-animation duration tokens (ms)."""
    DURATION_FAST   = 120
    DURATION_NORMAL = 200
    DURATION_SLOW   = 320
