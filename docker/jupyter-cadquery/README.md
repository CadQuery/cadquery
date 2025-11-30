# CadQuery + Jupyter Docker image

This directory contains a Docker image that provides:

- A ready-to-use **CadQuery** environment
- **JupyterLab** as the main user interface
- The **Jupyter-CadQuery** viewer extension for in-browser 3D visualization
- Optional **CQ-editor** inside the image (for advanced users who want a GUI in addition to Jupyter)

The goal is to offer a reproducible, cross-platform way to:

- Try CadQuery without touching your host Python installation
- Develop and run CadQuery notebooks and scripts
- Provide a consistent dev environment for contributors

The image is designed to work with:

- **Linux** (native Docker)
- **Windows** (Docker Desktop, Linux engine)
- **macOS / ARM devices** (via `linux/arm64` builds, where supported by Docker)

> CadQuery is installed using the conda-based workflow recommended in the official documentation, with `cadquery` coming from `conda-forge` / `cadquery` channels and Jupyter-CadQuery installed via `pip`. 

---

## Features

- **CadQuery** preinstalled with its dependencies
- **JupyterLab** with **Jupyter-CadQuery 4.x** for browser-based 3D viewing
- **CPU-only image** – no special GPU drivers needed in the container; rendering uses WebGL in your browser on the host
- **Multi-arch capable** Dockerfile:
  - `linux/amd64`
  - `linux/arm64` (for Docker Desktop on Apple Silicon, ARM servers, etc.)
- Optional **CQ-editor** in the image via a build argument

---

## Image contents

At a high level the image provides:

- Python 3.x
- CadQuery (installed via `mamba` from conda-forge / cadquery channels)
- JupyterLab
- Jupyter-CadQuery 4.x (`pip install jupyter-cadquery`)
- A non-root user (default: `cadquery`) with a simple home directory layout:

```text
/home/cadquery/
  ├── work/        # Your mounted project directory
  └── .conda/...   # Environment managed inside the image
