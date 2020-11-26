# EIS TimeSeriesProfiler

1. This module calculates the SPS(samples per second) of any EIS time-series modules based on the stream published by that respective module.
2. This module calculates the average e2e time for every sample data to process and it's breakup. The e2e time end to end time required
   for a metric from mqtt-publisher to TimeSeriesProfiler (mqtt-publisher->telegraf->influx->kapacitor->influx->influxdbconnector->
   TimeSeriesProfiler)


## EIS pre-requisites

1. TimeSeriesProfiler expects a set of config, interfaces & public private keys to be present in ETCD as a pre-requisite.
    To achieve this, please ensure an entry for TimeSeriesProfiler with its relative path from [IEdgeInsights](../../) directory is set in the time-series.yml file present in [build](../../build) directory. An example has been provided below:
    ```sh
        AppName:
        - Grafana
        - InfluxDBConnector
        - Kapacitor
        - Telegraf
        - tools/TimeSeriesProfiler
    ```

2. With the above pre-requisite done, please run the below command:
    ```sh
        python3 eis_builder.py -f ./time-series.yml
    ```


## Running TimeSeriesProfiler

1. Pre-requisite :

   Profiling UDF returns "ts_kapacitor_udf_entry" and "ts_kapacitor_udf_exit" timestamp.  
   
    These 2 as examples to refer:
    1. profiler_udf.go
    2. rfc_classifier.py.
   
* configuration required to run profiler_udf.go as profiler udf

   In **[Kapacitor config.json](../../Kapacitor/config.json)** , update "task" key as below:
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
   In **[kapacitor.conf](../../Kapacitor/config/kapacitor.conf)** under udf section:

   ```
      [udf.functions]
         [udf.functions.profiling_udf]
           socket = "/tmp/profiling_udf"
           timeout = "20s"

   ```
 * configuration required to run rfc_classifier.py as profiler udf
   In **[Kapacitor config.json](../../Kapacitor/config.json)** , update "task" key as below:
   ```
   "task": [{
       {
        "tick_script": "rfc_task.tick",
        "task_name": "random_forest_sample"
        }
   }]
   ```
   In **[kapacitor.conf](../../Kapacitor/config/kapacitor.conf)** under udf section:

   ```
    [udf.functions.rfc]
      prog = "python3.7"
      args = ["-u", "/EIS/udfs/rfc_classifier.py"]
      timeout = "60s"
      [udf.functions.rfc.env]
         PYTHONPATH = "/EIS/go/src/github.com/influxdata/kapacitor/udf/agent/py/"
   ```
  keep **[config.json](./config.json)** file as following:
```
  {
    "config": {
        "total_number_of_samples": 10,
        "export_to_csv": "False"
    },
    "interfaces": {
        "Subscribers": [
            {
                "Name": "default",
                "Type": "zmq_tcp",
                "EndPoint": "127.0.0.1:65032",
                "PublisherAppName": "InfluxDBConnector",
                "Topics": [
                    "rfc_results"
                ]
            }
        ]
    }
}
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

5. Refer [provision/README.md](../../README.md) to provision, build and run the tool along with the EIS time-series recipe/stack.

6. Run the following command to see the logs:

    ```sh
        docker logs -f ia_timeseries_profiler
    ```

