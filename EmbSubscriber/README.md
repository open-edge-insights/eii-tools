# Contents

- [Contents](#contents)
  - [EmbSubscriber](#embsubscriber)
    - [Prerequisites](#prerequisites)
    - [Running EmbSubscriber](#running-embsubscriber)
    - [Running EmbSubscriber in IPC mode](#running-embsubscriber-in-ipc-mode)

## EmbSubscriber

EmbSubscriber subscribes message coming from a publisher.It subscribes to messagebus topic to get the data.

>**Note:** In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

### Prerequisites

1. EmbSubscriber expects a set of config, interfaces & public private keys to be present in ETCD as a prerequisite.
    To achieve this, please ensure an entry for EmbSubscriber with its relative path from [IEdgeInsights](../../) directory is set in the time-series.yml file present in [build/usecases](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases) directory. An example has been provided below:

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
      cd [WORKDIR]/IEdgeInsights/build
      python3 builder.py -f usecases/time-series.yml
    ```

### Running EmbSubscriber

1. Refer [../README.md](https://github.com/open-edge-insights/eii-core/blob/master/README.md) to provision, build and run the tool along with the OEI time-series recipe/stack.

### Running EmbSubscriber in IPC mode

User needs to modify interface section of **[config.json](./config.json)** to run in IPC mode as following

```sh
{
  "config": {},
  "interfaces": {
    "Subscribers": [
      {
        "Name": "TestSub",
        "PublisherAppName": "Telegraf",
        "Type": "zmq_ipc",
        "EndPoint": {
                  "SocketDir": "/EII/sockets",
                  "SocketFile": "telegraf-out"
         },
        "Topics": [
          "*"
        ]
      }
    ]
  }
}
```
