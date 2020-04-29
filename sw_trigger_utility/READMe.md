# `SOFTWARE TRIGGER UTILITY for VideoIngestion Module`

This utility is used for triggering software triggers i.e. START INGESTION & STOP_INGESTION to the Video Ingestion module if EIS. 

## ` Usage of Software Trigger Utility: `   
Software trigger utility can be used in following ways to invoke various functionalities of the software trigger feature of VI.

USAGE 1:
```sh
# "START INGESTION" -> "ALLOW INGESTION FOR DEFAULT TIME (120 seconds being default)" -> "STOP INGESTION"
    $ ./sw_trigger_utility 

    # Here, the num_of_cycles is configurable through config.json file.
```

USAGE 2:
```sh
# Same as above scenario, but the time of ingestion is configurable using an 
# optional argument "TIME" of type unsigned int to represent time in seconds.
# " FLOW: START INGESTION" -> "ALLOW INGESTION FOR DURATION = "TIME" -> "STOP INGESTION""

    $ ./sw_trigger_utility 300

    # Example, here 300 is time for which ingestion happens. Here, VideoIngestion starts then does ingestion for 300 seconds then stops ingestion after 300 seconds & cycle repeqats for numberof cycles configured in the config.json.
```

USAGE 3:
```sh
# Here we can selectively send START_INGESTION software trigger:
    **EXAMPLE**: $ ./sw_trigger_utility START_INGESTION

```

USAGE 4:
```sh
# Here we can selectively send STOP_INGESTION software trigger:
    **EXAMPLE**: $ ./sw_trigger_utility STOP_INGESTION

```

> **Note**:  If duplicate START_INGESTION or   
  STOP_INGESTION sw_triggers are sent by client by mistake then the VI is capable  of catching these duplicates & responds back to client conveying that duplicate triggers were sent & requets to send proper sw_triggers. 

## Build steps for sw_trigger_utility:

```sh
# Move to the repo containing sw_trigger_utility
$ cd <multi_repo>/IEdgeInsights/tools/sw_trigger_utility

# Delete build directory (if already exists)
$ sudo rm -rf build

# Create build directory
$ mkdir build

# Run CMake command to generate make files to build the target
$ cd build
$ cmake ..

# Build the sw trigger utility binary
$ make

# This generates the "sw_trigger_vi"  binary.

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
```sh
# 1. Provision in prod mode by making dev_mode flag = false in "build.env"
$ cd  <EIS-working-directory>/IEdgeInsights/build/provision
$ sudo ./provision_eis.sh ../docker-compose.yml

# 2. needs to give explicitly provide permission to the necessary certs as follows
$sudo chmod -R 755 <EIS-working-directory>/IEdgeInsights/build/provision/Certificates/ca
$sudo chmod -R 755 <EIS-working-directory>/IEdgeInsights/build/provision/Certificates/root

# 3. Make the field "dev_mode= false" in config.json of tools/sw_trigger_utility. 
```