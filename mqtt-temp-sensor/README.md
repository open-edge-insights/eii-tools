# MQTT Temperature Sensor
Simple Python temperature sensor simulator.

## Usage
> **NOTE:** This assumes you have already installed and configured Docker.

1. Build the docker container
    ```sh
    $ ./build.sh
    ```
2. Run the broker
    ```sh
    $ ./broker.sh
    ```
3. Run the publisher (different terminal window)
    ```sh
    $ ./publisher.sh
    ```
   If you want to publish data from csv row by row, then run the below mentioned script
    ```sh
    $ ./publisher_csv.sh
    ```
   You can also change filename, topic, sampling rate and subsample parameters in the publisher_csv.sh script.

If you wish to see the messages going over MQTT, run the subscriber with the
following command:

```sh
$ ./subscriber.sh
```
