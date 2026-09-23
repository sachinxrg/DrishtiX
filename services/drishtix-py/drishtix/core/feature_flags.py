"""
DrishtiX v4.0 — Feature Flags.

Runtime feature gates for incremental UI rollout.
Read from environment variables with sensible defaults.
"""

import os


def _bool_env(name: str, default: bool = True) -> bool:
    """Read a boolean from an environment variable."""
    val = os.environ.get(name, "").strip().lower()
    if val in ("0", "false", "no", "off"):
        return False
    if val in ("1", "true", "yes", "on"):
        return True
    return default


# Gate new bento/glass layouts. Set DRISHTIX_ENABLE_BENTO_UI=0 to revert
# to the pre-refactor layout without touching code.
ENABLE_BENTO_UI: bool = _bool_env("DRISHTIX_ENABLE_BENTO_UI", default=True)
