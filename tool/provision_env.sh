#!/usr/bin/env bash

#
# generate project environment
#

eval "$(conda shell.bash hook)"

# build enviro
conda env remove -y -n cq_build
conda create     -y -n cq_build python=3.7

conda activate         cq_build

# build support
conda install -y -c conda-forge \
	conda-build \
	conda-verify \

# cadquery deps
conda install -y -c conda-forge \
    pythonocc-core=7.4.0 \

conda config --show
