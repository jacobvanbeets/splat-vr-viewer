# Splat VR Viewer

A [LichtFeld Studio](https://lichtfeld.io) plugin that lets you view Gaussian Splats in VR using WebXR.

## How It Works

1. Open a scene with a Gaussian Splat node in LichtFeld Studio
2. Go to the **Splat VR Viewer** panel
3. Click **Launch VR Viewer**
4. Your default browser opens with the splat loaded — click the VR button to enter immersive mode

The plugin exports the active splat as a PLY file, starts a lightweight localhost HTTP server, and opens the viewer in your browser. The viewer is built on [PlayCanvas](https://playcanvas.com/) with full WebXR support for VR headsets.

## Features

- **One-click launch** — exports and opens the viewer automatically
- **WebXR VR** — enter immersive VR with any SteamVR / OpenXR headset via Chrome or Edge
- **VR navigation** — thumbstick locomotion and teleportation
- **Orbit & fly camera** — standard 3D navigation on desktop
- **No external dependencies** — uses only Python's standard library (no pywebview, no Node.js)
- **Automatic cleanup** — temp files are removed on close and crash recovery

## Requirements

- [LichtFeld Studio](https://lichtfeld.io) with plugin support
- A modern browser with WebXR support (Chrome or Edge recommended)
- A VR headset with SteamVR or OpenXR runtime (for VR mode)

## Installation

Copy or clone this repo into your LichtFeld Studio plugins directory:

```
%USERPROFILE%\.lichtfeld\plugins\splat_vr_viewer\
```

LichtFeld Studio will detect the plugin on next launch.

## Project Structure

```
splat_vr_viewer/
├── __init__.py              # Plugin entry point (on_load / on_unload)
├── pyproject.toml           # Plugin metadata
├── core/
│   ├── __init__.py          # Temp file management & cleanup
│   └── launcher.py          # HTTP server + browser launcher
├── panels/
│   ├── splat_vr_panel.py    # LichtFeld Studio UI panel
│   └── splat_vr_panel.rml   # Panel layout template
└── viewer/
    ├── index.html           # Viewer HTML (PlayCanvas + WebXR)
    ├── viewer.js            # PlayCanvas engine + splat viewer
    └── viewer.css           # Viewer styles
```

## License

GPL-3.0-or-later
