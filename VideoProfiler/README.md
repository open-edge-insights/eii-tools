# Contents

- [Contents](#contents)
  - [EII Video Profiler](#eii-video-profiler)
    - [EII Video Profiler pre-requisites](#eii-video-profiler-pre-requisites)
    - [EII Video Profiler modes](#eii-video-profiler-modes)
    - [EII Video Profiler configurations](#eii-video-profiler-configurations)
    - [Running Video Profiler](#running-video-profiler)
    - [Running VideoProfiler in helm usecase](#running-videoprofiler-in-helm-usecase)
    - [Optimizing EII Video pipeline by analysing Video Profiler results](#optimizing-eii-video-pipeline-by-analysing-video-profiler-results)
    - [Benchmarking with multi instance config](#benchmarking-with-multi-instance-config)

## EII Video Profiler

This tool can be used to determine the complete metrics involved in the entire Video pipeline by
measuring the time difference between every component of the pipeline and checking for Queue blockages
at every component thereby determining the fast or slow components of the whole pipeline.
It can also be used to calculate the FPS of any EII modules based on the stream published by that respective
module.

>**Note:** In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

### EII Video Profiler pre-requisites

1. VideoProfiler expects a set of config, interfaces & public private keys to be present in ETCD as a pre-requisite.
    To achieve this, please ensure an entry for VideoProfiler with its relative path from [IEdgeInsights](../../) directory is set in any of the .yml files present in [build/usecases](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases) directory. An example has been provided below:

    ```sh
        AppContexts:
        - VideoIngestion
        - VideoAnalytics
        - tools/VideoProfiler
    ```

2. With the above pre-requisite done, please run the below to command:

    ```sh
        python3 builder.py -f usecases/video-streaming.yml
    ```

### EII Video Profiler modes

   By default the EII Video Profiler supports two modes, which are 'fps' & 'monitor' mode.

1. FPS mode

   Enabled by setting the 'mode' key in [config](./config.json) to 'fps', this mode calculates the frames
   per second of any EII module by subscribing to that module's respective stream.

    ```sh
        "mode": "fps"
    ```

   > **Note:**
   >
   > - For running Video Profiler in FPS mode, it is recommended to keep PROFILING_MODE set to false in [.env](https://github.com/open-edge-insights/eii-core/tree/master/build/.env) for better performance.

2. Monitor mode

   Enabled by setting the 'mode' key in [config](./config.json) to 'monitor', this mode calculates average & per frame stats
   for every frame while identifying if the frame was blocked at any queue of any module across the video pipeline thereby
   determining the fastest/slowest components in the pipeline.
   To be performant in profiling scenarios, VideoProfiler is enabled to work when subscribing only to a single topic in monitor mode.

   User must ensure that `ingestion_appname` and `analytics_appname` fields of the `monitor_mode_settings` need to be set accordingly for monitor mode.

   Refer the below exmaple config where VideoProfiler is used in monitor mode to subscribe PySafetyGearAnalytics CustomUDF results.

    ```javascript
        "config": {
        "mode": "monitor",
        "monitor_mode_settings": {
                                    "ingestion_appname": "PySafetyGearIngestion",
                                    "analytics_appname": "PySafetyGearAnalytics",
                                    "display_metadata": false,
                                    "per_frame_stats":false,
                                    "avg_stats": true
                                },
        "total_number_of_frames" : 5,
        "export_to_csv" : false
    }
    ```

    ```sh
        "mode": "monitor"
    ```

   The stats to be displayed by the tool in monitor_mode can be set in the monitor_mode_settings key of [config.json](config.json).
    1. 'display_metadata': Displays the raw meta-data with timestamps associated with every frame.
    2. 'per_frame_stats': Continously displays the per frame metrics of every frame.
    3. 'avg_stats': Continously displays the average metrics of every frame.

> **Note:**
>
> - Pre-requisite for running in profiling or monitor mode: VI/VA should be running with PROFILING_MODE set to **true** in [.env](https://github.com/open-edge-insights/eii-core/tree/master/build/.env)
> - It is mandatory to have a udf for running in monitor mode. For instance [GVASafetyGearIngestion](https://github.com/open-edge-insights/video-custom-udfs/blob/master/GVASafetyGearIngestion/README.md) does not have any udf(since it uses GVA elements) so it will not be supported in monitor mode. The workaround to use GVASafetyGearIngestion in monitor mode is to add [dummy-udf](https://github.com/open-edge-insights/video-common/blob/master/udfs/README.md
    ) in [GVASafetyGearIngestion-config](https://github.com/open-edge-insights/video-custom-udfs/blob/master/GVASafetyGearIngestion/config.json).

### EII Video Profiler configurations

1. dev_mode

   Setting this to false enables secure communication with the EII stack. User must ensure this switch is in sync with DEV_MODE in [.env](https://github.com/open-edge-insights/eii-core/tree/master/build/.env)
   With PROD mode enabled, the path for the certs mentioned in [config](./config.json) can be changed by the user to point to the required certs.

2. total_number_of_frames

   If mode is set to 'fps', the average FPS is calculated for the number of frames set by this variable.
   If mode is set to 'monitor', the average stats is calculated for the number of frames set by this variable.
   Setting it to (-1) will run the profiler forever unless terminated by signal interrupts('Ctrl+C').
   total_number_of_frames should never be set as (-1) for 'fps' mode.

3. export_to_csv

   Setting this switch to **true** exports csv files for the results obtained in VideoProfiler. For monitor_mode, runtime stats printed in the csv
   are based on the the following precdence: avg_stats, per_frame_stats, display_metadata.

### Running Video Profiler

1. Set environment variables accordingly in [config.json](config.json).

2. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

3. If VideoProfiler is subscribing to multiple streams, ensure the **AppName** of VideoProfiler is added in the Clients list of all the publishers.

4. If using Video Profiler in IPC mode, make sure to set required permissions to socket file created in SOCKET_DIR in [build/.env](https://github.com/open-edge-insights/eii-core/blob/master/build/.env).

    ```sh
        sudo chmod -R 777 /opt/intel/eii/sockets
    ```

   **Note:**

   - This step is required everytime publisher is restarted in IPC mode.

      Caution: This step will make the streams insecure. Please do not do it on a production machine.

   - Refer the below VideoProfiler interface example to subscribe to PyMultiClassificationIngestion CutomUDF results in fps mode.

      ```javascript
        "/VideoProfiler/interfaces": {
            "Subscribers": [
                {
                    "EndPoint": "/EII/sockets",
                    "Name": "default",
                    "PublisherAppName": "PyMultiClassificationIngestion",
                    "Topics": [
                        "py_multi_classification_results_stream"
                    ],
                    "Type": "zmq_ipc"
                }
            ]
        },
      ```

5. If running VideoProfiler with helm usecase or trying to subscribe to any external publishers outside the eii network, please ensure the correct IP of publisher has been provided in the interfaces section in [config](config.json) and correct ETCD host & port are set in environment for **ETCD_ENDPOINT** & **ETCD_HOST**.
    - For example, for helm use case, since the ETCD_HOST and ETCD_PORT are different, run the commands mentioned below wit the required HOST IP:

    ```sh
        export ETCD_HOST="<HOST IP>"
        export ETCD_ENDPOINT="<HOST IP>:32379"
    ```

6. Refer [provision/README.md](https://github.com/open-edge-insights/eii-core/blob/master/README.md#provision) to provision, build and run the tool along with the EII video-streaming recipe/stack.

7. Run the following command to see the logs:

    ```sh
        docker logs -f ia_video_profiler
    ```

8. The runtime stats of Video Profiler if enabled with export_to_csv switch can be found at [video_profiler_runtime_stats](video_profiler_runtime_stats.csv)

  > **Note:**
  >
  > - `poll_interval` option in the VideoIngestion [config](https://github.com/open-edge-insights/video-ingestion/blob/master/config.json) sets the delay(in seconds)
      to be induced after every consecutive frame is read by the opencv ingestor.
      Not setting it will ingest frames without any delay.
  > - `videorate` element in the VideoIngestion [config](https://github.com/open-edge-insights/video-ingestion/blob/master/config.json) can be used to modify the
      ingestion rate for gstreamer ingestor.
      More info available at [README](https://github.com/open-edge-insights/video-ingestion/blob/master/README.md).
  > - `ZMQ_RECV_HWM` option shall set the high water mark for inbound messages on the subscriber socket.
      The high water is a hard limit on the maximum number of outstanding messages ZeroMQ shall queue in memory for
      any single peer that the specified socket is communicating with.
      If this limit has been reached, the socket shall enter an exeptional state and drop incoming messages.
  > - In case of running Video Profiler for GVA use case we do not display the stats of the algo running with GVA since no
      UDFs are used.
  > - The rate at which the UDFs process the frames can be measured using the FPS UDF and ingestion rate can be monitored accordingly.
      In case multiple UDFs are used, the FPS UDF is required to be added as the last UDF.
  > - In case running this tool with VI & VA in two different nodes, same time needs to be set in both the nodes.

### Running VideoProfiler in helm usecase

For running VideoProfiler in helm usecase to subscribe to either VideoIngestion/VideoAnalytics or any other EII service, the etcd endpoint, volume mount for helm certs and service endpoints are to be updated.

For connecting to the etcd server running in helm environment, the endpoint and required volume mounts should be modified in the following manner in environment & volumes section of [docker-compose.yml](docker-compose.yml):

  ```yaml
  ia_video_profiler:
    depends_on:
      - ia_common
    ...
    environment:
    ...
      ETCD_HOST: ${ETCD_HOST}
      ETCD_CLIENT_PORT: ${ETCD_CLIENT_PORT}
      # Update this variable referring
      # for helm use case
      ETCD_ENDPOINT: <HOST_IP>:32379
      CONFIGMGR_CERT: "/run/secrets/VideoProfiler/VideoProfiler_client_certificate.pem"
      CONFIGMGR_KEY: "/run/secrets/VideoProfiler/VideoProfiler_client_key.pem"
      CONFIGMGR_CACERT: "/run/secrets/rootca/cacert.pem"
    ...
    volumes:
      - "${EII_INSTALL_PATH}/tools_output:/app/out"
      - "${EII_INSTALL_PATH}/sockets:${SOCKET_DIR}"
      - ./helm-eii/eii-deploy/Certificates/rootca:/run/secrets/rootca
      - ./helm-eii/eii-deploy/Certificates/VideoProfiler:/run/secrets/VideoProfiler
  ```

For connecting to any service running in helm usecase, the container IP associated with the specific service should be updated in the Endpoint section in VideoProfiler [config](config.json):

The IP associated with the service container can be obtained by checking the container pod IP using docker inspect. Assuming we are connecting to VideoAnalytics service, the command to be run would be:

```sh
 docker inspect <VIDEOANALYTICS CONTAINER ID> | grep VIDEOANALYTICS
```

The output of the above command consists the IP of the VideoAnalytics container that can be updated in VideoProfiler config using EtcdUI:

```sh
 "VIDEOANALYTICS_SERVICE_HOST=10.99.204.80"
```

The config can be updated with the obtained container IP in the following way:

```javascript
    {
        "interfaces": {
            "Subscribers": [
                {
                    "Name": "default",
                    "Type": "zmq_tcp",
                    "EndPoint": "10.99.204.80:65013",
                    "PublisherAppName": "VideoAnalytics",
                    "Topics": [
                        "camera1_stream_results"
                    ]
                }
            ]
        }
    }
 ```

### Optimizing EII Video pipeline by analysing Video Profiler results

1. VI ingestor/UDF input queue is blocked, consider reducing ingestion rate.

   If this log is displayed by the Video Profiler tool, it indicates that the ingestion rate is too high or the VideoIngestion
   UDFs are slow and causing latency throughout the pipeline.
   As per the log suggests, the user can increase the poll_interval to a optimum value to reduce the blockage of VideoIngestion
   ingestor queue thereby optimizing the video pipeline in case using the opencv ingestor.    In case Gstreamer ingestor is used, the videorate option can be optimized by following the [README](https://github.com/open-edge-insights/video-ingestion/blob/master/README.md).

2. VA subs/UDF input queue is blocked, consider reducing ZMQ_RECV_HWM value or reducing ingestion rate.

   If this log is displayed by the Video Profiler tool, it indicates that the VideoAnalytics UDFs are slow and causing latency
   throughout the pipeline.
   As per the log suggests, the user can consider reducing ZMQ_RECV_HWM to an optimum value to free the VideoAnalytics UDF input/subscriber
   queue by dropping incoming frames or reducing the ingestion rate to a required value.

3. UDF VI output queue blocked.

   If this log is displayed by the Video Profiler tool, it indicates that the VI to VA messagebus transfer is delayed.
    1. User can consider reducing the ingestion rate to a required value.
    2. User can increase ZMQ_RECV_HWM to an optimum value so as to not drop
    the frames when the queue is full or switching to IPC mode of communication.

4. UDF VA output queue blocked.

   If this log is displayed by the Video Profiler tool, it indicates that the VA to VideoProfiler messagebus transfer is delayed.
    1. User can consider reducing the ingestion rate to a required value.
    2. User can increase ZMQ_RECV_HWM to an optimum value so as to not drop
    the frames when the queue is full or switching to IPC mode of communication.

### Benchmarking with multi instance config

1. EII supports multi instance config generation for benchmarking purposes. This can be acheived by running the [builder.py](https://github.com/open-edge-insights/eii-core/blob/master/build/builder.py) with certain parameters, please refer to the **Multi instance config generation** section of **EII Pre-Requisites** in [README](https://github.com/open-edge-insights/eii-core/blob/master/README.md#eii-prerequisites-installation) for more details.

2. For running VideoProfiler for multiple streams, run the builder with the **-v** flag provided the pre-requisites mentioned above are done. Given below is an example for generating **6** streams config:

    ```sh
        python3 builder.py -f usecases/video-streaming.yml -v 6
    ```

> **Note:**
>
> - For multi instance monitor mode usecase, please ensure only **VideoIngestion** & **VideoAnalytics** are used as **AppName** for Publishers.
> - Running **VideoProfiler** with **CustomUDFs** for monitor mode is supported for single stream only. If required for multiple streams, please ensure **VideoIngestion** & **VideoAnalytics** are used as **AppName**.
> -In IPC mode, for accelerators: `MYRIAD`, `GPU` and USB 3.0 Vision cameras, add `user: root` in [VideoProfiler-docker-compose.yml](../../VideoProfiler/docker-compose.yml) as the subscriber needs to run as `root` if the publisher is running as `root`.
