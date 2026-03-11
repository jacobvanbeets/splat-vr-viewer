# SPDX-License-Identifier: GPL-3.0-or-later
"""Splat VR Viewer — view Gaussian Splats in VR from LichtFeld Studio."""

import lichtfeld as lf

from .panels.splat_vr_panel import SplatVrViewerPanel


def on_load():
    lf.register_class(SplatVrViewerPanel)


def on_unload():
    from .core.launcher import close_viewer

    close_viewer()
    lf.unregister_class(SplatVrViewerPanel)
