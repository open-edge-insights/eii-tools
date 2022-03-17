# Copyright (c) 2022 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""
Sample MQTT publisher to publisher sample temperature, humidity data etc.
"""

import json
import time
import random
import argparse
import re
import sys
import os
import glob
import pandas as pd
import paho.mqtt.client as mqtt
from multiprocessing import Process
from influxdb import InfluxDBClient

# MQTT topic string
TOPIC_TEMP = 'temperature/simulated/0'
TOPIC_PRES = 'pressure/simulated/0'
TOPIC_HUMD = 'humidity/simulated/0'

# INFLUXDB Credentials
INFLUXDB_USERNAME = os.getenv("INFLUXDB_USERNAME")
INFLUXDB_PASSWORD = os.getenv("INFLUXDB_PASSWORD")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
MEASUREMENT_NAME = "ts_data"

SERVICE = 'mqtt'
SAMPLING_RATE = 10  # 500.0 # 2msecdd
SUBSAMPLE = 1  # 1:every row, 500: every 500 rows (ie. every 1 sec)
POINTSPERPROCESS = 350
HOST = 'localhost'
PROCS = []
DATA_PUBLISH_WAIT_PERIOD = 10


def g_tick(period=1):
    """generate the tick
    """
    start_time = time.time()
    period_count = 0
    while True:
        period_count += 1
        yield max(start_time + period_count * period - time.time(), 0)


def parse_args():
    """Parse command line arguments.
    """
    a_p = argparse.ArgumentParser()
    a_p.add_argument('--host', default='localhost', help='MQTT broker host')
    a_p.add_argument('--port', default=1883, type=int,
                     help='MQTT broker port')
    a_p.add_argument('--qos', default=1, type=int, help='MQTT publish qos')
    a_p.add_argument('--interval', default=1, type=float,
                     help='MQTT publication interval')
    a_p.add_argument('--csv', default=None, type=str,
                     help='CSV file to publish to MQTT broker')
    a_p.add_argument('--json', default=None, type=str,
                     help='folder containing json file(s) to publish'
                     'to MQTT broker')
    a_p.add_argument('--temperature', default=None, type=str,
                     help='Random data generation range for temperature')
    a_p.add_argument('--pressure', default=None, type=str,
                     help='Random data generation range for pressure')
    a_p.add_argument('--humidity', default=None, type=str,
                     help='Random data generation range for humidity')
    a_p.add_argument('--topic', default=TOPIC_TEMP, type=str,
                     help='topic for csv, JSON file publish')
    a_p.add_argument('--topic_temp', default=TOPIC_TEMP, type=str,
                     help='topic for temperature data')
    a_p.add_argument('--topic_pres', default=TOPIC_PRES, type=str,
                     help='topic for temperature data')
    a_p.add_argument('--topic_humd', default=TOPIC_HUMD, type=str,
                     help='topic for temperature data')
    a_p.add_argument('--subsample', default=SUBSAMPLE, type=float)
    a_p.add_argument('--sampling_rate', default=SAMPLING_RATE, type=float,
                     help='Data Sampling Rate')
    a_p.add_argument('--streams', default=1, type=int,
                     help='Number of MQTT streams to send.'
                     'This should correspond to the number of brokers running')
    a_p.add_argument('--output', default=None, type=str,
                     help='Output file path')
    a_p.add_argument('--service', default=SERVICE, type=str,
                     help='service tool for publish data')
    return a_p.parse_args()


def stream_csv(mqttc, topic, subsample, sampling_rate, filename):
    """
    Stream the csv file
    """
    target_start_time = time.time()
    row_count = 0
    row_served = 0
    jencoder = json.JSONEncoder()

    print("\nMQTT Topic - {}\nSubsample - {}\n \
          Sampling Rate - {}\nFilename - {}\n".format(topic,
                                                      subsample,
                                                      sampling_rate,
                                                      filename))

    with open(filename, 'r') as fileobject:
        tick = g_tick(float(subsample) / float(sampling_rate))

        for row in fileobject:

            row = [x for x in row.split(',') if x not in (' \n', ' \r\n')]
            if re.match(r'^-?\d+', row[0]) is None:
                continue

            row_count += 1
            if (subsample > 1) and (row_count % subsample) != 1:
                continue
            row_served += 1

            values = [float(x) for x in row]
            msg = jencoder.encode({'data': values})
            mqttc.publish(topic, msg)

            time.sleep(next(tick))
            if (row_served % (int(sampling_rate) / subsample)) == 0:
                print('{} rows served in {}'.format(
                    row_served, time.time() - target_start_time))

    print('{} Done! {} rows served in {}'.format(
        filename, row_served, time.time() - target_start_time))


def send_json_cb(instance_id, host, port, topic, data, qos, service):
    """ Send JSON
    """
    if service == "benchmarking":
        client = mqtt.Client(str(port))
    else:
        client = mqtt.Client(str(instance_id))
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.connect(host, port, 60)
    client.loop_start()
    if service == "benchmarking":
        for i in range(0, POINTSPERPROCESS):
            t_s = time.time()
            for value in data:
                msg = {'ts': t_s, 'value': value}
                client.publish(topic, json.dumps(msg), qos=qos)
                time.sleep(instance_id)
    else:
        try:
            while True:
                t_s = time.time()
                for value in data:
                    msg = {'ts': t_s, 'value': value}
                    client.publish(topic, json.dumps(msg), qos=qos)
                    time.sleep(1)
        except KeyboardInterrupt:
            client.loop_stop()


def publish_json(mqttc, topic, path, qos, argsinterval, streams, host, port, output_file, service):
    """ Publish the JSON file
    """
    data = []
    path = path.replace("\\*", "*")
    files = glob.glob(path)
    for file in files:
        with open(file) as fpd:
            data.append(fpd.read())
    print("Publishing json files to mqtt in loop")
    if service == "benchmarking":
        intial_count_value = calculate_data_value(host)
        print("Path :", path, " files: ", files)
        totalpoints = streams * POINTSPERPROCESS * len(data)
        processes = []
        print("streams: ", streams, "topic: ", topic, " pointsperprocess: ", POINTSPERPROCESS, " length of data: ",
              len(data))
        try:
            for i in range(0, streams):
                port = port + i
                processes.append(Process(target=send_json_cb, args=(argsinterval, host, port, topic, data, qos, service)))
                processes[i].start()
            for process in processes:
                process.join()
            print("Success: ", totalpoints, " points sent!")
            time.sleep(DATA_PUBLISH_WAIT_PERIOD)
            # Calculate the data loss between published data and received data in influxdb
            final_count_value = calculate_data_value(host)
            count_value = final_count_value - intial_count_value
            if count_value != totalpoints:
                data_new = pd.read_csv(output_file)
                data_new['Data_Loss'] = str(count_value)
                data_new.to_csv(output_file, index=False)
        except Exception as e:
            print("Exception occured while publishing the points")
    else:
        if streams == 1:
            while True:
                t_s = time.time()
                for value in data:
                    msg = {'ts': t_s, 'value': value}
                    mqttc.publish(topic, json.dumps(msg), qos=qos)
                    msg.clear()
                    time.sleep(1)
        else:
            for i in range(0, streams):
                PROCS.append(Process(target=send_json_cb, args=(i, host, port,
                                                            topic, data, qos, service)))
                PROCS[i].start()


def update_topic(args_dict, topics, topic_data):
    """
    Update topics with different kind of data
    """
    updated_topics = {}
    topic_dict = {key: value for key, value in topics.items()
                  if args_dict[topic_data[key]] is not None}
    for key, value in topic_dict.items():
        if value in updated_topics:
            updated_topics[value].append(key)
        else:
            updated_topics[value] = [key]
    return updated_topics


def calculate_data_value(host):
    """
    Calculate the measurement count value
    """
    try:
        count_value = 0
        print("Fetching data count value from InfluxDB")
        client = InfluxDBClient(host=host, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD, ssl=True, verify_ssl=False)
        client.switch_database('datain')
        results = client.query('SELECT count(*) FROM {}'.format(MEASUREMENT_NAME))
        point = results.get_points()
        for item in point:
            count_value = item['count_ts']
        return count_value
    except:
        # measurement not created
        count_value = 0
        return count_value


def on_disconnect(client, userdata, rc):
    print("MQTT disconnected:\nclient: ", client, "\n userdata: ", userdata,
          "\n rc: ", rc)


def on_connect(client, userdata, flags, rc):
    print("MQTT Connected:\nclient: ", client, "\n userdata: ", userdata,
          "\n rc: ", rc)


def main():
    """Main method
    """
    args = parse_args()
    args.host = os.getenv('HOST_IP', 'localhost')
    args_dict = vars(args)
    updated_topics = {}
    topic_data = {'topic_temp': 'temperature', 'topic_pres': 'pressure',
                  'topic_humd': 'humidity'}
    topics = {'topic_temp': args.topic_temp, 'topic_pres': args.topic_pres,
              'topic_humd': args.topic_humd}
    updated_topics = update_topic(args_dict, topics, topic_data)
    client = None
    if int(args.streams) == 1:
        client = mqtt.Client()
        client.connect(args.host, args.port, 60)
        client.loop_start()

    try:
        if args.csv is not None:
            stream_csv(client,
                       args.topic,
                       args.subsample,
                       args.sampling_rate,
                       args.csv)
        elif args.json is not None:
            publish_json(client,
                         args.topic,
                         args.json,
                         args.qos,
                         args.interval,
                         args.streams,
                         args.host,
                         args.port,
                         args.output,
                         args.service)

        else:
            if not updated_topics:
                sys.exit("Arguments are missing")

            while True:
                t_s = time.time()
                for topic, value in updated_topics.items():
                    msg = {'ts': t_s}
                    print('-- Publishing message', t_s)
                    for d_topic in value:
                        msg.update({topic_data[d_topic]: random.uniform(
                            int(args_dict[topic_data[d_topic]].split(':')[0]),
                            int(args_dict[topic_data[d_topic]].split(':')[
                                1]))})
                    client.publish(topic, json.dumps(msg), qos=args.qos)
                    msg.clear()
                if args.interval > 1000:
                    args.interval = 1000
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print('-- Quitting')
        if args.streams == 1:
            client.loop_stop()
        else:
            for i in range(0, args.streams):
                PROCS[i].close()
                client[i].loop_stop()

if __name__ == '__main__':
    main()
