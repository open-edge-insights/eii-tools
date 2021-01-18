# Time Series Benchmarking Tool

These scripts are designed to automate the running of benchmarking tests and the collection of the performance data. This performance data includes the Samples per second (SPS) of each data stream, and also the CPU%, Memory%, and Memory Read/Write bandwidth.

The Processor Counter Monitor (PCM) is required for measuring memory read/write bandwidth, which can be downloaded and built here: https://github.com/opcm/pcm 

If you do not have PCM on your system, those values will be blank in the output.ppc

Steps for running a benchmarking test case:

1. Start 1 broker for every data stream you want to send with the publisher in step #2:

    ```sh
    $ cd ../../mqtt-publisher/
    $ ./broker.sh <port> &
    ```
   For example:
   ```sh
    $ cd ../../mqtt-publisher/
    $ ./broker.sh 1883 &
    $ ./broker.sh 1884 &
   ```

2. Build and run MQTT publisher:
    ```sh
     $ cd ../../mqtt-publisher/
     $ ./build.sh
     $ ./publisher_json.sh <streams>
    ```
   For example:
    ```sh
     $ cd ../../mqtt-publisher/
     $ ./build.sh
     $ ./publisher_json.sh 2
    ```

3. Run execute test to execute the time series test case.Before running following command, make sure that "export_to_csv" value in **[TimeSeriesProfiler config.json](../../TimeSeriesProfiler/config.json)** is set to "True":
   ```
	USAGE:
	  ./execute_test.sh TEST_DIR STREAMS SLEEP PCM_HOME [EIS_HOME]

	WHERE:
	  TEST_DIR  - Directory containing services.yml and config files for influx, telegraf, and kapacitor
	  STREAMS   - The number of streams (1, 2, 4, 8, 16)
	  SLEEP     - The number of seconds to wait after the containers come up
          PCM_HOME  - The absolute path to the PCM repository where pcm.x is built
          [EIS_HOME] - [Optional] Absolut path to EIS home directory, if running from a non-default location
   ```

4. The execution log, performance logs, and the output.ppc will be saved in TEST_DIR/output/< timestamp >/ so that the same test case can be ran multiple times without overwriting the output. You can see if the test ocurred any errors in the execution.log, and you can see the results of a successful test in output.ppc

5. The timeseries profiler output file (named "SPS_Results.csv" ) will be store in TEST_DIR/output/< timestamp >/.