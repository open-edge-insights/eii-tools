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


#######################################
RED='\033[0;31m'
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
NC='\033[0m' # No Color
#######################################
function echo_yellow() {
    echo -e "${YELLOW}$1 ${NC}"
}
#######################################
function echo_green() {
    echo -e "${GREEN}$1 ${NC}"
}
#######################################
function echo_red() {
    echo -e "${RED}$1${NC}"
}
#######################################
function echo_error() {
    echo -e "${RED}$1${NC}" >&2
    exit 1
}
#######################################

function usage(){
    echo "Error: missing one or more parameters." 1>&2
    echo "USAGE:" 1>&2
    echo "  $0 <number-of-streams> <starting-port-number> <bitrate> <width> <height> <framerate>" 1>&2
    echo "" 1>&2
    echo "WHERE:" 1>&2
    echo "  number-of-streams     - The number of streams to host" 1>&2
    echo "  starting-port-number  - The port number to start the first stream on. The rest of the streams will increment on this port number" 1>&2
    echo "  bitrate               - Encoding bitrate to use" 1>&2
    echo "  width                 - The width value of the resolution for each stream" 1>&2
    echo "  height                - The height value of the resolution for each stream" 1>&2
    echo "  framerate                - The framerate for each stream" 1>&2
    echo 1>&2
    echo "Aborting..." 1>&2
    exit ${FAILURE}

}
if [ -z "$1" ]; then usage; fi
if [ -z "$2" ]; then usage; fi
if [ -z "$3" ]; then usage; fi
if [ -z "$4" ]; then usage; fi
if [ -z "$5" ]; then usage; fi
if [ -z "$6" ]; then usage; fi

STREAMS=$1
RTSP_PORT=$2
BIT_RATE=$3
WIDTH=$4
HEIGHT=$5
FRAMERATE=$6

# Sanity check the input parameter
re='^[0-9]+$'
if ! [[ $STREAMS =~ $re ]] ; then
   echo_error "error: parameter is not a positive integer"
fi


function stop_all() {
    echo_green "Stopping docker containers"
    docker stop $(for ((i=8554; i < $((8554+$STREAMS)); i++)) ; do echo rtsp_$i ; done)
}

# Kill all subprocesses and exit when ctrl-c is pressed
trap "echo; echo Killing processes...; stop_all; exit 0" SIGINT SIGTERM

# Launch all the streams
for ((i=8554; i < $((8554+$STREAMS)); i++)); do
   echo_green "Starting $i RTSP server"
   ./rtsp.sh $i $BIT_RATE $WIDTH $HEIGHT $FRAMERATE &
   sleep 1
done

echo_green "All RTSP servers started"
# Enter into infinite loop
while true; do
  sleep .25
done
