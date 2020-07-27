# EIS Video Profiler

This tool can be used to determine the complete metrics involved in the entire Video pipeline by
measuring the time difference between every component of the pipeline and checking for Queue blockages
at every component thereby determining the fast or slow components of the whole pipeline.
It can also be used to calculate the FPS of any EIS modules based on the stream published by that respective
module.

## EIS Video Profiler modes

    By default the EIS Video Profiler supports two modes, which are 'fps' & 'monitor' mode.

1. FPS mode

    Enabled by setting the 'mode' key in [config](./config.json) to 'fps', this mode calculates the frames
    per second of any EIS module by subscribing to that module's respective stream.
    ```sh
        "mode": "fps"
    ```

2. Monitor mode

    Enabled by setting the 'mode' key in [config](./config.json) to 'monitor', this mode calculates average & per frame stats
    for every frame while identifying if the frame was blocked at any queue of any module across the video pipeline thereby
    determining the fastest/slowest components in the pipeline.
    ```sh
        "mode": "monitor"
    ```

    The stats to be displayed by the tool in monitor_mode can be set in the monitor_mode_settings key of [config.json](config.json).
    1. 'display_metadata': Displays the raw meta-data with timestamps associated with every frame.
    2. 'per_frame_stats': Continously displays the per frame metrics of every frame.
    3. 'avg_stats': Continously displays the average metrics of every frame.

  > **Note:**
  > * Pre-requisite for running in profiling or monitor mode: VI/VA should be running with PROFILING_MODE set to **true** in [.env](../../build/.env)
  > * For running Video Profiler in FPS mode, it is recommended to keep PROFILING_MODE set to false in [.env](../../build/.env) for better performance.

## EIS Video Profiler configurations

1. dev_mode

    Setting this to false enables secure communication with the EIS stack. User must ensure this switch is in sync with DEV_MODE in [.env](../../build/.env)
    With PROD mode enabled, the path for the certs mentioned in [config](./config.json) can be changed by the user to point to the required certs.

2. total_number_of_frames

    If mode is set to 'fps', the average FPS is calculated for the number of frames set by this variable.
    If mode is set to 'monitor', the average stats is calculated for the number of frames set by this variable.
    Setting it to (-1) will run the profiler forever unless terminated by signal interrupts('Ctrl+C').
    total_number_of_frames should never be set as (-1) for 'fps' mode.

3. export_to_csv

    Setting this switch to **true** exports csv files for the results obtained in VideoProfiler. For monitor_mode, runtime stats printed in the csv
    are based on the the following precdence: avg_stats, per_frame_stats, display_metadata.

## Installing Video Profiler requirements

1. To install EIS libs on bare-metal, follow the [README](../../common/README.md) of eis_libs_installer.

2. Run this command to install the requirements of Video Profiler

    ```sh
        pip3 install -r requirements.txt
    ```

3. Set the required env by running the below command.

    ```sh
        source ./env.sh
    ```

## Running Video Profiler

1. Set environment variables accordingly in [config.json](config.json)

2. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

3. VideoProfiler should be given an **AppName** which is present in the **Clients** list of the publisher services available in **SubTopics** of [config.json](config.json). This **AppName** has to be set in the [config.json](config.json). If VideoProfiler is subscribing to multiple streams, ensure the **AppName** of VideoProfiler is added in the Clients list of all the publishers.

4. If using Video Profiler in IPC mode, make sure to set required permissions to socket file created in SOCKET_DIR in [build/.env](../../build/.env).

    ```sh
        sudo chmod -R 777 /opt/intel/eis/sockets
    ```
    Note: This step is required everytime publisher is restarted in IPC mode.
    Caution: This step will make the streams insecure. Please do not do it on a production machine.

5. If using Video Profiler in PROD mode, make sure to set required permissions to certificates.

    ```sh
        sudo chmod -R 755 ../../build/provision/Certificates/ca
        sudo chmod -R 755 ../../build/provision/Certificates/root
    ```
    Note : This step is required everytime provisioning is done.
    Caution: This step will make the certs insecure. Please do not do it on a production machine.

6. Run the below command to start the Video Profiler.

    ```sh
        python3.6 video_profiler.py
    ```

7. The runtime stats of Video Profiler if enabled with export_to_csv switch can be found at [video_profiler_runtime_stats](video_profiler_runtime_stats.csv)

  > **Note:**
  > * `poll_interval` option in the VideoIngestion [config](../../VideoIngestion/config.json) sets the delay(in seconds)
      to be induced after every consecutive frame is read by the opencv ingestor.
      Not setting it will ingest frames without any delay.
  > * `videorate` element in the VideoIngestion [config](../../VideoIngestion/config.json) can be used to modify the
      ingestion rate for gstreamer ingestor.
      More info available at [README](../../VideoIngestion/README.md).
  > * `ZMQ_RECV_HWM` option shall set the high water mark for inbound messages on the subscriber socket.
      The high water is a hard limit on the maximum number of outstanding messages ZeroMQ shall queue in memory for
      any single peer that the specified socket is communicating with.
      If this limit has been reached, the socket shall enter an exeptional state and drop incoming messages.
  > * In case of running Video Profiler for GVA use case we do not display the stats of the algo running with GVA since no
      UDFs are used.
  > * The rate at which the UDFs process the frames can be measured using the FPS UDF and ingestion rate can be monitored accordingly.
      In case multiple UDFs are used, the FPS UDF is required to be added as the last UDF.
  > * In case running this tool with VI & VA in two different nodes, same time needs to be set in both the nodes.

## Optimizing EIS Video pipeline by analysing Video Profiler results

1. VI ingestor/UDF input queue is blocked, consider reducing ingestion rate.

    If this log is displayed by the Video Profiler tool, it indicates that the ingestion rate is too high or the VideoIngestion
    UDFs are slow and causing latency throughout the pipeline.
    As per the log suggests, the user can increase the poll_interval to a optimum value to reduce the blockage of VideoIngestion
    ingestor queue thereby optimizing the video pipeline in case using the opencv ingestor.
    In case Gstreamer ingestor is used, the videorate option can be optimized by following the [README](../../VideoIngestion/README.md).

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
