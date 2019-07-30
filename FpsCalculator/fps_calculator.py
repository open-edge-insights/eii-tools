"""
Copyright (c) 2019 Intel Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import os
import sys
import json
import logging
import time
import threading
import xlwt
from xlwt import Workbook

from distutils.util import strtobool
# IMPORT the library to read from IES
from DataBus import databus
import eis.msgbus as mb

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s : %(levelname)s : \
                    %(name)s : [%(filename)s] :' +
                    '%(funcName)s : in line : [%(lineno)d] : %(message)s')
logger = logging.getLogger(__name__)

startTime = 0.0
current_FPS = 0
total_FPS = 0
total_iterations = 0
total_frames_received = 0


def get_config():
    with open('config.json') as f:
        config_dict = json.load(f)
        return config_dict


class FpsCalculator:
    """ A sample app to check FPS of
    individual modules. """

    def __init__(self, devMode, subscribe_stream, subscribe_bus, host, port,
                 db_cert, db_priv, db_trust,
                 total_number_of_frames, export_to_csv):
        self.devMode = devMode
        self.subscribe_stream = subscribe_stream
        self.subscribe_bus = subscribe_bus
        self.db_cert = db_cert
        self.db_priv = db_priv
        self.db_trust = db_trust
        self.total_number_of_frames = total_number_of_frames
        self.export_to_csv = export_to_csv
        self.host = host
        self.port = port
        if self.export_to_csv:
            self.wb = Workbook()
            self.sheet1 = self.wb.add_sheet('FPS Results')

        try:
            if self.subscribe_bus == 'opcua':
                if self.devMode:
                    contextConfig = {
                        'endpoint': 'opcua://localhost:4840',
                        'direction': 'SUB',
                        'name': 'StreamManager',
                        'certFile': "",
                        'privateFile': "",
                        'trustFile': ""
                        }
                else:
                    contextConfig = {
                        'endpoint': 'opcua://localhost:4840',
                        'direction': 'SUB',
                        'name': 'StreamManager',
                        'certFile': db_cert,
                        'privateFile': db_priv,
                        'trustFile': db_trust
                    }
                self.ieidbus = databus(logger)
                self.ieidbus.ContextCreate(contextConfig)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    def eisSubscriber(self, topic, callback):
        global startTime
        config = {"type": "zmq_tcp", topic:
                  {"host": self.host, "port": self.port}}
        self.msgbus = mb.MsgbusContext(config)
        self.subscriber = self.msgbus.new_subscriber(topic)
        startTime = time.time()
        while True:
            # Discarding both the meta-data & frame
            _, _ = self.subscriber.recv()
            callback(topic)

    def run(self):
        global startTime
        if self.subscribe_bus == 'opcua':
            topicConfigs = []
            for topic in self.subscribe_stream:
                topicConfigs.append({"ns": "streammanager",
                                     "name": topic, "dType": "string"})
            startTime = time.time()
            self.ieidbus.Subscribe(topicConfigs, len(topicConfigs),
                                   "START", self.cbFunc)
        elif self.subscribe_bus == 'eismessagebus':
            if len(self.subscribe_stream) > 1:
                for i in range(len(self.subscribe_stream)):
                    stream_thread = \
                        threading.Thread(target=self.eisSubscriber,
                                         args=[self.subscribe_stream[i],
                                               self.calculate_fps])
                    stream_thread.start()
            else:
                startTime = time.time()
                self.eisSubscriber(self.subscribe_stream[0],
                                   callback=self.calculate_fps)

    def calculate_fps(self, topic):
        """ Calculates the FPS of required module"""
        global current_FPS
        current_FPS += 1
        global total_frames_received
        total_frames_received += 1
        global startTime
        global total_FPS
        global total_iterations
        if time.time() - startTime >= 1:
            total_iterations += 1
            total_FPS += current_FPS
            average_FPS = total_FPS/total_iterations
            logger.info('Current FPS value for {0}: {1}'.format(topic,
                        current_FPS))
            if total_frames_received >= int(self.total_number_of_frames):
                if self.export_to_csv:
                    logger.info('Check FPS_results.xls file for total FPS...')
                    self.sheet1.write(1, 0, 'Average FPS for {0} frames: {1}'
                                      .format(total_frames_received,
                                              average_FPS))
                    self.wb.save('FPS_results.xls')
                else:
                    logger.info('Total average FPS for {0} frames: {1}'
                                .format(total_frames_received, average_FPS))
                sys.exit(1)
            startTime = time.time()
            current_FPS = 0
            return

    def cbFunc(self, topic, msg):
        # Uncomment below line to display classifier results
        # logger.info("Msg: {} received on topic: {}".format(msg, topic))
        self.calculate_fps(topic)


if __name__ == "__main__":

    config_dict = get_config()
    subscribe_stream = config_dict['output_stream']
    dev_mode = bool(strtobool(config_dict['dev_mode']))
    export_to_csv = bool(strtobool(config_dict['export_to_csv']))
    subscribe_bus = config_dict['subscribe_bus']
    db_cert = config_dict['server_cert']
    db_priv = config_dict['client_cert']
    db_trust = config_dict['ca_cert']
    total_number_of_frames = int(config_dict['total_number_of_frames'])
    host = config_dict['host']
    port = config_dict['port']
    fps_app = FpsCalculator(dev_mode,
                            subscribe_stream,
                            subscribe_bus,
                            host,
                            port,
                            db_cert,
                            db_priv,
                            db_trust,
                            total_number_of_frames,
                            export_to_csv)
    fps_app.run()
