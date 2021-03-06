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
	echo "  $0 TEST_DIR STREAMS SLEEP PCM_HOME [EII_HOME]" 1>&2
	echo "" 1>&2
	echo "WHERE:" 1>&2
	echo "  TEST_DIR  - Directory containing services.yml for the services to be tested, and the config.json and docker-compose.yml for VI and VA if applicable." 1>&2
	echo "  STREAMS   - The number of streams (1, 2, 4, 8, 16)" 1>&2
	echo "  SLEEP     - The number of seconds to wait after the containers come up " 1>&2
	echo "	PCM_HOME  - The absolute path to the PCM repository where pcm.x is built" 1>&2
	echo "	[EII_HOME] - [Optional] Absolut path to EII home directory, if running from a non-default location" 1>&2
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
EII_HOME="../../.."

if [ $# -eq 5 ]
then
    EII_HOME=$5
fi


# --------------------------------------------------------------
# configure directories/files
# Each test has a unique directory. If that directory exists,
# the test is skipped. Override that behavior by supplying
# 'yes' or 'force' as the last (6th) argument to the script, and
# the test will be run again. Even if the test is run again.
# the original data is not deleted. a new folder based on the
# date is created and symbolic link 'latest' in that folder
# will point to the most recent such capture
# --------------------------------------------------------------
DATETIME=`date -u +"%Y%b%d_%H%M"`
DATA_DIR="${TEST_DIR}/output"
ACTUAL_DATA_DIR="${DATA_DIR}/${DATETIME}"
LOG_FILE="${ACTUAL_DATA_DIR}/execute.log"
CFG_DIR=${TEST_DIR}


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
	"$@" 2>&1 | tee -a ${LOG_FILE}
}

function stop_all() {
	echo "Stopping docker containers"
	docker container stop $(docker container ls -aq)
	pkill stats.sh &
	pkill pcm &
	pkill aggregate.sh
	pkill postprocess.sh
	tokill=`ps aux | grep top | grep -v grep | head -n 1 | awk '{print $2}'`
	kill "${tokill}"

}

	# Kill all subprocesses and exit when ctrl-c is pressed
trap "echo; echo Killing processes...; stop_all; exit 0" SIGINT SIGTERM

# --------------------------------------------------------------
# Create data directories
# --------------------------------------------------------------
mkdir -p "${DATA_DIR}"
mkdir -p "${ACTUAL_DATA_DIR}"
touch "${LOG_FILE}"

# --------------------------------------------------------------
# Ensure the Model-specific-register kernel module is installed
# (required by PCM monitoring tool)
# --------------------------------------------------------------
notice "Installing MSR kernelmodule"
run_logged modprobe msr

# --------------------------------------------------------------
# If necessary, start HDDL daemon
#
# --------------------------------------------------------------
export HDDL="cpu"
if [ "${HDDL}" == *"HDDL"* ]; then
	myprocess=`ps aux | grep hddldaemon | grep -v grep`
	if [ -z "${myprocess}" ]; then
		notice "Starting HDDL daemon"
		run_logged source /opt/intel/openvino/bin/setupvars.sh
		run_logged $HDDL_INSTALL_DIR/bin/hddldaemon &
		run_logged sleep 120
	fi
fi

# --------------------------------------------------------------
# Kill any previously provisioned containers
# --------------------------------------------------------------
notice "Stop any old containers"
pushd "${EII_HOME}/build/"
run_logged docker-compose down
popd

# --------------------------------------------------------------
# Remove files from last test and copy over files for this test
# --------------------------------------------------------------
notice "Cleaning files from prior tests"
run_logged rm -v "${EII_HOME}/build/docker-compose.yml"
run_logged rm -v "${EII_HOME}/build/eii_config.json"
run_logged rm -rf -v "${EII_HOME}/build/multi_instance"
run_logged mkdir -p ${EII_HOME}/VideoIngestion/benchmarking

notice "Generating test configuration files"
run_logged cp -v ${TEST_DIR}/services.yml ${EII_HOME}/build/services.yml
run_logged cp -rv ${EII_HOME}/VideoIngestion/docker-compose.yml ${EII_HOME}/VideoIngestion/benchmarking/
run_logged cp -rv ${TEST_DIR}/config.json ${EII_HOME}/VideoIngestion/benchmarking/

# --------------------------------------------------------------
# Configure the VideoProfiler
# --------------------------------------------------------------
notice "Configuring the VideoProfiler"
run_logged cp -rvf ${TEST_DIR}/VP_config.json ${EII_HOME}/tools/VideoProfiler/config.json

pushd "${EII_HOME}/build"
run_logged python3 builder.py -f services.yml -d benchmarking -v $STREAMS
popd

# --------------------------------------------------------------
# Launch
# --------------------------------------------------------------
notice "Starting containers"
pushd "${EII_HOME}/build"
run_logged docker-compose -f docker-compose-build.yml build
# TODO: Once the configmgr initialization timing issue is fixed
# remove the sleep and start all services
run_logged docker-compose up -d ia_configmgr_agent
run_logged sleep 10s
run_logged docker-compose up -d
#${PCM_HOME}/pcm.x 2>&1 | tee -a "${ACTUAL_DATA_DIR}/output.pcm" &
run_logged sleep $SLEEP
popd

# --------------------------------------------------------------
# Start statistics gathering tasks in the background
# --------------------------------------------------------------
notice "Starting statistics collection"
${EII_HOME}/tools/Benchmarking/video-benchmarking-tool/stats.sh "${ACTUAL_DATA_DIR}/output.stats" &
${PCM_HOME}/pcm.x  | tee -a "${ACTUAL_DATA_DIR}/output.pcm" &
top -b -i -o %CPU  | tee -a "${ACTUAL_DATA_DIR}/stat.top" &


# --------------------------------------------------------------
# kill all tasks and wait for processes to finish
# --------------------------------------------------------------
notice "Stopping statistics collection"
pkill stats.sh &
pkill pcm &
tokill=`ps aux | grep top | grep -v grep | head -n 1 | awk '{print $2}'`
kill "${tokill}"
run_logged wait


notice "Test Complete"
pushd "${EII_HOME}/build/"
while [[ $(docker ps -a | grep ia_video_profiler | grep Exited | wc -l) -ne 1 ]]; do
        echo "video profiler is running..sleep for 10s"
        sleep 10
done

# Storing video profiler log into file
docker logs ia_video_profiler >& ${ACTUAL_DATA_DIR}/profiler_output.log
run_logged docker-compose down
popd
run_logged mv /opt/intel/eii/tools_output/FPS_Results.csv ${ACTUAL_DATA_DIR}/FPS_Results.csv
# --------------------------------------------------------------
# Post-process results
# --------------------------------------------------------------
notice "Post-Processing Results"
#TODO vp output
run_logged "${EII_HOME}/tools/Benchmarking/video-benchmarking-tool/post-process.sh" "${ACTUAL_DATA_DIR}" "${STREAMS}" > "${ACTUAL_DATA_DIR}/results.ppc"
run_logged "${EII_HOME}/tools/Benchmarking/video-benchmarking-tool/aggregateresults.sh" "${ACTUAL_DATA_DIR}" "${STREAMS}" "${DATETIME}" "${ACTUAL_DATA_DIR}/output.csv" "${TEST_DIR}"
sed -e "s/\r//g" ${ACTUAL_DATA_DIR}/output.csv > ${ACTUAL_DATA_DIR}/final_output.csv

# --------------------------------------------------------------
# Post-process complete
# --------------------------------------------------------------
notice "Post-processing complete."
exit ${SUCCESS}

