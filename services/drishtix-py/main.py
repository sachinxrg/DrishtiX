"""
DrishtiX v4.0 — Main Entry Point.

Usage:
    python main.py
"""

import signal
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from drishtix.app import create_app
from drishtix.dao.session import shutdown as shutdown_db


def main() -> int:
    """Launch DrishtiX Tactical Surveillance Node."""
    # Allow Ctrl+C to terminate cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        app, window, worker = create_app()
        window.show()

        exit_code = app.exec()

        # Clean shutdown
        if worker.is_running():
            worker.stop()
            worker.wait(1000)

        shutdown_db()
        return exit_code
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
