FROM nvidia/cudagl:10.1-base

ARG INSTALL_PREFIX=/app

# Update packages
RUN apt-get update && \
    apt-get -y upgrade

# Install dependencies
RUN apt-get install -y curl cmake g++ libfreetype6-dev libfontconfig1-dev freeglut3-dev
# swig python3 python3-dev python3-pip
#RUN pip3 install six

# Install OCE
ARG OCE_VERSION=OCE-0.18.3
RUN mkdir -p $INSTALL_PREFIX/oce/cmake-build && \
    curl -L https://github.com/tpaviot/oce/archive/${OCE_VERSION}.tar.gz | \
        tar zx -C $INSTALL_PREFIX/oce --strip-components=1 && \
    cd $INSTALL_PREFIX/oce/cmake-build && \
    cmake .. && \
    make -j$(nproc) && \
    make install/strip && \
    make test
