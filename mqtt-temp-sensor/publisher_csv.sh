#!/bin/bash
echo "*****Running publisher container*****"
docker run --rm -it --net host publisher --csv demo_datafile.csv --sampling_rate 10 --subsample 1
