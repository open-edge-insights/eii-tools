# Software Trigger Utility for VideoIngestion Module

This utility is used for invoking various software trigger features of VideoIngestion. The currently supported triggers to VideoIngestion module are:
1. START INGESTION - to start the ingestor
2. STOP_INGESTION -  to stop the ingestor

## Installing Software Trigger Utility requirements

1. To install EIS libs on bare-metal, follow the [README](../../common/README.md) of eis_libs_installer.

## Usage of Software Trigger Utility:

Software trigger utility can be used in following ways:

USAGE 1: "START INGESTION" -> "ALLOW INGESTION FOR DEFAULT TIME (120 seconds being default)" -> "STOP INGESTION"
```sh
    ./sw_trigger_utility 
```
Note: The num_of_cycles is configurable through config.json file.

USAGE 2: "START INGESTION" -> "ALLOW INGESTION FOR USER DEFINED TIME (configurable time in seconds)" -> "STOP INGESTION"
```sh
    ./sw_trigger_utility 300
```
Note: In the above example, VideoIngestion starts then does ingestion for 300 seconds then stops ingestion after 300 seconds & cycle repeqats for number of cycles configured in the config.json.


USAGE 3: Selectively send START_INGESTION software trigger:
```sh
    ./sw_trigger_utility START_INGESTION

```

USAGE 4: Selectively send STOP_INGESTION software trigger:
```sh
    ./sw_trigger_utility STOP_INGESTION

```

> **Note**:  If duplicate START_INGESTION or STOP_INGESTION sw_triggers are sent by client by mistake then the VI is capable  of catching these duplicates & responds back to client conveying that duplicate triggers were sent & requets to send proper sw_triggers. 

## Build steps for sw_trigger_utility:

Install the required EIS baremetal libraries by referring [../EISLibsInstaller/README.md/](../EISLibsInstaller/README.md)

### To generate the "sw_trigger_vi"  binary.

```sh
   cd <multi_repo>/IEdgeInsights/tools/SWTriggerUtility && \
   sudo rm -rf build && \
   mkdir build && \
   cd build && \
   cmake .. && \
   make
```

## Configuration file:

**config.json** is the configuration file used for sw_trigger_vi utility.



|       Field      | Meaning |                                       Type of the value                                    |
| :-------------: | :-----: | ------------------------------------------------------------------------------------ |
| `num_of_cycles`   | `Number of cyles of start-stop ingestions to repeat`   | `integer`                           |
| `server_client`       | `server/client configuration`   | `string` |
| `client`    | `name of the client`   | `string`         |
| `sw_trigger_utility_cfg` | `connection endpoint configuration`   | `string`    |
| `dev_mode`     | `dev mode ON or OFF`   | `boolean (true or false)`  |
| `app_name`     | `App name (to get the certificates in the list of VI's trusted clients)`   | `string`  |
| `certFile`     | `ETCD cert file`   | `string`  |
| `keyFile`     | `key file`   | `string`  |
| `trustFile`     | `CA cert`   | `string`  |
| `log_level`     | `Log level to view the logs accordingly`   |  `integer [DEBUG=3 (default), ERROR=0, WARN=1, INFO=2]`  |


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
    sudo chmod -R 755 <EIS-working-directory>/IEdgeInsights/build/provision/Certificates/root
```

# 3. Make the field "dev_mode= false" in config.json of tools/sw_trigger_utility.

