# Contents

- [Contents](#contents)
  - [Video Benchmarking Tool](#video-benchmarking-tool)

## Video Benchmarking Tool

 >**Note:** In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

These scripts are designed to automate the running of benchmarking tests and the collection of the performance data. This performance data includes the FPS of each video stream, and also the CPU %, Memory %, and Memory Read/Write bandwidth.

The Processor Counter Monitor (PCM) is required for measuring memory read/write bandwidth, which can be downloaded and built [here](https://github.com/opcm/pcm).

If you do not have PCM on your system, those columns will be blank in the output.csv.

Refer [README-Using-video-accelerators](https://github.com/open-edge-insights/eii-core#using-video-accelerators-in-ingestionanalytics-containers) for using video accelerators and follow the required pre-reqisities to work with GPU, MYRIAD and HDDL devices.

 > **Note:**
 >
 > - To run the gstreamer pipeline mentioned in [sample_test/config.json](sample_test/config.json), copy the required model files to `[WORKDIR]/IEdgeInsights/VideoIngestion/models`. For more information, refer to the [models-readme](https://github.com/open-edge-insights/video-ingestion/blob/master/models/README.md).
 > - In IPC mode, for accelerators: `MYRIAD`, `GPU` and USB 3.0 Vision cameras, add `user: root` in [VideoProfiler-docker-compose.yml](../../VideoProfiler/docker-compose.yml) as the subscriber needs to run as `root` if the publisher is running as `root`.
 > - For `GPU` device there is an initial delay while the model is compiled and loaded. This can affect the first benchmarking results especially on low stream count. This will be reduced on subsequent runs using kernel caching. To ensure that the kernel cache files are created, remove `read_only: true` in the `docker-compose.yml` file for VI so that files can be generated.
 > - The `docker-compose.yml` files of VI and VideoProfiler is picked from their respective repos. So any changes needed should be applied in their respective repos.

Steps for running a benchmarking test case:

1. Ensure the VideoProfiler requirements are installed by following the README at [README](../../VideoProfiler/README.md).

2. Start the RTSP server on a sepereate system on the network:

    ```sh
    ./stream_rtsp.sh <number-of-streams> <starting-port-number> <bitrate> <width> <height> <framerate>
    ```

   For example:

   ```sh
    ./stream_rtsp.sh 16 8554 4096 1920 1080 30
   ```

3. Run execute_test.sh with the desired benchmarking config:

    ```sh
    USAGE:
        ./execute_test.sh TEST_DIR STREAMS SLEEP PCM_HOME [EII_HOME]

    WHERE:
        TEST_DIR  - The absolute path to directory containing services.yml for the services to be tested, and the config.json and docker-compose.yml for VI and VA if applicable.
        STREAMS   - The number of streams (1, 2, 4, 8, 16)
        SLEEP     - The number of seconds to wait after the containers come up
        PCM_HOME  - The absolute path to the PCM repository where pcm.x is built
        EII_HOME - [Optional] The absolute path to OEI home directory, if running from a non-default location
    ```

   For example:

    ```sh
    sudo -E ./execute_test.sh $PWD/sample_test 16 60 /opt/intel/pcm /home/intel/IEdgeInsights
    ```

4. The execution log, performance logs, and the output.csv will be saved in `TEST_DIR/< timestamp >/` so that the same test case can be run multiple times without overwriting the output. If any errors occur during the test, you can view its details from the execution.log file. For successful test, you can view the results in final_output.csv.
