# Copyright (c) 2021 Intel Corporation.

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

# Dockerfile for VideoProfiler

ARG EII_VERSION
ARG DOCKER_REGISTRY
ARG ARTIFACTS="/artifacts"
ARG EII_UID
ARG EII_USER_NAME
ARG UBUNTU_IMAGE_VERSION
FROM ${DOCKER_REGISTRY}ia_eiibase:$EII_VERSION as base
FROM ${DOCKER_REGISTRY}ia_common:$EII_VERSION as common

FROM base as builder
LABEL description="VideoProfiler image"


ARG ARTIFACTS
RUN mkdir $ARTIFACTS
WORKDIR /app

COPY requirements.txt .
RUN pip3 install --user -r requirements.txt

COPY video_profiler.py .
RUN mv video_profiler.py $ARTIFACTS

FROM ubuntu:$UBUNTU_IMAGE_VERSION as runtime

# Setting python dev env
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3.6 \
                                               python3-distutils  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app


ARG EII_UID
ARG EII_USER_NAME
RUN adduser --quiet --disabled-password ${EII_USER_NAME}

ARG ARTIFACTS
ARG CMAKE_INSTALL_PREFIX
ENV PYTHONPATH $PYTHONPATH:/app/.local/lib/python3.6/site-packages:/app
COPY --from=common ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=common /eii/common/util/*.py util/
COPY --from=common /root/.local/lib .local/lib
COPY --from=builder $ARTIFACTS .
COPY --from=builder /root/.local/lib .local/lib
RUN mkdir /app/out/
RUN chown -R ${EII_UID} .local/lib/python3.6

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:${CMAKE_INSTALL_PREFIX}/lib
ENV PATH $PATH:/app/.local/bin

HEALTHCHECK NONE
ENTRYPOINT ["python3.6", "video_profiler.py"]
