#!/bin/bash

RED='\033[0;31m'
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
NC='\033[0m' # No Color

function log_warn() {
    echo -e "${YELLOW}WARN: $1 ${NC}"
}

function log_info() {
    echo -e "${GREEN}INFO: $1 ${NC}"
}

function log_error() {
    echo -e "${RED}ERROR: $1 ${NC}"
}

function log_fatal() {
    echo -e "${RED}FATAL: $1 ${NC}"
    exit -1
}

function check_error() {
    if [ $? -ne 0 ] ; then
        log_fatal "$1"
    fi
}

log_info "Installing dependencies"
sudo apt install libmbedtls-dev python3.6 python3.6-dev build-essential pkg-config
check_error "Failed to install dependencies"

log_info "Installing Python dependencies"
sudo -H -E pip3 install -r requirements.txt
check_error "Failed to install Python dependencies"

log_info "Checking for libmbedcrypto soft-link"
if [ ! -f "/usr/lib/x86_64-linux-gnu/libmbedcrypto.so.0" ] ; then
    log_info "Creating soft-link for libmbedcrypto.so.0"
    sudo ln -s /usr/lib/x86_64-linux-gnu/libmbedcrypto.so /usr/lib/x86_64-linux-gnu/libmbedcrypto.so.0
    check_error "Failed to create soft-link"
else
    log_info "Soft-link for libmbedcrypto already exists"
fi

log_info "Done."
log_info "Source the source.sh script: . ./source.sh"
