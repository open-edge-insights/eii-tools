# Intel Edge Insights Simple Visualizer
Simple visualizer for the IEI platform.

## Installation

### 1. Running natively (Works only on Ubuntu 18.04. Run as container on other OS)

#### Steps to install and run

* Please have python3.6 and pip3 installed on the system.

* Installing dependencies

  To install all of the necessary requirements, execute the following script:

  ```sh
  $ ./install.sh
  ```

* Have etcd installed and running as a service:

  To install etcd:

  ```sh
  $ sudo apt-get install etcd
  ```

  To run etcd:

  ```sh
  $ sudo service etcd start
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

  Have the Visualizer config put to etcd before running visualizer. Refer this
  file [Etcd/README.md](../../Etcd/README.md)
    
  Run the visualizer as follows:

    ```sh
    python3.6 visualize.py --img_dir <path-to-IMAGE_DIR>
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
python3.6 visualize.py --labels labels.json -i ./test -d <true/false> -i <image_dir> -D <true/false>
```

#### Command Line Arguments
Use the below command to know the usage of the script `visualize.py`.

```sh
  $ python3.6 visualize.py --help
```

### 2. Running as a docker container

#### Steps to build and run

* Visualizer can be run as a container along with other EIS containers from docker_setup folder using the following command:

  ```sh
  $ sudo make build run
  ```

  > **NOTE**:
  > 1. The admin has to make sure all the necessary config is set in etcd before starting the visualizer.
  > 2. Run this command in terminal if you run into tkinter couldn't connect to display exception
    
    ```sh
    $ xhost +
    ```

    > Note: The Visualizer will not work with time-series / point data if used with docker container approach.
    > For point data, use the bare-metal run to see the results printed in the terminal.

* If one needs to remove the classified images on a periodic basis:

  1. Have this command running in a separate terminal as a cleanup task to remove images older than 60 mins in IMAGE_DIR. Replace <path-to-IMAGE_DIR> with IMAGE_DIR path given while running visualizer. The -mmin option can be changed accordingly by the user.

    ```sh
    $ while true; do find <path-to-IMAGE_DIR> -mmin +60 -type f -name "*.png" -exec rm -f {} \;;  done
    ```