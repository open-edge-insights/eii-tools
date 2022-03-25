# Copyright (c) 2020 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Dockerfile for TimeSeriesProfiler

ARG EII_VERSION
ARG DOCKER_REGISTRY
ARG ARTIFACTS="/artifacts"
ARG EII_UID
ARG EII_USER_NAME
ARG UBUNTU_IMAGE_VERSION
FROM ia_eiibase:$EII_VERSION as base
FROM ia_common:$EII_VERSION as common

FROM base as builder
LABEL description="TimeSeriesProfiler image"


ARG ARTIFACTS
RUN mkdir $ARTIFACTS
WORKDIR /app

ARG CMAKE_INSTALL_PREFIX

# Install libzmq
RUN rm -rf deps && \
    mkdir -p deps && \
    cd deps && \
    wget -q --show-progress https://github.com/zeromq/libzmq/releases/download/v4.3.4/zeromq-4.3.4.tar.gz -O zeromq.tar.gz && \
    tar xf zeromq.tar.gz && \
    cd zeromq-4.3.4 && \
    ./configure --prefix=${CMAKE_INSTALL_PREFIX} && \
    make install

# Install cjson
RUN rm -rf deps && \
    mkdir -p deps && \
    cd deps && \
    wget -q --show-progress https://github.com/DaveGamble/cJSON/archive/v1.7.12.tar.gz -O cjson.tar.gz && \
    tar xf cjson.tar.gz && \
    cd cJSON-1.7.12 && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_INCLUDEDIR=${CMAKE_INSTALL_PREFIX}/include -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} .. && \
    make install

COPY --from=common ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=common ${CMAKE_INSTALL_PREFIX}/include ${CMAKE_INSTALL_PREFIX}/include

COPY timeseries_profiler.py .
RUN mv timeseries_profiler.py $ARTIFACTS

FROM ubuntu:$UBUNTU_IMAGE_VERSION as runtime

# Setting python dev env
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-distutils python3-minimal && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app


ARG EII_UID
ARG EII_USER_NAME
RUN groupadd $EII_USER_NAME -g $EII_UID && \
    useradd -r -u $EII_UID -g $EII_USER_NAME $EII_USER_NAME

ARG ARTIFACTS
ARG CMAKE_INSTALL_PREFIX
ENV PYTHONPATH $PYTHONPATH:/app/.local/lib/python3.8/site-packages:/app
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/include ${CMAKE_INSTALL_PREFIX}/include
COPY --from=common /eii/common/util/*.py util/
COPY --from=common /root/.local/lib .local/lib
COPY --from=builder $ARTIFACTS .
RUN mkdir /app/out/ && \
    chown ${EII_UID} /app/out/
RUN chown -R ${EII_UID} .local/lib/python3.8

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:${CMAKE_INSTALL_PREFIX}/lib
ENV PATH $PATH:/app/.local/bin
USER $EII_USER_NAME

HEALTHCHECK NONE
ENTRYPOINT ["python3", "timeseries_profiler.py"]
