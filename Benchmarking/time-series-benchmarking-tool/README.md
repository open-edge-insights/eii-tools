# Contents

- [Contents](#contents)
  - [Time Series Benchmarking Tool](#time-series-benchmarking-tool)
  
## Time Series Benchmarking Tool

 >**Note:** In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

These scripts are designed to automate the running of benchmarking tests and the collection of the performance data. This performance data includes the Average Stats of each data stream, and also the CPU%, Memory%, and Memory Read/Write bandwidth.

The Processor Counter Monitor (PCM) is required for measuring memory read/write bandwidth, which can be downloaded and built [here](https://github.com/opcm/pcm)

If you do not have PCM on your system, those values will be blank in the output.ppc

Steps for running a benchmarking test case:

1. Configure [TimeSeriesProfiler config.json](../../TimeSeriesProfiler/config.json) file to recieve rfc_results according to [TimeSeriesProfiler README.md](../../TimeSeriesProfiler/README.md).

2. Change the `command` option in the MQTT publisher [docker-compose.yml](../../mqtt/publisher/docker-compose.yml) to:

   ```sh
     ["--topic", "test/rfc_data", "--json", "./json_files/*.json", "--streams", "<streams>"]
     ```

   For example:

     ```sh
     ["--topic", "test/rfc_data", "--json", "./json_files/*.json", "--streams", "1"]
     ```

3. Run execute test to execute the time series test case.Before running following command, make sure that "export_to_csv" value in [TimeSeriesProfiler config.json](../../TimeSeriesProfiler/config.json) is set to "True":

   ```sh

   USAGE:
   ./execute_test.sh TEST_DIR STREAMS INTERVAL PORT SLEEP PCM_HOME [EII_HOME]

   WHERE:
    TEST_DIR  - Directory containing services.yml and config files for influx, telegraf, and kapacitor
    STREAMS   - The number of streams (1, 2, 4, 8, 16)
    INTERVAL  - Time interval to publish the data in secs
    PORT      - MQTT broker port
    SLEEP     - The number of seconds to wait after the containers come up
    PCM_HOME  - The absolute path to the PCM repository where pcm.x is built
    [EII_HOME] - [Optional] Absolut path to OEI home directory, if running from a non-default location
  
   ```

   For example:

    ```sh
    sudo -E ./execute_test.sh $PWD/samples 2 1 1883 10 /opt/intel/pcm /home/intel/IEdgeInsights
    ```

4. The execution log, performance logs, and the output.ppc will be saved in TEST_DIR/output/< timestamp >/ so that the same test case can be ran multiple times without overwriting the output. You can see if the test ocurred any errors in the execution.log, and you can see the results of a successful test in output.ppc
5. The timeseries profiler output file (named "avg_latency_Results.csv" ) will be stored in TEST_DIR/output/< timestamp >/.

> **Note:** While running benchmarking tool with more than two streams, run  **[MQTT broker](../../mqtt/broker/)* manually with multiple instances and add the mqtt consumers in  **[Telegraf telegraf.conf](../../../Telegraf/config/Telegraf/config.json)* with 'n' number of streams based on the use case.
