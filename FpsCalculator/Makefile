SHELL := /bin/bash
CURDIR = $(shell pwd)
SERVER_CERTS = /etc/ssl/opcua
CLIENT_CERTS = /etc/ssl/opcua
CA_CERTS = /etc/ssl/ca
SUBSCRIBE_BUS = opcua
DEV_MODE = False
HOST = localhost
PORT = 4840
NUMBER_OF_STREAMS = 1
TOTAL_NUMBER_OF_FRAMES = 1000

run:
	@echo "Starting FPS calculator.."
	python3.6 fps_calculator.py --dev-mode $(DEV_MODE) --subscribe-bus $(SUBSCRIBE_BUS) \
							--certFile $(SERVER_CERTS)/opcua_server_certificate.der \
							--privateFile $(SERVER_CERTS)/opcua_server_key.der \
							--trustFile $(CA_CERTS)/ca_certificate.der \
							--number-of-streams $(NUMBER_OF_STREAMS) \
							--total-frames $(TOTAL_NUMBER_OF_FRAMES)
