# SPDX-License-Identifier: GPL-3.0-or-later
"""Native window launcher using pywebview with a JS API bridge.

The viewer loads entirely from local files — no HTTP server is needed.
PLY data is transferred from Python to JavaScript via the pywebview bridge.
"""

import base64
import json
import threading
from pathlib import Path
from typing import Optional


class SplatBridge:
    """pywebview JS API — exposes splat data and settings to the viewer page.

    JavaScript calls these methods via ``window.pywebview.api.<method>()``.
    """

    def __init__(self, ply_path: str, settings_path: str, node_name: str):
        self._ply_path = ply_path
        self._settings_path = settings_path
        self._node_name = node_name

    def get_node_name(self) -> str:
        """Return the name of the splat node being viewed."""
        return self._node_name

    def get_settings(self) -> dict:
        """Return the viewer settings.json as a dict."""
        try:
            with open(self._settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "camera": {"fov": 60, "startAnim": "none", "animTrack": None},
                "background": {"color": [0.2, 0.2, 0.2]},
                "animTracks": [],
            }

    def get_splat_base64(self) -> str:
        """Read the exported PLY file and return it as a base64 string."""
        with open(self._ply_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")


# ---------------------------------------------------------------------------
#  Module-level window state
# ---------------------------------------------------------------------------

_window = None
_webview_thread: Optional[threading.Thread] = None
_webview_started = threading.Event()


def _path_to_file_url(p: Path) -> str:
    """Convert a local Path to a ``file://`` URL."""
    posix = p.resolve().as_posix()
    if not posix.startswith("/"):
        posix = "/" + posix
    return "file://" + posix


def launch_viewer(ply_path: str, node_name: str, viewer_dir: Path):
    """Open the VR viewer in a native window.

    Parameters
    ----------
    ply_path:
        Path to the exported ``.ply`` file.
    node_name:
        Display name for the splat node.
    viewer_dir:
        Path to the ``viewer/`` directory containing index.html, viewer.js, etc.
    """
    global _window, _webview_thread

    try:
        import webview  # noqa: F811
    except ImportError:
        raise ImportError(
            "pywebview is required. Install via: pip install pywebview"
        )

    # Close any existing window first
    if _window is not None:
        try:
            _window.destroy()
        except Exception:
            pass
        _window = None

    settings_path = str(viewer_dir / "settings.json")
    bridge = SplatBridge(ply_path, settings_path, node_name)
    index_url = _path_to_file_url(viewer_dir / "index.html")

    _webview_started.clear()

    def _run():
        global _window
        _window = webview.create_window(
            f"{node_name} — Splat VR Viewer",
            index_url,
            js_api=bridge,
            width=1280,
            height=720,
            resizable=True,
            min_size=(640, 480),
        )
        _webview_started.set()
        webview.start(gui="edgechromium", debug=False)
        # webview.start() blocks until all windows are closed
        _window = None

    _webview_thread = threading.Thread(
        target=_run,
        daemon=True,
        name="splat-vr-webview",
    )
    _webview_thread.start()
    _webview_started.wait(timeout=10.0)


def close_viewer():
    """Close the viewer window if it is open."""
    global _window
    if _window is not None:
        try:
            _window.destroy()
        except Exception:
            pass
        _window = None


def is_viewer_open() -> bool:
    """Return True if the viewer window is still open."""
    return _window is not None
