#!/bin/bash

# Copyright (c) 2021 Intel Corporation.

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
# Fetch SAR data values and convert to csv format
# --------------------------------------------------------------

sar_data_file="sar_cmd_data.txt"
output_file="data_output.csv"

if [ -f "$sar_data_file" ] ; then
    rm "$sar_data_file"
fi
sar -n DEV 1 60 > ${sar_data_file}


if [ -f "$output_file" ] ; then
    rm "$output_file"
fi

title=`head -n 3 ${sar_data_file} | tail -n 1 | cut -d' ' -f3-`
title_data=`echo ${title} | sed 's/ /,/g'`
echo ${title_data} >> ${output_file}

network_value=`grep eno1 ${sar_data_file} | tail -n 1`
network_value_data=`echo ${network_value} | sed 's/ /,g'`
echo ${network_value_data} >> ${output_file}


