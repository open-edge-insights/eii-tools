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

# --------------------------------------------------------------
# check arguments
# --------------------------------------------------------------
function usage(){
	echo "Error: missing one or more parameters." 1>&2
	echo "USAGE:" 1>&2
	echo "  $0 TEST_DIR STREAMS SLEEP PCM_HOME [EIS_HOME]" 1>&2
	echo "" 1>&2
	echo "WHERE:" 1>&2
	echo "  TEST_DIR  - Directory containing services.yml and config files for influx, telegraf, and kapacitor" 1>&2
	echo "  STREAMS   - The number of streams (1, 2, 4, 8, 16)" 1>&2
	echo "  SLEEP     - The number of seconds to wait after the containers come up " 1>&2
	echo "	PCM_HOME  - The absolute path to the PCM repository where pcm.x is built" 1>&2
	echo "	[EIS_HOME] - [Optional] Absolut path to EIS home directory, if running from a non-default location" 1>&2
	echo 1>&2
	echo "Aborting..." 1>&2
	exit ${FAILURE}

}
if [ -z "$1" ]; then usage; fi
if [ -z "$2" ]; then usage; fi
if [ -z "$3" ]; then usage; fi
if [ -z "$4" ]; then usage; fi


# --------------------------------------------------------------
# Get command line arguments
# --------------------------------------------------------------
TEST_DIR=$1
STREAMS=$2
SLEEP=$3
PCM_HOME=$4
EIS_HOME="../../.."

if [ $# -eq 5 ]
then
    EIS_HOME=$5
fi

DATETIME=`date -u +"%Y%b%d_%H%M"`
DATA_DIR="${TEST_DIR}/output"
ACTUAL_DATA_DIR="${DATA_DIR}/${DATETIME}"
LOG_FILE="${ACTUAL_DATA_DIR}/execute.log"
CFG_DIR=${TEST_DIR}


# --------------------------------------------------------------
# Create data directories
# --------------------------------------------------------------
mkdir -p "${DATA_DIR}"
mkdir -p "${ACTUAL_DATA_DIR}"
touch "${LOG_FILE}"

# --------------------------------------------------------------
# misc functions
# --------------------------------------------------------------
function errexit (){
	local rc=$?
	echo "ERROR: $@" 1>&2
	echo "NOTE: return code was ${rc}" 1>&2
	echo "aborting..." 1>&2
	exit ${FAILURE}
}

function notice(){
	echo "# --------------------------------------------------------------" 2>&1 | tee -a ${LOG_FILE}
	echo "# `date -u` | $@" 2>&1 | tee -a ${LOG_FILE}
	echo "# --------------------------------------------------------------" 2>&1 | tee -a ${LOG_FILE}
}

function run_logged(){
	echo "# `date -u` | CMD: '$@'" 2>&1 | tee -a ${LOG_FILE}
	$@ 2>&1 | tee -a ${LOG_FILE}
}


# --------------------------------------------------------------
# Ensure the Model-specific-register kernel module is installed
# (required by PCM monitoring tool)
# --------------------------------------------------------------
notice "Installing MSR kernelmodule"
run_logged modprobe msr

# --------------------------------------------------------------
# Kill any previously provisioned containers
# --------------------------------------------------------------
notice "Stop any old containers"
pushd "${EIS_HOME}/build/"
run_logged docker-compose down
popd

# --------------------------------------------------------------
# Remove files from last test and copy over files for this test
# --------------------------------------------------------------
notice "Cleaning files from prior tests"
#run_logged rm -v "${EIS_HOME}/build/docker-compose.yml"
#run_logged rm -v "${EIS_HOME}/build/provision/config/eis_config.json"
#run_logged rm -v "${EIS_HOME}/build/config/telegraf"*".conf"
#run_logged rm -v "${EIS_HOME}/build/config/influxdb.conf"

notice "Copying in test configuration files"
#run_logged cp -v "${CFG_DIR}/docker-compose.yml" "${EIS_HOME}/build/docker-compose.yml"
#run_logged cp -v "${CFG_DIR}/eis_config.json" "${EIS_HOME}/build/provision/config/eis_config.json"
#run_logged cp -v "${CFG_DIR}/telegraf"*".conf" "${EIS_HOME}/build/config/"
#run_logged cp -v "${CFG_DIR}/influxdb.conf" "${EIS_HOME}/build/config/"


notice "Generating test configuration files"
run_logged cp -v ${TEST_DIR}/services.yml ${EIS_HOME}/build/services.yml

pushd "${EIS_HOME}/build"
run_logged python3 eis_builder.py -f services.yml
popd

# --------------------------------------------------------------
# Provision containers
# --------------------------------------------------------------
notice "Provisioning cluster"
pushd "${EIS_HOME}/build/provision/"
run_logged ./provision_eis.sh ../docker-compose.yml
popd

# --------------------------------------------------------------
# Launch
# --------------------------------------------------------------
notice "Starting containers"
pushd "${EIS_HOME}/build"
run_logged docker-compose up --build -d
run_logged sleep 10
popd


# --------------------------------------------------------------
# If this is test TS1, remove influx container
# -----------------------------s---------------------------------
#TODO
if [ "${TEST}" == "TS1" ]; then
	pushd "${EIS_HOME}/docker_setup"
	run_logged docker-compose stop ia_influxdbconnector
	run_logged docker-compose rm -f ia_influxdbconnector
fi

./ts-start-stats.sh ${ACTUAL_DATA_DIR} ${SLEEP} ${PCM_HOME} ${EIS_HOME}


# --------------------------------------------------------------
# Run Time Series Profiler
# --------------------------------------------------------------
notice "Time Series Profiler"
pushd "${EIS_HOME}/tools/TimeSeriesProfiler/"
run_logged docker-compose up 
popd

notice "Test Complete"
pushd "${EIS_HOME}/build/"
run_logged docker-compose down
popd

# --------------------------------------------------------------
# Post-process results
# --------------------------------------------------------------
notice "Post-Processing Results"
#TODO vp output
run_logged "./post-process.sh" "${ACTUAL_DATA_DIR}" "${STREAMS}" > "${ACTUAL_DATA_DIR}/results.ppc"
run_logged "./aggregateresults.sh" "${ACTUAL_DATA_DIR}" "${STREAMS}" "${DATETIME}" "${ACTUAL_DATA_DIR}/output.csv"
#sed -e "s/\r//g" ${ACTUAL_DATA_DIR}/output.csv > ${ACTUAL_DATA_DIR}/final_output.csv

# --------------------------------------------------------------
# Post-process complete
# --------------------------------------------------------------
notice "Post-processing complete."
exit ${SUCCESS}
