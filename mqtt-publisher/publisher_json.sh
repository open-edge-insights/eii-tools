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

# Preparing the command line argument to pass to common.sh
# when only "--deatched_mode true" is passed to this script, and
# delete the --detached_mode args with shift.
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

# Once the args become zero in the above step, (in case of --detached_mode true only)
# checking if detached mode args is present, if it is there calling the
# common.sh with detached mode or else calling without detached mode
if [ $# -eq 0 ]; then
	if [ ! -z "$detached_mode" ];then
		./publisher.sh --detached_mode true --topic test/rfc_data --json "./json_files/\*.json"
	else
		./publisher.sh --topic test/rfc_data --json "./json_files/\*.json"
        fi
fi
