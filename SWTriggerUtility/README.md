# Software Trigger Utility for VideoIngestion Module

This utility is used for invoking various software trigger features of VideoIngestion. The currently supported triggers to VideoIngestion module are:
1. START INGESTION - to start the ingestor
2. STOP_INGESTION -  to stop the ingestor
3. SNAPSHOT - to get frame snapshot which feeds one only frame into the video data pipeline.

## Installing Software Trigger Utility requirements

1. To install EIS libs on bare-metal, follow the [README](../../common/README.md) of eis_libs_installer.

## Software Trigger Utilily pre-requisites

SWTriggerUtility expects a set of config, interfaces & public private keys to be present in ETCD as a pre-requisite.
* To achieve this, please ensure an entry for SWTriggerUtility with its relative path from [IEdgeInsights](../../) directory is set in any of the .yml files present in [build](../../build) directory. An example has been provided in [video-streaming.yml](../../build/video-streaming.yml) and can be run using the below command
    ```yml
        AppName:
        ---snip---
        - tools/SWTriggerUtility
    ```
    ```sh
        $ python3 eis_builder.py -f ./video-streaming.yml
    ```
* Run the below steps to load the data to ETCD

    ```sh
        $ cd  <EIS-working-directory>/IEdgeInsights/build/provision
        $ sudo ./provision_eis.sh ../docker-compose.yml
    ```
* Run the below step to set the required env variables to communicate with ETCD

  ```sh
      $ source ./env.sh
  ```

* Since provisioning will stop the EIS services run the below command to start them

   ```sh
       $ cd <EIS-working-directory>/IEdgeInsights/build/
       $ docker-compose up -d
   ```

## Usage of Software Trigger Utility:

Software trigger utility can be used in following ways:

**NOTE**: Passing config file as a command line argument is optional.

USAGE 1: "START INGESTION" -> "ALLOW INGESTION FOR DEFAULT TIME (120 seconds being default)" -> "STOP INGESTION"
```sh
    "./sw_trigger_utility" or "./sw_trigger_utility ../config/config.json"
```
Note: The num_of_cycles is configurable through config.json file.

USAGE 2: "START INGESTION" -> "ALLOW INGESTION FOR USER DEFINED TIME (configurable time in seconds)" -> "STOP INGESTION"
```sh
    "./sw_trigger_utility 300" or "./sw_trigger_utility 300 ../config/config.json"
```
Note: In the above example, VideoIngestion starts then does ingestion for 300 seconds then stops ingestion after 300 seconds & cycle repeqats for number of cycles configured in the config.json.


USAGE 3: Selectively send START_INGESTION software trigger:
```sh
    "./sw_trigger_utility START_INGESTION" or "./sw_trigger_utility START_INGESTION ../config/config.json"

```

USAGE 4: Selectively send STOP_INGESTION software trigger:
```sh
    "./sw_trigger_utility STOP_INGESTION" or "./sw_trigger_utility STOP_INGESTION ../config/config.json"

```

USAGE 5: Selectively send SNAPSHOT software trigger:
```sh
    "./sw_trigger_utility SNAPSHOT" or "./sw_trigger_utility SNAPSHOT ../config/config.json"

```

> **Note**:  

* If duplicate START_INGESTION or STOP_INGESTION sw_triggers are sent by client by mistake then the VI is capable  of catching these duplicates & responds back to client conveying that duplicate triggers were sent & requets to send proper sw_triggers. 

* In order to send SNAPSHOT trigger, ensure that the ingestion is stopped. In case START_INGESTION trigger is sent previously then stop the ingestion using the STOP_INGESTION trigger.

## Configuration file:

**config.json** is the configuration file used for sw_trigger_vi utility.

|       Field      | Meaning |                                       Type of the value                                    |
| :-------------:  | :-----: | ------------------------------------------------------------------------------------ |
| `num_of_cycles`  | `Number of cyles of start-stop ingestions to repeat`   | `integer`                           |
| `dev_mode`       | `dev mode ON or OFF`   | `boolean (true or false)`  |
| `log_level`      | `Log level to view the logs accordingly`   |  `integer [DEBUG=3 (default), ERROR=0, WARN=1, INFO=2]`  |

**Note**: In case one needs to change the values in [config.json](./config.json) then provisioning needs to be done or one can choose to update the ETCD UI to change the values and then restart the application.

## Build steps for sw_trigger_utility:

Install the required EIS baremetal libraries by referring [EISLibsInstaller_README.md](../../common/README.md)

### To generate the "sw_trigger_vi"  binary.

```sh
   cd <multi_repo>/IEdgeInsights/tools/SWTriggerUtility && \
   sudo rm -rf build && \
   mkdir build && \
   cd build && \
   cmake .. && \
   make
```

**This utility works in both dev & prod mode.**  As a pre-requisite make sure to turn ON the flag corresponding to "dev_mode" to true/false in the config.json file.

### Prod mode support :

# 1. Provision in prod mode by making dev_mode flag = false in "build.env"

```sh
    cd  <EIS-working-directory>/IEdgeInsights/build/provision
    sudo ./provision_eis.sh ../docker-compose.yml
```

# 2. needs to give explicitly provide permission to the necessary certs as follows

```sh
    sudo chmod -R 755 <EIS-working-directory>/IEdgeInsights/build/provision/Certificates/ca
    sudo chmod -R 755 <EIS-working-directory>/IEdgeInsights/build/provision/Certificates/SWTriggerUtility
```

# 3. Make the field "dev_mode= false" in config.json of tools/sw_trigger_utility.

