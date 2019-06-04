#!/bin/bash

UBUNTU_IMAGE_VERSION=18.04
VISUALIZER_VERSION=1.0
hostTimezone=`timedatectl status | grep "zone" | sed -e 's/^[ ]*Time zone: \(.*\) (.*)$/\1/g'`
hostTimezone=`echo $hostTimezone`
buildLogFile="build_logs.log"

docker build --build-arg HOST_TIME_ZONE="$HOST_TIME_ZONE" \
             --build-arg UBUNTU_IMAGE_VERSION="$UBUNTU_IMAGE_VERSION" \
             -t ia/visualizer:"$VISUALIZER_VERSION" . | tee $buildLogFile

errorStrs=("fix-missing" "Unable to locate package")
for errorStr in "${errorStrs[@]}"
do
    tail $buildLogFile | grep "$errorStr"
    if [ `echo $?` = "0" ]
    then
        docker build --build-arg HOST_TIME_ZONE="$hostTimezone" \
                     --build-arg UBUNTU_IMAGE_VERSION="$UBUNTU_IMAGE_VERSION" \
                     --no-cache \
                     -t ia/visualizer:"$VISUALIZER_VERSION" . | tee $buildLogFile
        tail $buildLogFile | grep "Successfully"
        if [ `echo $?` != "0" ]
        then
            echo "ERROR: docker build --no-cache failed too, so exiting..."
            exit -1
        fi
    fi
done