"""
DrishtiX v4.0 — Main Entry Point.

Usage:
    python main.py
"""

# ruff: noqa: E402 — the drishtix imports below need the sys.path bootstrap first.

import logging
import signal
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from drishtix.app import create_app
from drishtix.dao.session import shutdown as shutdown_db

logger = logging.getLogger(__name__)


def _install_excepthook() -> None:
    """
    Log unhandled exceptions instead of letting Qt abort the process.

    PySide6 terminates the application when a Python exception escapes a slot
    invoked from C++ (a signal handler, a timer, a button click). A single
    transient DB or camera error in any slot would therefore kill the whole
    surveillance node. Logging keeps the app alive and the failure visible.
    """
    def hook(
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_tb: Optional[TracebackType],
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.error(
            "Unhandled exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )

    sys.excepthook = hook


def main() -> int:
    """Launch DrishtiX Tactical Surveillance Node."""
    # Allow Ctrl+C to terminate cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    _install_excepthook()

    exit_code = 1
    worker = None
    ingestion_worker = None

    try:
        app, window, worker, ingestion_worker = create_app()
        window.show()

        exit_code = app.exec()
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        # Clean shutdown — both worker threads, then the DB engine. Runs even
        # when startup or app.exec() raises, so threads and the SQLAlchemy
        # engine are never leaked.
        try:
            if worker is not None and worker.is_running():
                worker.stop()
                worker.wait(1000)

            if ingestion_worker is not None and ingestion_worker.is_running():
                ingestion_worker.stop()

            shutdown_db()
        except Exception:
            traceback.print_exc()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
