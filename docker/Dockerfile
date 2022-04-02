# Usage:
#     docker run --rm -i cadquery python < ./box.py > box.svg
#     docker run --rm -it -v $(pwd)/examples:/home/cq cadquery

FROM continuumio/miniconda3:4.10.3

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

RUN conda create -n cq -c default -c conda-forge -c cadquery python=3.8 cadquery=master && \
    conda clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

WORKDIR /home/cq
USER cq

ENV PATH="/opt/conda/envs/cq/bin:${PATH}"
