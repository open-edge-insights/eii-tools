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

# Dockerfile for Jupyter Notebook

ARG EII_VERSION
ARG DOCKER_REGISTRY
ARG ARTIFACTS="/artifacts"
ARG UBUNTU_IMAGE_VERSION
ARG EII_UID
ARG EII_USER_NAME
FROM ${DOCKER_REGISTRY}ia_eiibase:$EII_VERSION as base
FROM ${DOCKER_REGISTRY}ia_common:$EII_VERSION as common

FROM base as builder
LABEL description="Jupyter Notebook image"

ARG ARTIFACTS
WORKDIR /app

COPY . .
RUN pip3 install --user -r requirements.txt

FROM ubuntu:$UBUNTU_IMAGE_VERSION as runtime

# Setting python dev env
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends libsm6 \
                                               libxext6 \
                                               libfontconfig1 \
                                               libxrender1 \
                                               python3.6 \
                                               python3-distutils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG EII_UID
ARG EII_USER_NAME
RUN groupadd $EII_USER_NAME -g $EII_UID && \
    useradd -r -u $EII_UID -g $EII_USER_NAME $EII_USER_NAME

ARG ARTIFACTS
ARG CMAKE_INSTALL_PREFIX
ENV PYTHONPATH $PYTHONPATH:/app/.local/lib/python3.6/site-packages:/app
COPY --from=common ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=common /root/.local/lib .local/lib
COPY --from=builder /root/.local/lib .local/lib
COPY --from=builder /root/.local/bin .local/bin
COPY --from=builder /app .

RUN chown -R ${EII_UID} .local/lib/python3.6

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:${CMAKE_INSTALL_PREFIX}/lib
ENV PATH $PATH:/app/.local/bin
USER $EII_USER_NAME

HEALTHCHECK NONE
ENTRYPOINT ["jupyter", "notebook", "--allow-root"]
