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
from StreamSubLib.StreamSubLib import StreamSubLib

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

    def __init__(self, devMode, subscribe_stream, subscribe_bus,
                 db_cert, db_priv, db_trust, number_of_streams,
                 total_number_of_frames, export_to_csv):
        self.devMode = devMode
        self.subscribe_stream = subscribe_stream
        self.subscribe_bus = subscribe_bus
        self.db_cert = db_cert
        self.db_priv = db_priv
        self.db_trust = db_trust
        self.number_of_streams = number_of_streams
        self.total_number_of_frames = total_number_of_frames
        self.export_to_csv = export_to_csv
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

            elif self.subscribe_bus == 'streamsublib':
                self.strmSubscrbr = StreamSubLib()
                # Pass the mode
                self.strmSubscrbr.init(dev_mode=devMode)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    def run(self):
        global startTime
        if self.subscribe_bus == 'opcua':
            topicConfigs = []
            for topic in self.subscribe_stream:
                topicConfigs.append({"namespace": "streammanager",
                                     "name": topic, "dType": "string"})
            startTime = time.time()
            self.ieidbus.Subscribe(topicConfigs, len(topicConfigs),
                                   "START", self.cbFunc)
        elif self.subscribe_bus == 'streamsublib':
            if self.number_of_streams is not None \
               and int(self.number_of_streams) > 1:
                for i in range(int(self.number_of_streams)):
                    stream_thread = \
                        threading.Thread(target=self.strmSubscrbr.Subscribe,
                                         args=[self.subscribe_stream[i],
                                               self.calculate_fps])
                    startTime = time.time()
                    stream_thread.start()
            else:
                startTime = time.time()
                self.strmSubscrbr.Subscribe(self.subscribe_stream[0],
                                            self.calculate_fps)

    def calculate_fps(self, pointData):
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
            influxPoint = json.loads(pointData)
            current_stream = influxPoint.get('Measurement')
            logger.info('Current FPS value for {0}: {1}'.format(current_stream,
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
        self.calculate_fps(msg)


def parse_args():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser()

    parser.add_argument('--dev-mode', dest='dev_mode',
                        default='false',
                        help='run in secured or non-secured mode')
    parser.add_argument('--subscribe-bus', dest='subscribe_bus',
                        help='message bus to subscribe')
    parser.add_argument('--certFile', dest='db_cert',
                        help='cert file')
    parser.add_argument('--privateFile', dest='db_priv',
                        help='private file')
    parser.add_argument('--trustFile', dest='db_trust',
                        help='trust file')
    parser.add_argument('--number-of-streams', dest='number_of_streams',
                        help='number of streams')
    parser.add_argument('--total-frames', dest='total_number_of_frames',
                        help='total number of streams')
    parser.add_argument('--export-csv', dest='export_to_csv',
                        help='export result to csv file')
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    dev_mode = bool(strtobool(args.dev_mode))
    export_to_csv = bool(strtobool(args.export_to_csv))
    stream_dict = get_config()
    subscribe_stream = stream_dict['output_stream']
    subscribe_bus = args.subscribe_bus
    db_cert = args.db_cert
    db_priv = args.db_priv
    db_trust = args.db_trust
    number_of_streams = args.number_of_streams
    total_number_of_frames = int(args.total_number_of_frames)
    fps_app = FpsCalculator(dev_mode,
                            subscribe_stream,
                            subscribe_bus,
                            db_cert,
                            db_priv,
                            db_trust,
                            number_of_streams,
                            total_number_of_frames,
                            export_to_csv)
    fps_app.run()
