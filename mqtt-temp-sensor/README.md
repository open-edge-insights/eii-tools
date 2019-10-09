# MQTT Temperature Sensor
Simple Python temperature sensor simulator.

## Usage
> **NOTE:** This assumes you have already installed and configured Docker.

1. Run the broker (Use `docker ps` to see if the broker has started successfully as the container starts in detached mode)
    ```sh
    $ ./broker.sh
    ```
2. Build and run the MQTT publisher docker container
   * For EIS TimeSeries Analytics usecase
     ```sh
     $ ./build.sh && ./publisher.sh
     ```
   * For DiscoveryCreek usecase (publishes data from csv row by row)
     ```sh
     $ ./build.sh && ./publisher_csv.sh
     ```
     Once can also change filename, topic, sampling rate and subsample parameters in the publisher_csv.sh script.

3. If one wish to see the messages going over MQTT, run the
   subscriber with the following command:
   ```sh
   $ ./subscriber.sh
   ```
