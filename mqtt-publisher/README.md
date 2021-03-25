# MQTT Temperature Sensor
Simple Python temperature sensor simulator.

## Usage
> **NOTE:** This assumes you have already installed and configured Docker.

1. Run the broker (Use `docker ps` to see if the broker has started successfully as the container starts in detached mode)
    ```sh
    $ ./broker.sh <port>
    ```
    **NOTE:** To run the broker for EII TimeSeries Analytics usecase:
    ```sh
    $ ./broker.sh 1883
    ```

2. Build and run the MQTT publisher docker container
   * For EII TimeSeries Analytics usecase, 
    To publish temperature data to default topic:
     ```sh
     $./build.sh && ./publisher_temp.sh
     ```
    To start publisher docker container in detached mode:
     ```sh
     $./build.sh && ./publisher_temp.sh --detached_mode true
     ```

    To publish temperature and humidity data together:
     ```sh
     $./build.sh && ./publisher_temp_humidity.sh
     ```
    To start publisher docker container in detached mode:
     ```sh
     $./build.sh && ./publisher_temp_humidity.sh --detached_mode true
     ```

**Note**: To publish multiple sensor data(temperature, pressure, humidity) to default topic(temperature/simulated/0,pressure/simulated/0,humidity/simulated/0),using following command:
   ```sh
	$./build.sh && ./publisher.sh --temperature 10:30 --pressure 10:30 --humidity 10:30 
   ```
   To publish multiple sensor data in detached mode:
   ```sh
   $./build.sh && ./publisher.sh --temperature 10:30 --pressure 10:30 --humidity 10:30 --detached_mode true
   ```
   To publish differnt topic instead of default topic:
   ```sh
	./build.sh && ./publisher.sh --temperature 10:30 --pressure 10:30 --humidity 10:30 --topic_temp <temperature topic> --topic_pres <pressure topic> --topic_humd <humidity topic>
   ```

  It is possible to publish more than one sensor data into single topic, in that case, same topic name needs to be given for that sensor data.

   * For publishing data from csv row by row:
     $ ./build.sh && ./publisher_csv.sh
     ```
     To publish in deatched mode:
     ```sh
     $ ./build.sh && ./publisher_csv.sh --detached_mode true
     ```
     One can also change filename, topic, sampling rate and subsample parameters in the publisher_csv.sh script.

   * To publish JSON files (to test random forest UDF)
     ```sh
     $ ./build.sh && ./publisher_json.sh
     ```
     To publish JSON files (to test random forest UDF) in detached mode:
     ```sh
     $ ./build.sh && ./publisher_json.sh --detached_mode true
     ```
     One can also change filename, topic in the publisher_json.sh script.


3. If one wish to see the messages going over MQTT, run the
   subscriber with the following command:
   ```sh
   $ ./subscriber.sh <port>
   ```
   Example:
   If Broker runs at port 1883, to run subscriber use following command:

   ```sh
   $ ./subscriber.sh 1883
   ```

