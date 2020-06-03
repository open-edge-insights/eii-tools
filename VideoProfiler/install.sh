#!/bin/bash

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

EISMessageBus="$PWD/../../common/libs/EISMessageBus"
ConfigManager="$PWD/../../common/libs/ConfigManager/python"

# Installing cmake 3.15
wget -O- https://cmake.org/files/v3.15/cmake-3.15.0-Linux-x86_64.tar.gz | \
    tar --strip-components=1 -xz -C /usr/local

apt-get install -y python3-distutils

export PY_ETCD3_VERSION=cdc4c48bde88a795230a02aa574df84ed9ccfa52 && \
    git clone https://github.com/kragniz/python-etcd3 && \
    cd python-etcd3 && \
    git checkout $PY_ETCD3_VERSION && \
    python3.6 setup.py install && \
    cd .. && \
    rm -rf python-etcd3

# Install EISMessageBus
cd $EISMessageBus &&
   ./install.sh --cython

cd $EISMessageBus/../IntelSafeString/ &&
   rm -rf build && \
   mkdir build && \
   cd build && \
   cmake .. && \
   make install

cd $EISMessageBus/../EISMsgEnv/ &&
   rm -rf build && \
   mkdir build && \
   cd build && \
   cmake .. && \
   make install

cd $EISMessageBus/../../util/c/ &&
   ./install.sh && \
   rm -rf build && \
   mkdir build && \
   cd build && \
   cmake .. && \
   make install

cd $EISMessageBus &&
   rm -rf build deps && \
   mkdir build && \
   cd build && \
   cmake -DWITH_PYTHON=ON .. && \
   make && \
   make install

cd $ConfigManager &&
   rm -rf build && \
   cmake -DWITH_PYTHON=ON -DWITH_GO_ENV_CONFIG=ON -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} .. && \
   make install
