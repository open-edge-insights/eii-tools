#!/bin/bash -e

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

export PYTHONPATH=$PYTHONPATH:../../:../../common/libs/EIIMessageBus:../../common
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

# Env variables to be set for communicating with ETCD
export AppName="VideoProfiler"

# Comment out below 4 lines if running in DEV mode
export DEV_MODE=FALSE
export CONFIGMGR_CERT=../../build/provision/Certificates/VideoProfiler/VideoProfiler_client_certificate.pem
export CONFIGMGR_KEY=../../build/provision/Certificates/VideoProfiler/VideoProfiler_client_key.pem
export CONFIGMGR_CACERT=../../build/provision/Certificates/ca/ca_certificate.pem

# Uncomment below 4 lines if running in DEV mode
# export DEV_MODE=TRUE
# export CONFIGMGR_CERT=""
# export CONFIGMGR_KEY=""
# export CONFIGMGR_CACERT=""

# For running VideoProfiler on a separate node or with CSL, set these variables to
# point to the etcd on different node
export ETCD_HOST=
export ETCD_CLIENT_PORT=2379
# ETCD prefix for the key
export ETCD_PREFIX=
export no_proxy=localhost,127.0.0.1,$ETCD_HOST
