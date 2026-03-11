# SPDX-License-Identifier: GPL-3.0-or-later
"""Native window launcher using pywebview for the splat VR viewer."""

import threading
from typing import Optional


_window = None
_webview_thread: Optional[threading.Thread] = None
_webview_started = threading.Event()


def launch_viewer(url: str, title: str = "Splat VR Viewer"):
    """Open the viewer in a native window via pywebview.

    If a window is already open, navigates it to the new URL.
    """
    global _window, _webview_thread

    try:
        import webview
    except ImportError:
        raise ImportError(
            "pywebview is required. Install via: pip install pywebview"
        )

    # If already running, just navigate to the new URL
    if _window is not None:
        try:
            _window.load_url(url)
            return
        except Exception:
            # Window was closed or invalid — recreate
            _window = None

    _webview_started.clear()

    def _run():
        global _window
        _window = webview.create_window(
            title,
            url,
            width=1280,
            height=720,
            resizable=True,
            min_size=(640, 480),
        )
        _webview_started.set()
        webview.start(gui="edgechromium", debug=False)
        # Window was closed
        _window = None

    _webview_thread = threading.Thread(
        target=_run,
        daemon=True,
        name="splat-vr-webview",
    )
    _webview_thread.start()
    _webview_started.wait(timeout=10.0)


def close_viewer():
    """Close the viewer window if open."""
    global _window
    if _window is not None:
        try:
            _window.destroy()
        except Exception:
            pass
        _window = None


def is_viewer_open() -> bool:
    """Check if the viewer window is still open."""
    return _window is not None
