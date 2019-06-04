#!/bin/bash

if [[ "$(docker images -q publisher:latest 2> /dev/null)" != "" ]]; then
    echo "-- Deleting previous image"
    docker rmi -f publisher
fi

docker build -t publisher .
