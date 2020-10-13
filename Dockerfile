FROM continuumio/miniconda3

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN useradd -ms /bin/bash cq

WORKDIR /home/cq/

USER root

RUN apt-get install -y libgl1-mesa-glx

RUN conda install -c cadquery -c conda-forge cadquery=master

USER cq
