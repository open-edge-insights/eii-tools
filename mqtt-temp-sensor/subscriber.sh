#!/bin/bash
docker exec -ti mosquitto mosquitto_sub -h 127.0.0.1 -v -t '#'
