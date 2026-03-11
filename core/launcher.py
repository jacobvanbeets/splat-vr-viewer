# SPDX-License-Identifier: GPL-3.0-or-later
"""Launcher for the Splat VR Viewer.

Runs a lightweight HTTP server in a daemon thread and opens the viewer
in the user's default browser.  This gives full WebXR / VR support
(unlike pywebview's WebView2 which can't create immersive sessions).
"""

import json
import threading
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

# The running server instance and its thread
_server: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None


class _QuietHandler(SimpleHTTPRequestHandler):
    """Serves files from a fixed directory without printing every request."""

    def log_message(self, format, *args):  # noqa: A002
        pass  # suppress console spam


def _write_config(viewer_dir: Path, node_name: str, settings_path: Path) -> None:
    """Write ``_config.json`` into the viewer directory.

    The HTML page fetches this on load to get the node name and settings
    without needing a pywebview bridge.
    """
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception:
        settings = {
            "camera": {"fov": 60, "startAnim": "none", "animTrack": None},
            "background": {"color": [0.2, 0.2, 0.2]},
            "animTracks": [],
        }

    config = {"nodeName": node_name, "settings": settings}
    config_path = viewer_dir / "_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)


def launch_viewer(ply_path: str, node_name: str, viewer_dir: Path) -> None:
    """Start the HTTP server and open the viewer in the default browser.

    Raises
    ------
    RuntimeError
        If the server fails to start.
    """
    global _server, _server_thread

    # Shut down any existing server first
    close_viewer()

    # Write config JSON so the HTML page can pick up metadata
    settings_path = viewer_dir / "settings.json"
    _write_config(viewer_dir, node_name, settings_path)

    # Create a handler rooted in the viewer directory
    handler = partial(_QuietHandler, directory=str(viewer_dir))

    # Bind to an ephemeral port on localhost
    _server = HTTPServer(("127.0.0.1", 0), handler)
    port = _server.server_address[1]

    _server_thread = threading.Thread(
        target=_server.serve_forever,
        daemon=True,
        name="splat-vr-http",
    )
    _server_thread.start()

    # Open the viewer in the user's default browser
    url = f"http://127.0.0.1:{port}/index.html"
    webbrowser.open(url)


def close_viewer() -> None:
    """Shut down the HTTP server if it is running."""
    global _server, _server_thread
    if _server is not None:
        _server.shutdown()
        _server = None
    if _server_thread is not None:
        _server_thread.join(timeout=3)
        _server_thread = None


def is_viewer_open() -> bool:
    """Return True if the HTTP server is still running."""
    return _server_thread is not None and _server_thread.is_alive()
