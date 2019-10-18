"""Simple MQTT publisher which publishes randomized temperature sensor data.
"""
import json
import time
import random
import argparse
import paho.mqtt.client as mqtt
import re

# MQTT topic string
TOPIC = 'temperature/simulated/0'

SAMPLING_RATE = 10  # 500.0 # 2msecdd
SUBSAMPLE = 1  # 1:every row, 500: every 500 rows (ie. every 1 sec)

HOST = 'localhost'
PORT = 1883

def g_tick(period=1):
        start_time = time.time()
        period_count = 0
        while True:
                period_count += 1
                yield max(start_time +
                                  period_count * period - time.time(), 0)


def parse_args():
    """Parse command line arguments.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost', help='MQTT broker host')
    ap.add_argument('--port', default=1883, type=int, help='MQTT broker port')
    ap.add_argument('--qos', default=1, type=int, help='MQTT publish qos')
    ap.add_argument('--interval', default=1, type=float,
                    help='MQTT publication interval')
    ap.add_argument('--csv', default=None, type=str, help='CSV file to publish to MQTT broker')
    ap.add_argument('--topic', default=TOPIC, type=str)
    ap.add_argument('--subsample', default=SUBSAMPLE, type=float)
    ap.add_argument('--sampling_rate', default=SAMPLING_RATE, type=float, help='Data Sampling Rate')
    return ap.parse_args()


def stream_csv(mqttc, topic, subsample, sampling_rate, filename):
    target_start_time = time.time()
    row_count = 0
    row_served = 0
    jencoder = json.JSONEncoder()

    print("\nMQTT Topic - {}\nSubsample - {}\nSampling Rate - {}\nFilename - {}\n".format(topic, subsample, sampling_rate, filename))

    with open(filename, 'r') as fileobject:
        tick = g_tick(float(subsample) / float(sampling_rate))

        for row in fileobject:

            row = [x for x in row.split(',') if x != ' \n' and x != ' \r\n']
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
                print('{} rows served in {}'.format(row_served, time.time() - target_start_time))

    print('{} Done! {} rows served in {}'.format(filename, row_served, time.time() - target_start_time))

def main():
    """Main method
    """
    args = parse_args()
    client = mqtt.Client()
    client.connect(args.host, args.port, 60)
    client.loop_start()

    try:
        if (args.csv is not None):
            stream_csv(client, args.topic, args.subsample, args.sampling_rate, args.csv)
        else:
            while True:
                ts = time.time()
                print('-- Publishing message', ts)
                msg = { 'ts': ts, 'temperature': random.uniform(10, 30) }
                client.publish(TOPIC, json.dumps(msg), qos=args.qos)
                if args.interval > 1000:
                    args.interval = 1000
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print('-- Quitting')
        client.loop_stop()

if __name__ == '__main__':
    main()
