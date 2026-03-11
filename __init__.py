# SPDX-License-Identifier: GPL-3.0-or-later
"""Splat VR Viewer — view Gaussian Splats in VR from LichtFeld Studio."""

import lichtfeld as lf

from .core import cleanup_temp_files
from .panels.splat_vr_panel import SplatVrViewerPanel


def on_load():
    # Clean up any temp files left over from a previous crash/freeze
    cleanup_temp_files()
    lf.register_class(SplatVrViewerPanel)


def on_unload():
    from .core.launcher import close_viewer

    close_viewer()
    cleanup_temp_files()
    lf.unregister_class(SplatVrViewerPanel)
