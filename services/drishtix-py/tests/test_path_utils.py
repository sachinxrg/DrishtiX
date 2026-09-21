"""
Unit tests for portable storage paths.

The database stores where a snapshot or gallery photo lives, and a different
part of the app later reads that value back to open or delete the file. These
tests pin the property that actually matters: the two halves agree no matter
what the current working directory is.
"""

import os
from pathlib import Path

from drishtix.core.constants import GALLERY_DIR, PROJECT_ROOT, SNAPSHOTS_DIR
from drishtix.utils.path_utils import resolve_stored_path, to_stored_path


def test_stored_path_is_relative_to_project_root():
    """A file inside the project tree is stored as a root-relative path."""
    stored = to_stored_path(SNAPSHOTS_DIR / "det_7_1234567890.jpg")

    assert not Path(stored).is_absolute()
    assert stored == "data/snapshots/det_7_1234567890.jpg"


def test_round_trip_resolves_back_to_the_same_file():
    """to_stored_path and resolve_stored_path are inverses."""
    original = GALLERY_DIR / "target_John_Doe_20260101120000.jpg"

    assert resolve_stored_path(to_stored_path(original)) == original


def test_round_trip_is_independent_of_cwd(tmp_path):
    """
    The stored value must not depend on where the process was launched.

    This is the regression that mattered: the path used to be computed with
    os.path.relpath(..., Path.cwd()), so a snapshot written by a run started in
    one directory could not be found by a run started in another — the erasure
    service then deleted no image file at all, while reporting success.
    """
    original = SNAPSHOTS_DIR / "det_42_1700000000.jpg"

    cwd_before = Path.cwd()
    try:
        os.chdir(tmp_path)
        stored_elsewhere = to_stored_path(original)
        resolved_elsewhere = resolve_stored_path(stored_elsewhere)
    finally:
        os.chdir(cwd_before)

    stored_here = to_stored_path(original)

    assert stored_elsewhere == stored_here
    assert resolved_elsewhere == original


def test_path_outside_project_tree_stays_absolute():
    """
    There is no portable form for a file outside the project, so it is kept
    absolute rather than turned into a relative path pointing somewhere wrong.
    """
    outside = Path(PROJECT_ROOT.anchor) / "definitely_not_the_project" / "photo.jpg"

    stored = to_stored_path(outside)

    assert Path(stored).is_absolute()
    assert resolve_stored_path(stored) == Path(stored)
