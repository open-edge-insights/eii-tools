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

2. Run these commands from IEdgeInsights/DataBusAbstraction/py/test directory

    ```sh
        make build_safestring_lib
    ```

    ```sh
        make build
    ```

3. Run this command from IEdgeInsights/DataAnalytics/VideoAnalytics directory

    ```sh
        source ./setenv.sh
    ```

4. Run this command from current directory to set PYTHONPATH environment variable

    ```sh
        export PYTHONPATH="../../:../../DataBusAbstraction/py/:../../DataBusAbstraction/:../../libs/EISMessageBus"
        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
    ```

## Running FPS calculator

1. Set environment variables accordingly in [config.json](config.json)

    Change values of SUBSCRIBE_STREAM and SUBSCRIBE_BUS to required stream and message bus.
    Currently supported streams for EISMessagebus:
    1. camera1_stream
    2. camera1_stream_results
    3. cam_serial1_results (for multi-cam only)
    4. cam_serial2_results (for multi-cam only)
    5. cam_serial3_results (for multi-cam only)
    6. cam_serial4_results (for multi-cam only)
    7. cam_serial5_results (for multi-cam only)
    8. cam_serial6_results (for multi-cam only)

    Currently supported streams for OPCUA:
    1. stream1_results
    2. cam_serial1_results (for multi-cam only)
    3. cam_serial2_results (for multi-cam only)
    4. cam_serial3_results (for multi-cam only)
    5. cam_serial4_results (for multi-cam only)
    6. cam_serial5_results (for multi-cam only)
    7. cam_serial6_results (for multi-cam only)

2. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

3. Run the Makefile to start the FPS Calculator using this command

    ```sh
        python3.6 fps_calculator.py
    ```
