# CadQuery + Jupyter-CadQuery container
# - Multi-arch via mambaorg/micromamba
# - Default: JupyterLab + jupyter-cadquery (browser viewer)
# - Optional: CQ-editor GUI (Linux + X11)

FROM mambaorg/micromamba:2.3.0-ubuntu22.04

# Ensure conda "base" env is activated in RUN steps (see micromamba-docker docs)
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# ---- System packages (minimal) ----
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        # Dependencies useful for CQ-editor / OpenGL on Linux
        libgl1-mesa-glx \
        libgl1-mesa-dri \
        libglu1-mesa \
        libxrender1 \
        libxext6 \
        libxkbcommon0 \
        libxi6 \
        fonts-dejavu-core \
        # For nice shell experience if you drop into the container
        bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the unprivileged micromamba user provided by the base image
USER $MAMBA_USER
WORKDIR /home/$MAMBA_USER

# ---- Core conda environment: Python + CadQuery + Jupyter ----
# Channels: conda-forge + cadquery, as recommended in the official docs.
RUN micromamba install -y -n base \
        -c conda-forge -c cadquery \
        python=3.11 \
        cadquery \
        jupyterlab \
        ipywidgets \
    && micromamba clean --all --yes

# ---- Jupyter-CadQuery viewer (pip) ----
# Jupyter-CadQuery 4.x supports CadQuery >= 2.5 and uses ocp_vscode/three-cad-viewer. :contentReference[oaicite:3]{index=3}
RUN pip install --no-cache-dir "jupyter-cadquery>=4.0.2"

# ---- Optional CQ-editor (GUI) ----
# Build arg lets you choose whether to pull CQ-editor into this image.
# Build with: `--build-arg WITH_CQEDITOR=true` to enable.
ARG WITH_CQEDITOR=false
RUN if [ "$WITH_CQEDITOR" = "true" ]; then \
        micromamba install -y -n base -c cadquery -c conda-forge cq-editor && \
        micromamba clean --all --yes; \
    fi

# Workspace inside the container
RUN mkdir -p /home/$MAMBA_USER/work

# Jupyter port
EXPOSE 8888

# Default: start JupyterLab with no token, serving /home/mambauser/work
# (Micromamba's entrypoint will auto-activate the "base" env.)
CMD ["bash", "-lc", "jupyter lab \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --notebook-dir=/home/mambauser/work"]
