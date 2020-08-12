# EIS  GigEConfig


The GigEConfig tool is used for integrating the camera properties into the gstreamer pipeline by printing the required pipeline or by updating the config manager storage

## Generating PFS file

In order to execute this tool user has to genrate pfs file by following below steps:-

1. If basler camera's essentials are not present in your repo, Then go to following link to install it:-
    https://docs.baslerweb.com/overview-of-the-pylon-viewer
    
2. After that go to pylon5/bin/

3. Run PylonViewerApp like below:

    ```sh
    $ sudo ./PylonViewerApp
    ```

4. Configure the camera , Then on toolbar select Camera -> Save Features..

## Running GiGeConfig Tool

**Note**:
Before executing the tool make sure following steps are executed:- 
1. Source build/.env to get all the required ENVs

    ```sh
    $ set -a
    $ source build/.env
    $ set +a
    ```
2. Install the dependencies:
    
    ```sh
    $ pip install -r requirements.txt file
    ```   

## Input for GigEConfig

Command usage:
```sh
$python3 GigEConfig --help
```
....

usage: GigEConfig.py [-h] --pfs_file PFS_FILE [--etcd] [--ca_cert CA_CERT]
                     [--root_key ROOT_KEY] [--root_cert ROOT_CERT]
                     [--app_name APP_NAME]

Tool for updating pipeline according to user requirement

optional arguments:

  -h, --help            show this help message and exit

  --pfs_file PFS_FILE, -f PFS_FILE
                        To process pfs file genrated by PylonViwerApp (default: None)

  --etcd, -e            Set for updating etcd config (default: False)

  --ca_cert CA_CERT, -c CA_CERT
                        Provide path of ca_certificate.pem (default: None)

  --root_key ROOT_KEY, -r_k ROOT_KEY
                        Provide path of root_client_key.pem (default: None)

  --root_cert ROOT_CERT, -r_c ROOT_CERT
                        Provide path of root_client_certificate.pem (default: None)

  --app_name APP_NAME, -a APP_NAME
                        For providing appname of VideoIngestion instance (default: VideoIngestion)

Following is the config file of the tool :-

[config.json](config.json)   

The config.json consist of mapping between the PFS file elements and the camera properties.The pipeline will only consist of the elements specified in config.json.

The user is needed to provide following in config.json:-

pipeline_constant:Specify the constant gstreamer element of pipeline.

plugin_properties:Properties to be integrated in pipeline, The keys in here are mapped to respective gstreamer properties

**NOTE** : user is needed to hardcode serial parameter in config.json's plugin_properties section.

## Execution of GigEConfig

The tool can be executed in following manner :-

1. cd [WORKDIR]/IEdgeInsights/tools/GigEConfig 

2. config.json can be modified based on the requirements

3. To run the script :-

3.1. For DEV Mode

 a. In case etcd configuration needs to be updated.

    python3 GigEConfig.py --pfs_file <path to pylon's pfs file> --etcd 1 

 b. In case only pipeline needs to be printed.

    python3 GigEConfig.py --pfs_file <path to pylon's pfs file>

3.2. For PROD Mode

 a. In case etcd configuration needs to be updated.

    python3 GigEConfig.py -f <path to pylon's pfs file> -c <path>/ca_certificate.pem -r_k <path>/root/root_client_key.pem -r_c <path>/root/root_client_certificate.pem -e

 b. In case only pipeline needs to be printed.

    python3 GigEConfig.py -f <path to pylon's pfs file> -c <path>/ca_certificate.pem -r_k <path>/root/root_client_key.pem -r_c <path>/root/root_client_certificate.pem 

