# EIS FPS calculator

This module calculates the FPS of any EIS modules based on the stream published by that respective module.

## Pre-requisites

1. Run these commands to install required requirements.

    ```sh
        sudo -H pip3 install -r requirements.txt
    ```

    Needed only for Ubuntu 18.04

    ```sh
        sudo apt-get install -y python3-distutils
    ```

2. Run this command to install python-etcd3

    ```sh
        export PY_ETCD3_VERSION=cdc4c48bde88a795230a02aa574df84ed9ccfa52 && \
        git clone https://github.com/kragniz/python-etcd3 && \
        cd python-etcd3 && \
        git checkout $PY_ETCD3_VERSION && \
        sudo python3.6 setup.py install && \
        cd .. && \
        sudo rm -rf python-etcd3
    ```

3. Install EISMessageBus by following the EISMessageBus [README](../../common/libs/EISMessageBus/README.md)

4. Run this command from current directory to set PYTHONPATH environment variable

    ```sh
        export PYTHONPATH="../../:../../common/libs/EISMessageBus:../../common"
        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
    ```

5. If using FpsCalculator in IPC mode, make sure to set required permissions to socket file created in SOCKET_DIR in [docker_setup/.env](../../docker_setup/.env).

    ```sh
        sudo chmod -R 777 /opt/intel/eis/sockets
    ```

    Caution: This step will make the streams insecure. Please do not do it on a production machine.

6. If using FpsCalculator in PROD mode, make sure to set required permissions to certificates.

    ```sh
        sudo chmod -R 777 ../../docker_setup/provision/Certificates/ca
        sudo chmod -R 777 ../../docker_setup/provision/Certificates/root
    ```

    Caution: This step will make the certs insecure. Please do not do it on a production machine.

## Running FPS calculator

1. Set environment variables accordingly in [config.json](config.json)

2. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

3. Run the Makefile to start the FPS Calculator using this command

    ```sh
        python3.6 fps_calculator.py
    ```
