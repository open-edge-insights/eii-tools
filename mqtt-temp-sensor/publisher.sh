#!/bin/bash
echo "*****Running publisher container*****"
if [ "$1" = "detached_mode" ]; then
docker run --rm -itd --net host --name publisher publisher
else
docker run --rm -it --net host --name publisher publisher
fi
