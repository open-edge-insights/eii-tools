# EIS Video Profiler

This tool can be used to determine the complete metrics involved in the entire Video pipeline by
measuring the time difference between every component of the pipeline and checking for Queue blockages
at every component thereby determining the fast or slow components of the whole pipeline.
It can also be used to calculate the FPS of any EIS modules based on the stream published by that respective
module.

## EIS Video Profiler modes

1. FPS mode

    Enabled by setting the 'fps_mode' to true in [config.json](config.json), this mode calculates the frames
    per second of any EIS module by subscribing to that module's respective stream.

2. Profiling mode

    Enabled by setting the 'profiling_mode' to true in [config.json](config.json), this mode calculates the time
    spent by every frame at different points throughout the pipeline.

3. Monitor mode

    Enabled by setting the 'monitor_mode' to true in [config.json](config.json), this mode combines FPS & profiling mode
    and also calculates average & per frame stats for every frame whilst identifying if the frame was blocked at any
    queue of any module across the video pipeline thereby determining the fastest/slowest components in the pipeline.

    The stats to be displayed by the tool in monitor_mode can be set in the monitor_mode_settings key of [config.json](config.json).
    1. 'display_metadata': Displays the raw meta-data with timestamps associated with every frame.
    2. 'per_frame_stats': Continously displays the per frame metrics of every frame.
    3. 'avg_stats': Continously displays the average metrics of every frame.

## Installing Video Profiler requirements

1. To install EIS libs on bare-metal, follow the [README](../../common/README.md) of eis_libs_installer.

2. Set the required env by running the below command.

    ```sh
        source ./env.sh
    ```

## Running Video Profiler

1. Set environment variables accordingly in [config.json](config.json)

2. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

5. If using Video Profiler in IPC mode, make sure to set required permissions to socket file created in SOCKET_DIR in [build/.env](../../build/.env).

    ```sh
        sudo chmod -R 777 /opt/intel/eis/sockets
    ```
    Note: This step is required everytime publisher is restarted in IPC mode.
    Caution: This step will make the streams insecure. Please do not do it on a production machine.

4. If using Video Profiler in PROD mode, make sure to set required permissions to certificates.

    ```sh
        sudo chmod -R 755 ../../build/provision/Certificates/ca
        sudo chmod -R 755 ../../build/provision/Certificates/root
    ```
    Note : This step is required everytime provisioning is done.
    Caution: This step will make the certs insecure. Please do not do it on a production machine.

5. Run the below command to start the Video Profiler.

    ```sh
        python3.6 video_profiler.py
    ```

6. The runtime stats of Video Profiler if enabled with export_to_csv switch can be found at [video_profiler_runtime_stats](video_profiler_runtime_stats.csv)

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
