FROM nvidia/cudagl:10.1-base
LABEL source="https://github.com/roipoussiere/cadquery/tree/master/docker" \
      issues="https://github.com/roipoussiere/cadquery/issues" \
      license="https://github.com/roipoussiere/cadquery/blob/master/LICENSE"

ARG INSTALL_PREFIX=/cadquery2
RUN mkdir $INSTALL_PREFIX

# Update packages
RUN apt-get update && \
    apt-get -y upgrade

# Install dependencies
RUN apt-get install -y git cmake g++ libfreetype6-dev libfontconfig1-dev freeglut3-dev swig python3 python3-dev python3-pip
RUN pip3 install six pyparsing

# Install OCE
RUN git clone git://github.com/tpaviot/oce.git $INSTALL_PREFIX/oce && \
    mkdir $INSTALL_PREFIX/oce/cmake-build && \
    cd $INSTALL_PREFIX/oce/cmake-build && \
    cmake .. && \
    make -j9 && \
    make install/strip && \
    make test

# Install PythonOCC-core's cadquery fork
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/
RUN git clone https://github.com/CadQuery/pythonocc-core.git $INSTALL_PREFIX/pythonocc-core && \
    mkdir $INSTALL_PREFIX/pythonocc-core/cmake-build && \
    cd $INSTALL_PREFIX/pythonocc-core/cmake-build && \
    cmake -DOCE_INCLUDE_PATH=/usr/local/include/oce -DOCE_LIB_PATH=/usr/local/lib .. && \
    make -j9 && \
    make install && \
    cd ../test && \
    python3 run_tests.py

# Install CadQuery
RUN git clone https://github.com/CadQuery/cadquery.git $INSTALL_PREFIX/cadquery && \
    cd $INSTALL_PREFIX/cadquery && \
    python3 setup.py install --single-version-externally-managed --record=record.txt && \
    python3 runtests.py

ENTRYPOINT ["python3", "-c"]
CMD ["import cadquery; print('cadquery.Workplane('XY').box(1,2,3).toSvg()')"]
