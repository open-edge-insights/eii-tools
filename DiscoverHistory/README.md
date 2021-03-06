# Contents

- [Contents](#contents)
  - [DiscoverHistory Tool](#discoverhistory-tool)
    - [Build and run the DiscoverHistory tool](#build-and-run-the-discoverhistory-tool)
      - [Prerequisites](#prerequisites)
      - [Run the DiscoverHistory tool in the PROD mode](#run-the-discoverhistory-tool-in-the-prod-mode)
      - [Run the DiscoverHistory tool in the DEV mode](#run-the-discoverhistory-tool-in-the-dev-mode)
      - [Run the DiscoverHistory tool in the zmq_ipc mode](#run-the-discoverhistory-tool-in-the-zmq_ipc-mode)
    - [Sample select queries](#sample-select-queries)
    - [Multi-instance feature support for the Builder script with the DiscoverHistory tool](#multi-instance-feature-support-for-the-builder-script-with-the-discoverhistory-tool)

## DiscoverHistory Tool

You can get history metadata and images from the InfluxDB and ImageStore containers using the DiscoverHistory tool.

>**Note:** In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

### Build and run the DiscoverHistory tool

This section provides information for building and running DiscoverHistory tool in various modes such as the PROD mode and the DEV mode. To run the DiscoverHistory tool base images should be on the same node. Ensure that on the node where the DiscoverHistory tool is running, the `ia_common` and `ia_eiibase` base images are also available. For scenario, where OEI and DiscoverHistory tool are not running on the same node, then you must build the base images, `ia_common` and `ia_eiibase`.

#### Prerequisites

As a prerequisite to run the DiscoverHistory tool, a set of config, interfaces, public, and private keys should be present in etcd. To meet the prerequisite, ensure that an entry for the DiscoverHistory tool with its relative path from the `[WORK_DIR]/IEdgeInsights]` directory is set in the `video-streaming-storage.yml` file in the `[WORK_DIR]/IEdgeInsights/build/usecases/` directory. For more information, see the following example:

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

#### Run the DiscoverHistory tool in the PROD mode

After completing the prerequisites, perform the following steps to run the DiscoverHistory tool in the PROD mode:

 1. Open the `config.json` file.
 2. Enter the query for InfluxDB.
 3. Run the following command to generate the new `docker-compose.yml` that includes DiscoverHistory:

    ```sh
        python3 builder.py -f usecases/video-streaming-storage.yml
    ```

 4. Provision, build, and run the DiscoverHistory tool along with the OEI video-streaming-storage recipe or stack. For more information, refer to the [OEI README](https://github.com/open-edge-insights/eii-core/blob/master/README.md).
 5. Check if the `imagestore` and `influxdbconnector` services are running.
 6. Locate the `data` and the `frames` directories from the following path:
  `/opt/intel/eii/tools_output`.
    >**Note:** The `frames` directory will be created only if `img_handle` is part of the select statement.
 7. Use the ETCDUI to change the query in the configuration.
 8. Run the following command to start container with new configuration:

    ```sh
       docker restart ia_discover_history
    ```

#### Run the DiscoverHistory tool in the DEV mode

After completing the prerequisites, perform the following steps to run the DiscoverHistory tool in the DEV mode:

 1. Open the [.env] file from the `[WORK_DIR]/IEdgeInsights/build` directory.
 2. Set the `DEV_MODE` variable as `true`.

#### Run the DiscoverHistory tool in the zmq_ipc mode

After completing the prerequisites, to run the DiscoverHistory tool in the zmq_ipc mode, modify the interface section of the `config.json` file as follows:

```json
    {
        "type": "zmq_ipc",
        "EndPoint": "/EII/sockets"
    }
```


### Sample select queries

The following table shows the samples for the select queries and its details:

| Select Query      | Details      |
|  ---  |  ---  |
| "select * from camera1_stream_results order by desc limit 10"      | This query will return latest 10 records.      |
| "select height,img_handle from camera1_stream_results order by desc limit 10"      |       |
| "select * from camera1_stream_results where time>='2019-08-30T07:25:39Z' AND time<='2019-08-30T07:29:00Z'"      | This query will return all the records between the given time frame, which is (time>='2019-08-30T07:25:39Z' and time<='2019-08-30T07:29:00Z')      |
| "select * from camera1_stream_results where time>=now()-1h"      | This query will return all the records from the current time, going back upto last 1 hour.      |
|       |       |

>**Note:**
> Include the following parameters in the query to get the good and the bad frames:
>
> - *img_handle
> - *defects
> - *encoding_level
> - *encoding_type
> - *height
> - *width
> - *channel
>
> The following examples shows how to include the parameters:
>
> - "select img_handle, defects, encoding_level, encoding_type, height, width, channel from camera1_stream_results order by desc limit 10"
> - "select * from camera1_stream_results order by desc limit 10"

### Multi-instance feature support for the Builder script with the DiscoverHistory tool

The multi-instance feature support of Builder works only for the video pipeline (`[WORK_DIR]/IEdgeInsights/build/usecase/video-streaming.yml`). For more details, refer to the [OEI core readme](https://github.com/open-edge-insights/eii-core/blob/master/README.md#running-builder-to-generate-multi-instance-configs)

In the following example you can view how to change the configuration to use the builder.py script -v 2 feature with 2 instances of the DiscoverHistory tool enabled:
![DiscoverHistory instance 1 interfaces](img/discoverHistoryTool-conf-change1.png)
![DiscoverHistory instance 2 interfaces](img/discoverHistoryTool-conf-change2.png)
