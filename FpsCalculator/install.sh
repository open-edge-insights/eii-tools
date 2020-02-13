#!/bin/bash

EISMessageBus="$PWD/../../common/libs/EISMessageBus"

# Installing cmake 3.15
wget -O- https://cmake.org/files/v3.15/cmake-3.15.0-Linux-x86_64.tar.gz | \
    tar --strip-components=1 -xz -C /usr/local

# Installing requirements
python3.6 -m pip install -r requirements.txt

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