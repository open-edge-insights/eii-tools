# EIS TimeSeriesProfiler

1. This module calculates the SPS(samples per second) of any EIS time-series modules based on the stream published by that respective module.
2. This module calculates the average e2e time for every sample data to process and it's breakup. The e2e time end to end time required
   for a metric from mqtt-publisher to TimeSeriesProfiler (mqtt-publisher->telegraf->influx->kapacitor->influx->influxdbconnector->
   TimeSeriesProfiler)

## Installing TimeSeriesProfiler requirements

1. To set environment variables run the below commands.

    ```sh
        cd tools/TimeSeriesProfiler
        set -a
        source ../../build/.env
        set +a
    ```
2. To build the TimeSeriesProfiler run the below commands.

    ```sh
        docker-compose build
    ```

## Running TimeSeriesProfiler

1. Pre-requisite : EIS time-series recipe/stack should be running prior to start of this tool

   Kapacitor service should run profiler_udf.go, configuration required to run the profiler udf

   In [Kapacitor config.json](../../Kapacitor/config.json):
   ```
   "task": [{
       "tick_script": "profiling_udf.tick",
       "task_name": "profiling_udf",
       "udfs": [{
          "type": "go",
          "name": "profiling_udf"
       }]
   }]
   ```
   In [kapacitor.conf](../../Kapacitor/config/kapacitor.conf) under udf section:

   ```
      [udf.functions]
         [udf.functions.profiling_udf]
           socket = "/tmp/profiling_udf"
           timeout = "20s"

   ```

   In [.env](../../build/.env):

   Set the profiling mode as true.

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
 ## ADDITIONAL STEP TO RUN TimeSeriesProfiler IN DEV MODE
 1. Open [.env](../../build/.env)
 2. Set the DEV_MODE variable as "true".
 ```
    DEV_MODE=false
 ```
to
 ```
    DEV_MODE=true
 ```
3. Comment the following lines in the [docker-compose.yml](docker-compose.yml)
```
    secrets:
      - ca_etcd
      - etcd_root_cert
      - etcd_root_key

```
to
```
#    secrets:
#      - ca_etcd
#      - etcd_root_cert
#      - etcd_root_key

```
