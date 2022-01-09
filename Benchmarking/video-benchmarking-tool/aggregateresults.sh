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

results_dir=$1
num_streams=$2
datetime=$3
outputfile=$4
testname=$5

cd $results_dir

infodata="System,Date,Test,Streams"

CPUdata="ia_video_ingestion1 CPU (%)"
for i in `seq 2 $num_streams`;
do
	CPUdata="$CPUdata,ia_video_ingestion$i CPU (%)"
done

MemData="Memory Read (GB/s),Memory Write (GB/s),Memory IO (GB/s),ia_video_ingestion1 Mem (%)"
for i in `seq 2 $num_streams`;
do
	MemData="$MemData, ia_video_ingestion$i Mem (%)"
done

MemData2="ia_video_ingestion1 Mem Usage (MiB)"
for i in `seq 2 $num_streams`;
do
	MemData2="$MemData2,ia_video_ingestion$i Mem Usage (MiB)"
done

FPSdata="Total FPS, FPS Camera 1"
for i in `seq 2 $num_streams`;
do
	FPSdata="$FPSdata,FPS Camera $i"
done

TopData="Top Total % CPU Utilization top 10 processes, Top Percent Memory Usage, Top Memory Utilization"


if [ ! -f $outputfile ]; then echo $infodata,$CPUdata,$MemData,$MemData2,$FPSdata,$TopData > $outputfile; fi
FPSdata=""
infodata="$HOSTNAME,$datetime,$testname,$num_streams"
CPUdata=`grep "ia_video_ingestion1 CPU" -A1 results.ppc | grep -v "ia_video_ingestion"`
echo "$CPUdata"
for i in `seq 2 $num_streams`;
do
	cpu=`grep "ia_video_ingestion$i CPU" -A1 results.ppc | grep -v ia_video_ingestion`
	CPUdata="${CPUdata},${cpu}"
done
#for i in `seq $((num_streams+1)) 32`; do CPUdata="${CPUdata},"; done


if [ "${includeanalytics}" = "True" ]; then
	cpu=`grep "ia_video_analytics CPU" -A1 results.ppc | grep -v "ia_video_analytics "`
	CPUdata="${CPUdata},${cpu}"
	for i in `seq 2 $num_streams`;
	do
		cpu=`grep "ia_video_analytics$i CPU" -A1 results.ppc | grep -v ia_video_analytics`
		CPUdata="${CPUdata},${cpu}"
	done
	for i in `seq $((num_streams+1)) 32`; do CPUdata="${CPUdata},"; done
#else
#	for i in `seq 2 $num_streams`; do CPUdata="${CPUdata},"; done
fi
echo "$CPUdata"

PCMData=`grep "Memory Read, Write, IO" -A1 results.ppc | grep -v "Memory Read, Write"`
MemData=`grep "ia_video_ingestion1 Mem %" -A1 results.ppc | grep -v "ia_video_ingestion"`
for i in `seq 2 $num_streams`;
do
	mem=`grep "ia_video_ingestion$i Mem %" -A1 results.ppc | grep -v ia_video_ingestion`
	MemData="${MemData},${mem}"
done
#for i in `seq $((num_streams+1)) 32`; do MemData="${MemData},"; done

if [ "${includeanalytics}" = "True" ]; then
	mem=`grep "ia_video_analytics Mem %" -A1 results.ppc | grep -v "ia_video_analytics "`
	MemData="${MemData},${mem}"
	for i in `seq 2 $num_streams`;
	do
		mem=`grep "ia_video_analytics$i Mem %" -A1 results.ppc | grep -v ia_video_analytics`
		MemData="${MemData},${mem}"
	done
	for i in `seq $((num_streams+1)) 32`; do MemData="${MemData},"; done
#else 
#	for i in `seq 2 $num_streams`; do MemData="${MemData},"; done
fi
echo "$PCMData"
echo "$MemData"

MemData2=`grep "ia_video_ingestion1 Mem Usage" -A1 results.ppc | grep -v "ia_video_ingestion"`
for i in `seq 2 $num_streams`;
do
	mem=`grep "ia_video_ingestion$i Mem Usage" -A1 results.ppc | grep -v ia_video_ingestion`
	MemData2="${MemData2},${mem}"
done
#for i in `seq $((num_streams+1)) 32`; do MemData2="${MemData2},"; done

if [ "${includeanalytics}" = "True" ]; then
	mem=`grep "ia_video_analytics Mem Usage" -A1 results.ppc | grep -v "ia_video_analytics "`
	MemData2="${MemData2},${mem}"
	for i in `seq 2 $num_streams`;
	do
		mem=`grep "ia_video_analytics$i Mem Usage" -A1 results.ppc | grep -v ia_video_analytics`
		MemData2="${MemData2},${mem}"
	done
	for i in `seq $((num_streams+1)) 32`; do MemData2="${MemData2},"; done
#else
#	for i in `seq 1 $num_streams`; do MemData2="${MemData2},"; done
fi
FPSdata=`grep camera1_stream FPS_Results.csv | awk -F',' '{print $2}'`
grep "camera1_stream" FPS_Results.csv | awk -F',' '{print $2}'
for i in `seq 2 $num_streams`
do
    grep "camera${i}_stream" FPS_Results.csv | awk -F',' '{print $2}'
    temp=`grep "camera${i}_stream" FPS_Results.csv | awk -F',' '{print $2}'`
    FPSdata="$FPSdata,$temp"
done
echo "$FPSdata"

TOTALfps=`grep Total FPS_Results.csv | awk -F',' '{print $2}'`
TopData=`grep "Top CPU Results (CPU%)" -A1 results.ppc | grep -v "Top CPU Results (CPU%)"`
next=`grep "Top Average Percent Memory usage" -A1 results.ppc | grep -v "Top Average Percent Memory usage"`
TopData="${TopData},${next}"
next=`grep "Top Memory utilization (KiB)" -A1 results.ppc | grep -v "Top Memory utilization (KiB)"`
TopData="${TopData},${next}"

# If PCMData is set to junk value, set Memory Read, Write, IO values to NA
if [[ "$PCMData" == *"ia"* ]];
then
   PCMData='NA,NA,NA'
fi

echo $infodata,$CPUdata,$PCMData,$MemData,$MemData2,$TOTALfps,$FPSdata,$TopData >> $outputfile
