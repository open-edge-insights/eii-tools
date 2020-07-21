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


if [ "$#" -eq 2 ]; then
    ARGS=$@
    if [[ "$ARGS" =~ "detached_mode" ]]; then
        while [ $# -ne 0 ] ; do
            case "$1" in
                --detached_mode)
                    detached_mode=$2 ; shift 2;;
            esac
        done
    fi
fi

if [ $# -eq 0 ]; then
    if [ ! -z "$detached_mode" ];then
        ./common.sh --detached_mode true --csv demo_datafile.csv --sampling_rate 10 --subsample 1
    else
        ./common.sh --csv demo_datafile.csv --sampling_rate 10 --subsample 1
    fi
else
    ./common.sh $@
fi



