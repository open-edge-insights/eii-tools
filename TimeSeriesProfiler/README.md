# EIS TimeSeriesProfiler

1. This module calculates the SPS(samples per second) of any EIS time-series modules based on the stream published by that respective module.
2. This module calculates the average e2e time for every sample data to process and it's breakup. The e2e time end to end time required
   for a metric from mqtt-publisher to TimeSeriesProfiler (mqtt-publisher->telegraf->influx->kapacitor->influx->influxdbconnector->
   TimeSeriesProfiler)

## Installing TimeSeriesProfiler requirements

1. To build the TimeSeriesProfiler run the below commands.

    ```sh
        cd tools/TimeSeriesProfiler
        docker-compose build
    ```

## Running TimeSeriesProfiler

1. Pre-requisite : EIS time-series recipe/stack should be running prior to start of this tool

2. Set environment variables accordingly in [config.json](config.json)

3. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

4. If using TimeSeriesProfiler in IPC mode, make sure to set required permissions to socket file created in `EIS_INSTALL_PATH`

    ```sh
        sudo chmod -R 777 /opt/intel/eis/sockets
    ```
    > **NOTE**: This step is required everytime publisher is restarted in IPC mode.
    > Caution: This step will make the streams insecure. Please do not do it on a production machine.

5. If using TimeSeriesProfiler in PROD mode, make sure to set required permissions to certificates.

    ```sh
        sudo chmod -R 755 ../../build/provision/Certificates/ca
        sudo chmod -R 755 ../../build/provision/Certificates/root
    ```
    Note : This step is required everytime provisioning is done. 
    Caution: This step will make the certs insecure. Please do not do it on a production machine.

6. Run the below command to start the TimeSeriesProfiler.

    ```sh
        docker-compose up
    ```
