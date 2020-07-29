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


function helpFunction {
    echo >&2
    echo "Usage: ./publish.sh --name container_name --temperature temperature_range_lower:temperature_range_upper --pressure pressure_range_lower:pressure_range_upper --humidity humidity_range_lower:humidity_range_upper --topic_temp temperature_topic --topic_pres pressure_topic --topic_humd humidity_topic --interval publication_interval" >&2
    echo >&2
    echo "OR" >&2
    echo >&2
    echo "Usage: ./publisher_csv.sh --name container_name --csv csv_file --sampling_rate sampling_rate --subsample subsample --topic topic" >&2
    echo >&2
    echo "SUMMARY": >&2
    echo >&2
    echo "  --name  publisher container name" >&2
    echo >&2
    echo "  --temperature  Random data generation range for temperature" >&2
    echo >&2
    echo "  --pressure  Random data generation range for temperature" >&2
    echo >&2
    echo "  --humidity  Random data generation range for humidity" >&2
    echo >&2
    echo "  --topic_temp  Topic for temperature data" >&2
    echo >&2
    echo "  --topic_pres  Topic for pressure data" >&2
    echo >&2
    echo "  --topic_humd  Topic for humidity data" >&2
    echo >&2
    echo "  --csv  CSV file to publish to MQTT broker" >&2
    echo >&2
    echo "  --sampling_rate  Data Sampling Rate" >&2
    echo >&2
    echo "  --subsample  subsample" >&2
    echo >&2
    echo "  --topic  Topic for csv file pulish" >&2
    echo >&2
    echo "  --interval  MQTT publication interval" >&2
    echo >&2
    exit 1
}


function publisher_csv {
    echo "*****Running publisher container*****"
    name="publisher"
    while [ $# -ne 0 ] ; do
        case "$1" in
            --detached_mode)
                detached_mode=$2 ; shift 2;;
            --name)
                name=$2 ; shift 2 ;;
            *)
                if [ ! -z "$args" ];then
                    args+=" "
                fi
                args+="$1 $2"
                shift 2 ;;
        esac
    done

    if [ ! -z "$detached_mode" ];then
        docker run --rm -itd --net host --name $name publisher $args
    else
        docker run --rm -it --net host --name $name publisher $args
    fi
}

function publisher {
    echo "*****Running publisher container*****"
    name="publisher"
    while [ $# -ne 0 ] ; do
        case "$1" in
            --detached_mode)
                detached_mode=$2 ; shift 2;;
            --name)
                name=$2 ; shift 2 ;;
            *)
                if [ ! -z "$args" ];then
                    args+=" "
                fi
                args+="$1 $2"
                shift 2 ;;
        esac
    done

    if [ ! -z "$detached_mode" ];then
        docker run --rm -itd --net host --name $name publisher $args
    else
        docker run --rm -it --net host --name $name publisher $args
    fi
}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	helpFunction
fi
echo $@
ARGS=$@
if [[ "$ARGS" =~ "csv" ]]; then
	publisher_csv $@
else
	publisher $@
fi