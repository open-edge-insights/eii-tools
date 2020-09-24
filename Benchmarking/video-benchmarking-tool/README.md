# Video Benchmarking Tool

These scripts are designed to automate the running of benchmarking tests and the collection of the performance data. This performance data includes the FPS of each video stream, and also the CPU%, Memory%, and Memory Read/Write bandwidth.

The Processor Counter Monitor (PCM) is required for measuring memory read/write bandwidth, which can be downloaded and built here: https://github.com/opcm/pcm 

If you do not have PCM on your system, those columns will be blank in the output.csv.

Steps for running a benchmarking test case:

1. Start RTSP server on a sepereate system on the network:

    ```
    $ sh stream_rtsp.sh <number-of-streams> <starting-port-number> <bitrate> <width> <height> <framerate>
    ```
   For example:
   ```
    $ sh stream_rtsp.sh 16 8554 4096 1920 1080 30
   ```

2. Run execute_test.sh with the desired benchmarking config:
    ```
    USAGE:
        ./execute_test.sh TEST_DIR STREAMS SLEEP PCM_HOME [EIS_HOME]

    WHERE:
        TEST_DIR  - The absolute path to directory containing services.yml for the services to be tested, and the config.json and docker-compose.yml for VI and VA if applicable.
        STREAMS   - The number of streams (1, 2, 4, 8, 16)
        SLEEP     - The number of seconds to wait after the containers come up
        PCM_HOME  - The absolute path to the PCM repository where pcm.x is built
        EIS_HOME - [Optional] The absolute path to EIS home directory, if running from a non-default location 
    ```
   For example:
    ```
    ./execute_test.sh $PWD/tc1 16 60 /opt/intel/pcm 
    ```

3. The execution log, performance logs, and the output.csv will be saved in TEST_DIR/< timestamp >/ so that the same test case can be ran multiple times without overwriting the output. You can see if the test ocurred any errors in the execution.log, and you can see the results of a successful test in output.csv.
