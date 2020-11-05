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

results_dir=$1
streams=$2
datetime=$3
outputfile=$4

cd $results_dir

infodata="System,Date,Instances,Measured Throughput at Loadgen(MB/s)"

CPUdata="mosquitto CPU (%),ia_telegraf CPU (%),ia_influx CPU (%)"

MemData="Memory Read (GB/s),Memory Write (GB/s),Memory IO (GB/s),mosquitto Mem (%),ia_telegraf Mem (%),ia_influxdb Mem (%)"

MemData2="mosquitto Mem Usage (MiB),ia_telegraf Mem Usage (MiB),ia_influxdb Mem Usage (MiB)"

TopAndMpstat="Top Total % CPU Utilization top 10 processes, Top Percent Memory Usage, Top Memory Utilization"

Points="Points Received"

if [ ! -f $outputfile ]; then echo $infodata,$CPUdata,$MemData,$MemData2,$TopAndMpstat,$Points > $outputfile; fi

cd $results_dir
infodata="$HOSTNAME,$datetime,$streams,"
CPUdata=`grep "mosquitto CPU" -A1 results.ppc | grep -v "mosquitto "`
cpu=`grep "ia_telegraf CPU" -A1 results.ppc | grep -v "ia_telegraf"`
CPUdata="${CPUdata},${cpu}"
cpu=`grep "ia_influxdb CPU" -A1 results.ppc | grep -v "influxdb"`
if [[ $cpu =~ [0-9] ]]; then
	CPUdata="${CPUdata},${cpu}"
else
	CPUdata="${CPUdata},"
fi

MemData=`grep "Memory Read, Write, IO" -A1 results.ppc | grep -v "Memory Read, Write"`
mem=`grep "mosquitto Mem %" -A1 results.ppc | grep -v "mosquitto "`
MemData="${MemData},${mem}"
mem=`grep "ia_telegraf Mem %" -A1 results.ppc | grep -v "ia_telegraf"`
MemData="${MemData},${mem}"
mem=`grep "ia_influxdb Mem %" -A1 results.ppc | grep -v "influxdb"`
if [[ $mem =~ [0-9] ]]; then
	MemData="${MemData},${mem}"
else
	MemData="${MemData},"
fi



MemData2=`grep "mosquitto Mem Usage" -A1 results.ppc | grep -v "mosquitto "`
mem=`grep "ia_telegraf Mem Usage" -A1 results.ppc | grep -v "ia_telegraf"`
MemData2="${MemData2},${mem}"
mem=`grep "ia_influxdb Mem Usage" -A1 results.ppc | grep -v "influxdb"`
MemData2="${MemData2},${mem}" 
if [[ $mem =~ [0-9] ]]; then
	MemData2="${MemData2},${mem}"
else
	MemData2="${MemData2},"
fi

TopAndMpstat=`grep "Top CPU Results (CPU%)" -A1 results.ppc | grep -v "Top CPU Results (CPU%)"`
next=`grep "Top Average Percent Memory usage" -A1 results.ppc | grep -v "Top Average Percent Memory usage"`
TopAndMpstat="${TopAndMpstat},${next}"
next=`grep "Top Memory utilization (KiB)" -A1 results.ppc | grep -v "Top Memory utilization (KiB)"`
TopAndMpstat="${TopAndMpstat},${next}"


Points=`grep Points -A2 execute.log | tail -n 1`
#Points=`grep "Points:" -Al execute.log | grep -v "Points:"`
echo $infodata,$CPUdata,$MemData,$MemData2,$FPSDATA,$TopAndMpstat,$Points >> $outputfile
