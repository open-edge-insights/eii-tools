#!/bin/bash
docker run --rm -d -p 1883:1883 --name mosquitto trafex/alpine-mosquitto
