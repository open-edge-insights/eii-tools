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
instances=$2

cd $results_dir

#CPU % per container type
echo "mosquitto CPU %:"
grep "mosquitto" *.stats | awk -v inst="$instances" '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", ( sum * inst ) / NR ) }'
#echo "ia_telegraf CPU %:"
#grep "ia_telegraf" *.stats | awk -v inst="$instances" '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", ( sum * inst ) / NR ) }'
echo "ia_telegraf CPU %:"
grep "ia_telegraf" *.stats | awk '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'

echo "ia_influxdb CPU %:"
grep "ia_influxdbconnector " *.stats | awk '{ sum += $3 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'


#Memory BW
echo "Memory Read, Write, IO (GB/s):"
grep ^MEM -A2 *.pcm | grep SKT | awk '{print $3}' | awk '{sum += $1 } END { if (NR > 0) printf ("%0.3f, ", sum / NR)}'
grep ^MEM -A2 *.pcm | grep SKT | awk '{print $4}' | awk '{sum += $1 } END { if (NR > 0) printf ("%0.3f, ", sum / NR)}'
grep ^MEM -A2 *.pcm | grep SKT | awk '{print $5}' | awk '{sum += $1 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'

#Memory % per container type
echo "mosquitto Mem %:"
grep "mosquitto" *.stats | awk -v inst="$instances" '{ sum += $7 } END { if (NR > 0) printf ("%0.3f\n", ( sum * inst ) / NR ) }'
#echo "ia_telegraf Mem %:"
#grep "ia_telegraf" *.stats | awk -v inst="$instances" '{ sum += $7 } END { if (NR > 0) printf ("%0.3f\n", ( sum * inst ) / NR ) }'
echo "ia_telegraf Mem %:"
grep "ia_telegraf" *.stats | awk '{ sum += $7 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
echo "ia_influxdb Mem %:"
grep "ia_influxdbconnector " *.stats | awk '{ sum += $7 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'


#Memory Usage per container type
echo "mosquitto Mem Usage (MiB):"
awk 'BEGIN{ FS=OFS=" " }{ s=substr($4,1,length($4)-2); u=substr($4,length($4)-2);
     if(u=="KiB") $4=(s/1024)"MiB"; else if(u=="GiB") $4=(s*1024)"MiB" }1' *.stats | grep "mosquitto" | awk -v inst="$instances" '{ sum += substr($4, 1, length($4)-3) } END { if (NR > 0) printf ("%0.3f\n", ( sum * inst ) / NR ) }'
echo "ia_telegraf Mem Usage (MiB):"
awk 'BEGIN{ FS=OFS=" " }{ s=substr($4,1,length($4)-2); u=substr($4,length($4)-2);
     if(u=="KiB") $4=(s/1024)"MiB"; else if(u=="GiB") $4=(s*1024)"MiB" }1' *.stats | grep "ia_telegraf" | awk '{ sum += substr($4, 1, length($4)-3) } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'
echo "ia_influxdb Mem Usage (MiB):"
awk 'BEGIN{ FS=OFS=" " }{ s=substr($4,1,length($4)-2); u=substr($4,length($4)-2);
     if(u=="KiB") $4=(s/1024)"MiB"; else if(u=="GiB") $4=(s*1024)"MiB" }1' *.stats | grep "ia_influxdbconnector " | awk '{ sum += substr($4, 1, length($4)-3) } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'


echo "Top CPU Results (CPU%):"
grep "top -" *.top -A 16 | grep -v top | grep -v Tasks | grep -v "%Cpu(s)" | grep -v KiB | grep -v PID | awk '{ printf "%s"",",$9 }' | sed -e 's/,,,/\n/g' | awk '{ for(i=1; i<=NF; i++) j+=$i; print j; j=0 }' | awk '{ sum +=$1 } END { if (NR > 0) print sum / NR}'
echo "Top Average Percent Memory usage:"
avg=`grep 'KiB Mem' *.top | awk '{ sum += $8 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
total=`grep 'KiB Mem' *.top | awk '{ sum += $4 } END { if (NR > 0) printf ("%0.3f\n", sum / NR)}'`
echo "scale=4; $avg / $total" | bc
echo "Top Memory utilization (KiB):"
echo "$avg"
