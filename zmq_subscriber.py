# Copyright (c) 2019 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Simple VideoIngestion ZMQ Subscriber
"""

import zmq
import sys
import numpy as np
import time
import datetime
import threading
import argparse
import logging
import json
import cv2
import os

fmt_str = ('%(asctime)s : %(levelname)s : %(name)s : [%(filename)s] :' +
               '%(funcName)s : in line : [%(lineno)d] : %(message)s')

# Do basic configuration of logging (just for stdout config)
logging.basicConfig(format=fmt_str, level=logging.DEBUG)


def main(args):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(args.endpoint)
    start = time.time()
    frame_count = 0
    thread = threading.Thread(target=subscribe, args=(subscriber, start,
                                                      frame_count, args.topic))
    thread.start()

def subscribe(subscriber, start, frame_count, topic):
    subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)
    while True:
        data = subscriber.recv_multipart()
        topic = data[0].decode()
        logging.info(topic)
        meta_data = json.loads(data[1])
        frame = data[2]
        frame = np.frombuffer(frame, dtype=np.uint8)
        if meta_data['encoding'] is None:
            frame = np.reshape(frame, (meta_data['height'], meta_data['width'],
                               meta_data['channel']))
        else:
            frame = np.reshape(frame, (frame.shape))
            frame = cv2.imdecode(frame, 1)
        logging.info(meta_data)
    frame_count += 1
    if time.time() - start >= 1:
        logging.info("fps:{}".format(frame_count))
        frame_count = 0
        start = time.time()


def parse_args():
    """Parse command line arguments
    """
    parser = argparse.ArgumentParser(
             formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--endpoint', dest='endpoint',
                        default='tcp://127.0.0.1:65011', 
                        help='ipc/tcp endpoint to connect to \
                              (eg: ipc://<file.sock>/tcp://ip:port')
    parser.add_argument('--topic', dest='topic', default='camera1_stream',
                        help='topic to subscribe to')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)

