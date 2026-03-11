# SPDX-License-Identifier: GPL-3.0-or-later
"""Local HTTP server for serving the splat viewer and exported files."""

import os
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class _ViewerHandler(SimpleHTTPRequestHandler):
    """Serves viewer static files and a /splat_file route for the exported PLY."""

    splat_file_path: str = ""

    def do_GET(self):
        if self.path.startswith("/splat_file"):
            self._serve_splat_file()
        else:
            super().do_GET()

    def _serve_splat_file(self):
        splat_path = self.splat_file_path
        if not splat_path or not os.path.isfile(splat_path):
            self.send_error(404, "No splat file available")
            return

        file_size = os.path.getsize(splat_path)
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(file_size))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        with open(splat_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def log_message(self, format, *args):
        # Silence request logging
        pass


class ViewerServer:
    """Manages a background HTTP server for the splat viewer."""

    def __init__(self):
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._port: int = 0

    @property
    def port(self) -> int:
        return self._port

    @property
    def running(self) -> bool:
        return self._server is not None

    @property
    def url(self) -> str:
        if not self._port:
            return ""
        return f"http://localhost:{self._port}"

    def start(self, viewer_dir: str | Path, splat_file_path: str) -> str:
        """Start the server. Returns the base URL."""
        if self._server is not None:
            self.stop()

        viewer_dir = str(viewer_dir)

        handler_class = partial(
            _ViewerHandler, directory=viewer_dir
        )
        # Set the splat file path on the class so all instances can access it
        _ViewerHandler.splat_file_path = splat_file_path

        # Bind to port 0 to get an available port
        self._server = HTTPServer(("127.0.0.1", 0), handler_class)
        self._port = self._server.server_address[1]

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="splat-vr-server",
        )
        self._thread.start()

        return self.url

    def update_splat_path(self, splat_file_path: str):
        """Update the path to the served splat file (for re-export)."""
        _ViewerHandler.splat_file_path = splat_file_path

    def stop(self):
        """Shut down the server."""
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._port = 0
