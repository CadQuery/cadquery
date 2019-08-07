FROM nvidia/cudagl:10.1-base
LABEL source="https://github.com/CadQuery/cadquery/tree/master/docker" \
      issues="https://github.com/CadQuery/cadquery/issues" \
      license="https://github.com/CadQuery/cadquery/blob/master/LICENSE"

ARG INSTALL_PREFIX=/cadquery2

# Upgrade packages
RUN apt-get update && \
    apt-get -y upgrade

# Install dependencies
RUN apt-get install -y curl cmake g++ libfreetype6-dev libfontconfig1-dev freeglut3-dev swig python3 python3-dev python3-pip
RUN pip3 install six pyparsing

# Install OCE
ARG OCE_VERSION=master
RUN mkdir -p $INSTALL_PREFIX/oce/cmake-build && \
    curl -L https://github.com/tpaviot/oce/tarball/${OCE_VERSION} | \
        tar zx -C $INSTALL_PREFIX/oce --strip-components=1 && \
    cd $INSTALL_PREFIX/oce/cmake-build && \
    cmake .. && \
    make -j9 && \
    make install/strip && \
    make test

# Install PythonOCC-core's cadquery fork
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/
ARG PYTHONOCC_CORE_VERSION=master
RUN mkdir -p $INSTALL_PREFIX/pythonocc-core/cmake-build && \
    curl -L https://github.com/CadQuery/pythonocc-core/tarball/${PYTHONOCC_CORE_VERSION} | \
        tar zx -C $INSTALL_PREFIX/pythonocc-core --strip-components=1 && \
    cd $INSTALL_PREFIX/pythonocc-core/cmake-build && \
    cmake -DOCE_INCLUDE_PATH=/usr/local/include/oce -DOCE_LIB_PATH=/usr/local/lib .. && \
    make -j9 && \
    make install && \
    cd ../test && \
    python3 run_tests.py

ARG CADQUERY_VERSION=master
# Install CadQuery
RUN mkdir $INSTALL_PREFIX/cadquery && \
    curl -L https://github.com/CadQuery/cadquery/tarball/${CADQUERY_VERSION} | \
        tar zx -C $INSTALL_PREFIX/cadquery --strip-components=1 && \
    cd $INSTALL_PREFIX/cadquery && \
    python3 setup.py install --single-version-externally-managed --record=record.txt && \
    python3 runtests.py

# Clean system
# RUN cd / && rm -rf $INSTALL_PREFIX
# RUN pip3 uninstall six pyparsing
# RUN apt-get autoremove git cmake g++ libfreetype6-dev libfontconfig1-dev freeglut3-dev swig python3-dev python3-pip

COPY cadquery.sh cadquery.sh

# Run CadQuery CLI script
ENTRYPOINT ["./cadquery.sh"]
