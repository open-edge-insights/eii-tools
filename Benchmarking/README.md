# Benchmarking EIS

For best benchmarking results VideoIngestion Service with GVA(Gstreamer Video Analytics) Plugins will the used.

The Following are the steps required for benchmarking:

1. Start RTSP server using cvlc server using the below command on the host m/c.

    ```
    cvlc -vvv file:///[repo]/VideoIngestion/test_videos/Safety_Full_Hat_and_Vest.mp4 --sout '#gather:rtp{sdp=rtsp://localhost:8554/}' --loop --sout-keep
    ```
2. [Optional] Start the HDDL Dameon on host m/c following the steps given in `Using video accelerators` section in
 [../../README.md](../../README.md)

3. EIS needs to be built as a prerequesite following [../../README.md](../../README.md)

4. Replace the docker-compose.yml file in [repo]/build and etcd_pre_load.json file in [repo]/build/provision/config with the sample files added in the current directory.

**Note**:
* `WITH_PROFILE` build argument is set to `ON` in [../../build/docker-compose.yml](../../build/docker-compose.yml) to enable the profiling mode  with the gstreamer ingestor.
* The `PROFILING_MODE` environment variable mentioned in [../../build/.env](../../build/.env) file is for a different purpose and should not be used along with the `WITH_PROFILE` build argument in the docker compose file as it will affect the benchmarking performance.

5. Provision EIS by running the below script from [repo]/build/provision

    ```sh
    $ sudo ./provision_eis.sh ../docker-compose.yml
    ```

6. Execute the following script in [repo]/build to launch multuiple VI containers in detached mode

    ```sh
    $ docker-compose build
    $ docker-compose up -d
    ```

* This will start multiple VI containers based on the number of VI services given in docker compose file.
* Once the VI services are launched the the timer will be started before the gstreamer loop starts.
* In order to get the FPS results stop the RTSP server started using cvlc command.
* When the VI applicaiton stops receiving data form the RTSP server, the gstreamer loop will stop and FPS will be calculated.
* The FPS of each VI service along with it's AppName will be written to `/var/tmp/fps.txt`.
* One can also check the log of each VI service to get the FPS.

* `docker ps` command can be used to check the number of VI services launced.
* `docker-compose logs -f` can be used to check the logs.

**NOTE**: In our Lab Test we have seen arround 522 FPS with vehicle-license-plate-detection-barrier-0106 FP16 model on a system
with the following configuration:

* Intel(R) Core(TM) i7-8700 CPU @ 3.20GHz
* 16GB RAM
* GT2 Graphics
* 2 Mustang-V100 HDDL card (8VPU)*

**NOTE**: Refer the following link to download openvino models:
https://docs.openvinotoolkit.org/latest/_tools_downloader_README.html

The downloaded model needs to be moved to [repo]/VideoIngestion/models and VI services needs to be built to volume mount the xml and bin files
of the models using `docker-compose build`.