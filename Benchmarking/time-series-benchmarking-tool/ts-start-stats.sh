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

# --------------------------------------------------------------
# Get command line arguments
# --------------------------------------------------------------
ACTUAL_DATA_DIR=$1
SLEEP=$2
PCM_HOME=$3
EIS_HOME="../../.."

function notice(){
	echo "# --------------------------------------------------------------" 2>&1 | tee -a ${LOG_FILE}
	echo "# `date -u` | $@" 2>&1 | tee -a ${LOG_FILE}
	echo "# --------------------------------------------------------------" 2>&1 | tee -a ${LOG_FILE}
}

function run_logged(){
	echo "# `date -u` | CMD: '$@'" 2>&1 | tee -a ${LOG_FILE}
	"$@" 2>&1 | tee -a ${LOG_FILE}
}

# --------------------------------------------------------------
# Start statistics gathering tasks in the background
# --------------------------------------------------------------
notice "Starting statistics collection"
run_logged ./stats.sh "${ACTUAL_DATA_DIR}/output.stats" &
run_logged ${PCM_DIR}/pcm.x > "${ACTUAL_DATA_DIR}/output.pcm" &
top -b -i -o %CPU > ${ACTUAL_DATA_DIR}/stat.top &


sleep $SLEEP

pkill pcm &
pkill stats.sh &
tokill=`ps aux | grep top | grep -v grep | head -n 1 | awk '{print $2}'`
kill "${tokill}"

