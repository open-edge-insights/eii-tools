# Intel Edge Insights Simple Visualizer
Simple visualizer for the IEI platform.

Pre-requisite for this visualizer is to have IEI installed on the target
machine and the `dist_libs` installed in `/opt/intel/iei` directory. The
`setup_iei.py` will automatically create the `dist_libs`. If IEI is run using
sudo make build run, then the dist_libs can be created using the below
command:

```sh
cd IEdgeInsights/docker_setup
sudo make distlibs
```

## Installation

### 1. Running natively (Works only on Ubuntu 18.04. Run as container on other OS)

#### Steps to install and run

* Please have python3.6 and pip3 installed on the system.

* Installing dependencies

  To install all of the necessary requirements, execute the following script:

  ```sh
  $ ./install.sh
  ```

* Running `visualize.py`

  Before running the visualizer, you need to source the `source.sh` script to
  configure the environmental veriables correctly. To do this, simply execute
  the following command in the terminal window you plan to run the visualizer
  from.

  ```sh
  $ source ./source.sh
  ```

  If you have a proxy configured on your system you need to add your IP address
  to the `no_proxy` environmental variable (shown below).

  ```sh
  export no_proxy=$no_proxy,<IP ADDRESS>
  ```

  Run the visualizer as follows:

  1. In production mode (default mode):

    ```sh
    python3.6 visualize.py -c IEdgeInsights/cert-tool/Certificates -host <IP_ADDRESS> -d <true/false> -i <image_dir>
    ```

  2. In developer mode:

    ```sh
    python3.6 visualize.py -host <IP_ADDRESS> -d <true/false> -i <image_dir> -D true
    ```

#### Using Labels

In order to have the visualizer label each of the defects on the image (i.e.
text underneath of the bounding box), you will need to provide a JSON file with
the mapping between the classfication type and the text you wish to display.

An example of what this JSON file should look like is shown below. In this case
it is assumed that the classification types are `0` and `1` and the text labels
to be displayed are `MISSING` and `SHORT` respectively.

```json
{
    "0": "MISSING",
    "1": "SHORT"
}
```
> **NOTE:** These labels are the mapping for the PCB demo provided in IEI.

An important thing to note above, is that the keys need to still be strings.
The visualizer will take care of the conversion when it receives publications
for classification results.

Assuming you saved the above JSON file as `labels.json`, run the visualizer
as follows:

```sh
python3.6 visualize.py -c IEdgeInsights/cert-tool/Certificates  -host <IP_ADDRESS> --labels labels.json -d <true/false> -i ./test
```

#### Command Line Arguments
Use the below command to know the usage of the script `visualize.py`.

```
   python3.6 visualize.py --help
```

### 2. Running as a docker container

#### Steps to build and run

* Building the image (it has to be done everytime the source code changes)

  ```sh
  $ sudo make build
  ```

* Running the container

  > **NOTE**:
  > 1. The `IMAGE_DIR` argument here will override the value set in the [Makefile]
  >    (./Makefile). If no `IMAGE_DIR` value is provided, the value set in the [Makefile]
  >    (./Makefile) will be used
  >    `IMAGE_DIR` in container mode should be present before passing it to the container as an argument.
  >  2. Change `SECURE_VISUALIZE_ARGS` or `NON_SECURE_VISUALIZE_ARGS` as needed in [Makefile](./Makefile).
  >  3. Change `PROFILING` to True in [Makefile](./Makefile) in case if you want to enable profiling.
  >    Refer `Command Line Arguments` section under in this file to know the supported args for
  >    visualizer app
  >  4. The `DISPLAY_IMG` argument here will override the value set in the [Makefile]
  >    (./Makefile). If no `DISPLAY_IMG` value is provided, the value is set to "true"

  By default production mode will be enabled, hence IEI must run in secured mode for visualize app to work.
  Below command will make the APP run in secured mode.

  ```sh
  $ sudo make run CERT_PATH=<absolute_path_to_the_certificates_dir> HOST=<system_ip_address> IMAGE_DIR=<absolute_directory_path_to_save_images> DISPLAY_IMG=true/false
  ```

* For running the APP in non secured mode, Kindly follow the below mentioned steps:

  1. Open the Makefile present in current directory and replace $(SECURE_VISUALIZE_ARGS) to $(NON_SECURE_VISUALIZE_ARGS) for "docker run" commandline. Below code snippet explains how it should look after enabling Developement mode.

    ```sh
    -it ia/visualizer:1.0 \
      $(SECURE_VISUALIZE_ARGS)
    ```

    TO

    ```sh
    -it ia/visualizer:1.0 \
    $(NON_SECURE_VISUALIZE_ARGS)
    ```

  2. Following this file modifcation execute the below command to make the container up in development mode.

    ```sh
    $ sudo make run  HOST=<system_ip_address> IMAGE_DIR=<absolute_directory_path_to_save_images>
    ```

* If one needs to remove the classified images on a periodic basis:

  1. Have this command running in a separate terminal as a cleanup task to remove images older than 60 mins in IMAGE_DIR. Replace <path-to-IMAGE_DIR> with IMAGE_DIR path given while running visualizer. The -mmin option can be changed accordingly by the user.

    ```sh
    $ while true; do find <path-to-IMAGE_DIR> -mmin +60 -type f -name "*.png" -exec rm -f {} \;;  done
    ```