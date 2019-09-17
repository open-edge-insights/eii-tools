README FOR DISCOVER HISTORY TOOL

# CONTENTS #

1. CONFIG FILES
2. PYTHON FILES
3. PROCEDURE TO RUN DISCOVERY TOOL


# CONFIG FILES #

1. [eis_config.json](config/eis_config.json)

    Details of "imagestore_service" and "influxconnector_service" have been configured here.

2. [query_config.json](config/query_config.json)
  
    Details of Output Directory and User Query are provided here.

    NOTE: The user can provide any select query of choice.


# PROCEDURE TO RUN DISCOVERY TOOL (DEFAULT: PROD MODE) #

 1. Open "query_config.json"
 2. Provide the required query to be passed on to InfluxDB.
 3. Open [.env](DiscoverHistory/.env)
 4. Set the output directory variable at "SAVE_PATH".
 5. Check imagestore and influxdbconnector services are running.
 6. Use "docker-compose build" to build tool image.
 7. Use "docker-compose up" to run the tool.
 8. In the provided "SAVE_PATH", you will find data & frames directory.
    (Note: if img_handle is part of select statement , then only frames
    directory will be created)
 9. If the user changes the query in "query_config.json" then no need to run build command, just execute the up command.

 ## ADDITIONAL STEP TO RUN DISCOVERY TOOL IN DEV MODE
 1. Open [.env](DiscoverHistory/.env)
 2. Set the DEV_MODE variable as "true".
 ```
    DEV_MODE=false
 ```
to
 ```
    DEV_MODE=true
 ```
3. Comment the following lines in the [docker-compose.yml](DiscoverHistory/docker-compose.yml)
```
    secrets:
      - ca_etcd
      - etcd_root_cert
      - etcd_root_key

```
to
```
#    secrets:
#      - ca_etcd
#      - etcd_root_cert
#      - etcd_root_key

```
### NOTE:Building the base images like ia_common, ia_eisbase are must in cases if this tool isn't run on the same node where EIS is running.
### Please ensure that the base images i.e. ia_common and ia_eisbase are present on the node where this tool is run.

# List of sample select queries #

1. "select * from camera1_stream_results order by desc limit 10"
   This query will return latest 10 records.

2. "select height,img_handle from camera1_stream_results order by desc limit 10"

3. "select * from camera1_stream_results where time>='2019-08-30T07:25:39Z' AND time<='2019-08-30T07:29:00Z'"
    This query will return all the records between the given time frame i.e. (time>='2019-08-30T07:25:39Z' AND time<='2019-08-30T07:29:00Z')

4. "select * from camera1_stream_results where time>=now()-1h"
    This query will return all the records from the current time, going back upto last 1 hour.

NOTE: If you want good and bad frames then the query must contain the following parameters:
	
	*img_handle
	*defects
	*encoding_level
	*encoding_type
	*height
	*width
	*channel

    Example: 
     "select img_handle, defects, encoding_level, encoding_type,  height, width, channel from camera1_stream_results order by desc limit 10"

     or

     "select * from camera1_stream_results order by desc limit 10"



