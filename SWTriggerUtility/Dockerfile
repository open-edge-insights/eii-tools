# Copyright (c) 2020 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Dockerfile for cpp_publisher
ARG EII_VERSION
ARG DOCKER_REGISTRY
ARG UBUNTU_IMAGE_VERSION
ARG CMAKE_BUILD_TYPE
ARG RUN_TESTS
ARG ARTIFACTS="/artifacts"
FROM ia_common:$EII_VERSION as common
FROM ia_eiibase:${EII_VERSION} as builder
LABEL description="SWTriggerUtility image"

WORKDIR /app

ARG ARTIFACTS
RUN mkdir $ARTIFACTS

ARG CMAKE_INSTALL_PREFIX
ENV CMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}

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

COPY --from=common ${CMAKE_INSTALL_PREFIX}/include ${CMAKE_INSTALL_PREFIX}/include
COPY --from=common ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=common /eii/common/cmake ./common/cmake
COPY --from=common /eii/common/libs ./common/libs

ENV LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${CMAKE_INSTALL_PREFIX}/lib

COPY . SWTriggerUtility/

RUN cd SWTriggerUtility/ && \
    rm -rf build/ && \
    mkdir build/ && \
    cd build/ && \
    cmake -DCMAKE_INSTALL_INCLUDEDIR=${CMAKE_INSTALL_PREFIX}/include -DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} .. && \
    make
RUN cp SWTriggerUtility/build/sw_trigger_utility $ARTIFACTS/

FROM ubuntu:$UBUNTU_IMAGE_VERSION as runtime

ARG EII_UID
ARG EII_USER_NAME
RUN groupadd $EII_USER_NAME -g $EII_UID && \
    useradd -r -u $EII_UID -g $EII_USER_NAME -m $EII_USER_NAME
RUN rm -rf /var/lib/apt/lists/*

ARG ARTIFACTS
WORKDIR /app
ARG CMAKE_INSTALL_PREFIX
ENV CMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/include ${CMAKE_INSTALL_PREFIX}/include
COPY --from=builder $ARTIFACTS .

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:${CMAKE_INSTALL_PREFIX}/lib
USER $EII_USER_NAME

HEALTHCHECK NONE

ENTRYPOINT ["sleep","infinity"]
