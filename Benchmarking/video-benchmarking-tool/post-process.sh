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

cd $results_dir

#ingestion CPU % per streams
no="1"
includeanalytics="False"


echo "ia_video_ingestion1 CPU %:"
testit=`grep "ia_video_ingestion${no} " *.stats | awk '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
if [ -z "$testit" ]
then
     no=""
     testit=`grep "ia_video_ingestion${no} " *.stats | awk '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
fi
echo $testit
for i in `seq 2 $num_streams`;
do
	echo "ia_video_ingestion$i CPU %:"
	grep ia_video_ingestion$i *.stats | awk '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
done

#Analytics CPU % per stream
testit=`grep "ia_video_analytics${no} " *.stats | awk '{ sum+= $3 } END {if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
if [ -z $testit ]
then
    includeanalytics="False"
fi
if [ "${includeanalytics}" = "True" ]; then
	echo "ia_video_analytics CPU %:"
	grep "ia_video_analytics${no} " *.stats | awk '{ sum+= $3 } END {if (NR > 0) printf ("%0.3f\n", sum / NR)}'
	for i in `seq 2 $num_streams`;
	do
		echo "ia_video_analytics$i CPU%:"
		grep ia_video_analytics$i *.stats | awk '{ sum += $3} END { if (NR > 0) printf ("%0.3f\n", sum / NR)}' 
	done
fi

#Memory BW for whole system
echo "Memory Read, Write, IO (GB/s):"
grep ^MEM -A2 *.pcm | grep SKT | awk '{print $3}' | awk '{sum += $1 } END { if (NR > 0) printf ("%0.3f, ", sum / NR)}'
grep ^MEM -A2 *.pcm | grep SKT | awk '{print $4}' | awk '{sum += $1 } END { if (NR > 0) printf ("%0.3f, ", sum / NR)}'
grep ^MEM -A2 *.pcm | grep SKT | awk '{print $5}' | awk '{sum += $1 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'

#Ingestion Memory % per stream
echo "ia_video_ingestion1 Mem %:"
grep "ia_video_ingestion${no} " *.stats | awk '{ sum += $7 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
for i in `seq 2 $num_streams`;
do
	echo "ia_video_ingestion$i Mem %:"
	grep ia_video_ingestion$i *.stats | awk '{ sum += $7 } END {if (NR > 0) printf ("%0.3f\n", sum / NR)}'
done

#Analytics Memory % per stream
if [ "${includeanalytics}" = "True" ]; then
	echo "ia_video_analytics Mem %:"
	grep "ia_video_analytics${no} " *.stats | awk '{ sum +=$7 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
	for i in `seq 2 $num_streams`;
	do
		echo "ia_video_analytics$i Mem %:"
		grep ia_video_analytics$i *.stats | awk '{ sum += $7 } END { if (NR > 0) printf ( "%0.3f\n", sum / NR)}'
	done
fi

#Ingestion Memory Usage per stream
echo "ia_video_ingestion1 Mem Usage (MiB):"
grep "ia_video_ingestion${no} " *.stats | awk '{ sum += substr($4, 1, length($4)-3) } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
for i in `seq 2 $num_streams`;
do
	echo "ia_video_ingestion$i Mem Usage (MiB):"
	grep ia_video_ingestion$i *.stats | awk '{ sum += substr($4, 1, length($4)-3) } END {if (NR > 0) printf ("%0.3f\n", sum / NR)}'
done

#Analytics Memory Usage per stream
if [ "${includeanalytics}" = "True" ]; then
	echo "ia_video_analytics Mem Usage (MiB):"
	grep "ia_video_analytics${no} " *.stats | awk '{ sum +=substr($4, 1, length($4)-3) } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
	for i in `seq 2 $num_streams`;
	do
		echo "ia_video_analytics$i Mem Usage (MiB):"
		grep ia_video_analytics$i *.stats | awk '{ sum += substr($4, 1, length($4)-3) } END { if (NR > 0) printf ( "%0.3f\n", sum / NR)}'
	done
fi


echo "Top CPU Results (CPU%):"
grep "top -" *.top -A 16 | grep -v top | grep -v Tasks | grep -v "%Cpu(s)" | grep -v KiB | grep -v PID | awk '{ printf "%s"",",$9 }' | sed -e 's/,,,/\n/g' | awk '{ for(i=1; i<=NF; i++) j+=$i; print j; j=0 }' | awk '{ sum +=$1 } END { if (NR > 0) print sum / NR}'
echo "Top Average Percent Memory usage:"
avg=`grep 'KiB Mem' *.top | awk '{ sum += $8 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
total=`grep 'KiB Mem' *.top | awk '{ sum += $4 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
echo "scale=4; $avg / $total" | bc
echo "Top Memory utilization (KiB):"
echo "$avg"
