#!/bin/bash
echo "*****Running publisher container*****"
docker run --rm -it --net host --name publisher publisher
