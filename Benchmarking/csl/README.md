# Benchmarking EIS with CSL

For best benchmarking results VideoIngestion Service with GVA(Gstreamer Video Analytics) Plugins will the used.

The Following are the steps required for benchmarking:

## Pre-requisites
    
* Please follow the `Step 1` to `Step 5` of [Benchmarking Readme](../README.md)

## Steps run VideoIngestion containers in CSL Environment.
1. Register the `modulespec.json` as `videoingestion` module spec for benchmarking.
    ```sh
        $ ./csladm register artifact --type file --name videoingestion --version 2.3 --file ./modulespec.json
    ```
2. Set **whitelisted_mounts** property value as follows.
      ```sh    
      $   whitelisted_mounts=/dev,/var/tmp,/tmp/.X11-unix,/opt/intel/eis/data,/opt/intel/eis/saved_images,/opt/intel/eis/sockets
      ```
  > Save the file.
3. Restart CSL Manager container.

4. Deploy the Benchmarking appspec `csl_appspec.json` using CSL Manager.

5. Use `VideoProfiler` with CSL root certificates to get the FPS data. For More details please refer [VideoProfiler Readme](../../VideoProfiler/README.md)