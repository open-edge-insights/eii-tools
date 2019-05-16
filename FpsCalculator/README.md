# EIS FPS calculator

This module calculates the FPS of any EIS modules based on the stream published by that respective module.

## Pre-requisites

1. Run this command to install xlwt requirement.

    ```sh
        pip3 install xlwt
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
        export PYTHONPATH="../../:../../ImageStore/protobuff:../../ImageStore/protobuff/py/:../../DataAgent/da_grpc/protobuff/py:../../DataAgent/da_grpc/protobuff/py/pb_internal:../../DataBusAbstraction/py/:../../DataBusAbstraction/"
    ```

## Running FPS calculator

1. Set environment variables accordingly in Makefile 

    Change values of SUBSCRIBE_STREAM and SUBSCRIBE_BUS to required stream and message bus.
    Currently supported streams for StreamSubLib:
    1. stream1
    2. stream1_results
    3. cam_serial1_results (for multi-cam only)
    4. cam_serial2_results (for multi-cam only)
    5. cam_serial3_results (for multi-cam only)
    6. cam_serial4_results (for multi-cam only)
    7. cam_serial5_results (for multi-cam only)
    8. cam_serial6_results (for multi-cam only)

    Currently supported streams for OPCUA:
    1. stream1_results

2. Set the required output stream/streams in config.json file.

3. Run the Makefile to start the FPS Calculator using this command

    ```sh
        make run
    ```
