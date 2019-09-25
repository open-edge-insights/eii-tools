# The sample config files can be referred to test for 500 FPS with a 600x600 frame.

1. [fps_multiple_vi_va_docker-compose.yml](./fps_multiple_vi_va_docker-compose.yml) file can be referred to launch multiple VI and VA containers. In        the sample docker-compose.yml file 25 VI and VA containers are launched using IPC mode.

2. [etcd_pre_load.json](./etcd_pre_load.json) file can be referred to change the config for different VI containers. In case multiple physical RTSP         cameras are used then update the `RTSP_CAMERA_IP` env variable with the IP addresses of all the RTSP cameras as comma separated values in [[repo]/docker_setup/.env](../../docker_setup/.env) with all the camera IPs.

3. [VA_config.json](./VA_config.json) file can be referred to use the FPS tool to subscribe to VA stream results. In case you want to subscribe to VI
    then refer [VI_config.json](./VI_config.json).

* [VideoIngestion/README.md](../../VideoIngestion/README.md) can be referred to launch RTSP cvlc based camera simulation.

* In order to run fps tool refer [FpsCalculator/README.md](../FpsCalculator/README.md).

* In order to use [fps_multiple_vi_va_docker-compose.yml] file the following command can be used from `[repo]/docker_setup` folder,

    * ` docker-compose -f docker-compose.yml -f ../tools/multiple_vi_va_sample_configs/fps_multiple_vi_va_docker-compose.yml build `

    * ` docker-compose -f docker-compose.yml -f ../tools/multiple_vi_va_sample_configs/fps_multiple_vi_va_docker-compose.yml up -d `
