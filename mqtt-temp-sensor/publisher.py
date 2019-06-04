"""Simple MQTT publisher which publishes randomized temperature sensor data.
"""
import json
import time
import random
import argparse
import paho.mqtt.client as mqtt


# MQTT topic string
TOPIC = 'temperature/simulated/0'


def parse_args():
    """Parse command line arguments.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost', help='MQTT broker host')
    ap.add_argument('--port', default=1883, type=int, help='MQTT broker port')
    ap.add_argument('--qos', default=1, type=int, help='MQTT publish qos')
    ap.add_argument('--interval', default=1, type=float,
                    help='MQTT publication interval')
    return ap.parse_args()


def main():
    """Main method
    """
    args = parse_args()
    client = mqtt.Client()
    client.connect(args.host, args.port, 60)
    client.loop_start()

    try:
        while True:
            ts = time.time()
            print('-- Publishing message', ts)
            msg = { 'ts': ts, 'temperature': random.uniform(10, 30) }
            client.publish(TOPIC, json.dumps(msg), qos=args.qos)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('-- Quitting')
        client.loop_stop()


if __name__ == '__main__':
    main()
