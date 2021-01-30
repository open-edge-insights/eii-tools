# EmbSubscriber

EmbSubscriber subscribes message coming from a publisher.It subscribes to messagebus topic to get the data.
    
## EIS pre-requisites
1.  EmbSubscriber expects a set of config, interfaces & public private keys to be present in ETCD as a pre-requisite.
    To achieve this, please ensure an entry for EmbSubscriber with its relative path from [IEdgeInsights](../../) directory is set in the time-series.yml file present in [build](../../build) directory. An example has been provided below:
    ```sh
        AppName:
        - Grafana
        - InfluxDBConnector
        - Kapacitor
        - Telegraf
        - tools/EmbSubscriber
    ```

2. With the above pre-requisite done, please run the below command:
    ```sh
        python3 eis_builder.py -f ./time-series.yml
    ```

## Running EmbSubscriber

1. Refer [provision/README.md](../../README.md) to provision, build and run the tool along with the EIS time-series recipe/stack.
