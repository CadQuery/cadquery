#!/usr/bin/env bash

eval "$(conda shell.bash hook)"

conda activate cq_build

export PYTHON_VERSION=3.7
export PACKAGE_VERSION=TEST

conda config --show channels

conda build . -c conda-forge --croot /tmp/cq_build
