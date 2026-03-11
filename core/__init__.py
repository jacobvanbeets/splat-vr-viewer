# SPDX-License-Identifier: GPL-3.0-or-later
"""Temp file management for the Splat VR Viewer plugin.

The exported PLY and config JSON are written into the ``viewer/`` directory
so the localhost HTTP server can serve them to the browser.  A secondary
temp directory is kept for any other scratch files.
"""

import tempfile
from pathlib import Path

# The viewer/ directory (served by the localhost HTTP server)
_VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"

# Fixed filenames inside viewer/
_EXPORT_PLY_NAME = "_export.ply"
_CONFIG_JSON_NAME = "_config.json"

# Secondary temp directory for any other scratch files
TEMP_DIR = Path(tempfile.gettempdir()) / "lf_splat_vr_viewer"


def get_temp_ply_path() -> str:
    """Return the path where the exported PLY should be written.

    The file is placed inside ``viewer/`` so the HTTP server can
    serve it directly to the browser.
    """
    return str(_VIEWER_DIR / _EXPORT_PLY_NAME)


def cleanup_temp_files() -> None:
    """Delete all temp/export files created by this plugin.

    Safe to call at any time — silently ignores missing or locked files.
    """
    # Clean generated files in the viewer directory
    for name in (_EXPORT_PLY_NAME, _CONFIG_JSON_NAME):
        path = _VIEWER_DIR / name
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

    # Clean the secondary temp directory
    if TEMP_DIR.exists():
        for entry in TEMP_DIR.iterdir():
            try:
                if entry.is_file():
                    entry.unlink()
            except OSError:
                pass
        try:
            TEMP_DIR.rmdir()
        except OSError:
            pass
