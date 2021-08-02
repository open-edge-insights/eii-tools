DiscoverHistory tool helps in pulling the history meta-data and images from InfluxDB and ImageStore containers respectively

# Steps to build and run DiscoverHistory service

* **Running in PROD mode**

 1. DiscoverHistory expects a set of config, interfaces & public private keys to be present in ETCD as a pre-requisite.
    To achieve this, please ensure an entry for DiscoverHistory with its relative path from [IEdgeInsights](../../) directory is set in the video-streaming-storage.yml file present in [build/usecases](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases) directory. An example has been provided below:
    ```sh
        AppContexts:
        - VideoIngestion
        - VideoAnalytics
        - Visualizer
        - WebVisualizer
        - tools/DiscoverHistory
        - ImageStore
        - InfluxDBConnector
    ```

 2. Open "config.json"
 3. Provide the required query to be passed on to InfluxDB.
 4. With the above pre-requisite done, please run the below to command:
    ```sh
        python3 builder.py -f usecases/video-streaming-storage.yml
    ```
 5. Refer [main EII README.md](https://github.com/open-edge-insights/eii-core/blob/master/README.md) to provision, build and run the tool along with the EII video-streaming-storage recipe/stack.
 6. Check imagestore and influxdbconnector services are running.
 7. You will find data & frames directories at "/opt/intel/eii/tools_output".
    (Note: if img_handle is part of select statement , then only frames
    directory will be created)
 8. Use ETCDUI to change the query in configuration. Please run below command to start container with new configuration:
     ```sh
        docker restart ia_discover_history
     ```

* **Running in DEV mode**

 1. Open [.env](https://github.com/open-edge-insights/eii-core/blob/master/build/.env)
 2. Set the DEV_MODE variable as "true".
 ```
    DEV_MODE=false
 ```
to
 ```
    DEV_MODE=true
 ```

> **NOTE**:
> * Building the base images like ia_common, ia_eiibase are must in cases if this tool isn't run on the same node
>   where EII is running.
> * Please ensure that the base images i.e. ia_common and ia_eiibase are present on the node where this tool is run.

# List of sample select queries

1. "select * from camera1_stream_results order by desc limit 10"
   This query will return latest 10 records.

2. "select height,img_handle from camera1_stream_results order by desc limit 10"

3. "select * from camera1_stream_results where time>='2019-08-30T07:25:39Z' AND time<='2019-08-30T07:29:00Z'"
    This query will return all the records between the given time frame i.e. (time>='2019-08-30T07:25:39Z' AND time<='2019-08-30T07:29:00Z')

4. "select * from camera1_stream_results where time>=now()-1h"
    This query will return all the records from the current time, going back upto last 1 hour.

# To run the tool in zmq_ipc mode

User needs to modify interface section of **[config.json](./config.json)** as following

```
    {
        "type": "zmq_ipc",
        "EndPoint": "/EII/sockets"
    }
```

----
**NOTE**:
If you want good and bad frames then the query must contain the following parameters:

	*img_handle
	*defects
	*encoding_level
	*encoding_type
	*height
	*width
	*channel

    Example:
     "select img_handle, defects, encoding_level, encoding_type,  height, width, channel from camera1_stream_results order by desc limit 10"

     or

     "select * from camera1_stream_results order by desc limit 10"
----
