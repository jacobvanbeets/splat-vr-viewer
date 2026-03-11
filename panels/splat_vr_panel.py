# SPDX-License-Identifier: GPL-3.0-or-later
"""Splat VR Viewer panel — export the active splat and view in a native window."""

import threading
from pathlib import Path
from typing import Optional

import lichtfeld as lf
from lfs_plugins.types import RmlPanel

from ..core import cleanup_temp_files, get_temp_ply_path
from ..core.launcher import launch_viewer, close_viewer, is_viewer_open

# Viewer web assets directory (sibling of panels/)
_VIEWER_DIR = Path(__file__).resolve().parent.parent / "viewer"


class SplatVrViewerPanel(RmlPanel):
    """Panel for launching the Gaussian Splat VR viewer."""

    idname = "splat_vr_viewer.main_panel"
    label = "Splat VR Viewer"
    space = "MAIN_PANEL_TAB"
    order = 110
    rml_template = str(Path(__file__).resolve().with_name("splat_vr_panel.rml"))
    update_interval_ms = 500

    def __init__(self):
        self._handle = None
        self._status = "Ready"
        self._is_error = False
        self._target_name = ""
        self._gaussian_count = ""
        self._temp_ply: Optional[str] = None
        self._exporting = False

    # ── Data Model ───────────────────────────────────────────────────

    def on_bind_model(self, ctx):
        model = ctx.create_data_model("splat_vr_viewer")
        if model is None:
            return

        model.bind_func("target_label",
                         lambda: self._target_name or "No splat selected")
        model.bind_func("gaussian_count", lambda: self._gaussian_count)
        model.bind_func("has_target", lambda: bool(self._target_name))
        model.bind_func("status_text", lambda: self._status)
        model.bind_func("is_error", lambda: self._is_error)
        model.bind_func("is_running", lambda: is_viewer_open())
        model.bind_func("launch_label", lambda: "Launch VR Viewer")
        model.bind_func("refresh_label", lambda: "Re-export & Refresh")
        model.bind_func("stop_label", lambda: "Close Viewer")

        model.bind_event("launch", self._on_launch)
        model.bind_event("refresh", self._on_refresh)
        model.bind_event("stop", self._on_stop)

        self._handle = model.get_handle()

    def on_load(self, doc):
        pass

    def on_update(self, doc):
        self._refresh_target()

        # Detect if the webview window was closed externally
        if not is_viewer_open() and self._status == "Viewer running":
            cleanup_temp_files()
            self._status = "Viewer closed"
            self._dirty_all()

        return False

    def on_scene_changed(self, doc):
        self._refresh_target()

    # ── Internals ────────────────────────────────────────────────────

    def _dirty_all(self):
        if self._handle:
            self._handle.dirty_all()

    def _refresh_target(self):
        """Update the target splat node from the current scene."""
        old_name = self._target_name
        scene = lf.get_scene()
        if not scene:
            self._target_name = ""
            self._gaussian_count = ""
            if old_name:
                self._dirty_all()
            return

        # Find first SPLAT node: prefer selected, else first in scene
        selected = lf.get_selected_node_names()
        splat_node = None
        for name in selected:
            node = scene.get_node(name)
            if node and str(node.type).endswith("SPLAT"):
                splat_node = node
                break

        if splat_node is None:
            for node in scene.get_nodes():
                if str(node.type).endswith("SPLAT"):
                    splat_node = node
                    break

        if splat_node is not None:
            self._target_name = splat_node.name
            count = splat_node.gaussian_count
            self._gaussian_count = f"{count:,}" if count else "—"
        else:
            self._target_name = ""
            self._gaussian_count = ""

        if self._target_name != old_name:
            self._dirty_all()

    def _get_splat_data(self):
        """Get SplatData for the target node."""
        scene = lf.get_scene()
        if not scene or not self._target_name:
            return None
        node = scene.get_node(self._target_name)
        if not node:
            return None
        return node.splat_data()

    def _export_and_launch(self):
        """Export the splat to a temp PLY and open the viewer."""
        self._exporting = True
        self._status = "Exporting PLY…"
        self._is_error = False
        self._dirty_all()

        try:
            splat_data = self._get_splat_data()
            if splat_data is None:
                self._status = "No splat data available"
                self._is_error = True
                self._exporting = False
                self._dirty_all()
                return

            # Clean up previous export before writing a new one
            cleanup_temp_files()
            temp_path = get_temp_ply_path()
            lf.io.save_ply(splat_data, temp_path)
            self._temp_ply = temp_path

            self._status = "Launching viewer…"
            self._dirty_all()

            # Start HTTP server and open viewer in default browser
            launch_viewer(temp_path, self._target_name, _VIEWER_DIR)

            self._status = "Viewer running"
            self._is_error = False

        except Exception as e:
            self._status = f"Error: {e}"
            self._is_error = True
            lf.log.error(f"Splat VR Viewer: {e}")
        finally:
            self._exporting = False
            self._dirty_all()

    def _on_launch(self, _handle, _ev, _args):
        """Handle launch button click."""
        if self._exporting:
            return
        thread = threading.Thread(
            target=self._export_and_launch,
            daemon=True,
            name="splat-vr-export",
        )
        thread.start()

    def _on_refresh(self, _handle, _ev, _args):
        """Re-export the current splat and reopen the viewer."""
        if self._exporting:
            return
        thread = threading.Thread(
            target=self._export_and_launch,
            daemon=True,
            name="splat-vr-refresh",
        )
        thread.start()

    def _on_stop(self, _handle, _ev, _args):
        """Close the viewer window."""
        close_viewer()
        cleanup_temp_files()
        self._status = "Stopped"
        self._is_error = False
        self._dirty_all()
