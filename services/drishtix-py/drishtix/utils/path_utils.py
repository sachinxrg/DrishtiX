"""
DrishtiX v4.0 — Portable storage paths for the media the database points at.

Snapshots and gallery photos are written under data/ and their location is then
stored in SQLite, so the two halves have to agree across launches. A stored path
is therefore always relative to the project root, never to the current working
directory: PROJECT_ROOT is derived from the package location and is identical no
matter where the process was started from, while cwd is not.

Anchoring on cwd meant a snapshot written by a run started in one directory could
not be found by a run started in another — the erasure service then silently
failed to delete the face images it was legally required to remove, because
Path("data/snapshots/det_7.jpg").exists() was False from the new cwd.
"""

from pathlib import Path
from typing import Union

from drishtix.core.constants import PROJECT_ROOT


def to_stored_path(path: Union[str, Path]) -> str:
    """
    Convert a media path into the portable form that goes into the database.

    Returns a project-root-relative POSIX-style string for files inside the
    project tree. Files outside it have no portable form, so the absolute path
    is kept as-is — an honest absolute path beats a relative one that resolves
    somewhere wrong.

    Args:
        path: Absolute (or cwd-relative) path to the file just written.

    Returns:
        The string to persist in profile_image_path / snapshot_path.
    """
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def resolve_stored_path(stored: Union[str, Path]) -> Path:
    """
    Resolve a path read back out of the database into a real filesystem path.

    The inverse of to_stored_path: relative values are anchored to the project
    root, absolute values are returned unchanged. Rows written by earlier
    versions stay readable, since those were relative to the launch directory
    and the app is normally launched from the project root.

    Args:
        stored: Value of profile_image_path / snapshot_path as persisted.

    Returns:
        An absolute path suitable for .exists() / .unlink() / open().
    """
    path = Path(stored)
    return path if path.is_absolute() else PROJECT_ROOT / path
