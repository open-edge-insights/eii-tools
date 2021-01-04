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

# env variables to communicate with ETCD
export AppName="SWTriggerUtility"
export DEV_MODE="FALSE"
export CONFIGMGR_CERT="../../../build/provision/Certificates/SWTriggerUtility/SWTriggerUtility_client_certificate.pem"
export CONFIGMGR_KEY="../../../build/provision/Certificates/SWTriggerUtility/SWTriggerUtility_client_key.pem"
export CONFIGMGR_CACERT="../../../build/provision/Certificates/ca/ca_certificate.pem"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export no_proxy=$no_proxy,127.0.0.1
# The name of the interface to be fetched
# If using with multi instance:
# If user wants to connect to VideoIngestion1, the interface_name
# would be default1 & default2 for VideoIngestion2 etc. Also, ensure
# to have the same `Name`, `EndPoint` and `Type` values in `Clients`
# interface key of `config.json` matching to those coming in `Servers`
# interface key of respective VideoIngestion service `config.json`
export interface_name="default"
