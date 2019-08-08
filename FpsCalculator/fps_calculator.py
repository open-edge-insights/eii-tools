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
from libs.common.py.util import Util
from libs.ConfigManager import ConfigManager
import eis.msgbus as mb

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s : %(levelname)s : \
                    %(name)s : [%(filename)s] :' +
                    '%(funcName)s : in line : [%(lineno)d] : %(message)s')
logger = logging.getLogger(__name__)

avg_fps_per_topic = {}


def get_config():
    with open('config.json') as f:
        config_dict = json.load(f)
        return config_dict


class FpsCalculator:
    """ A sample app to check FPS of
    individual modules. """

    def __init__(self, devMode, topics,
                 db_cert, db_priv,
                 db_trust, total_number_of_frames):
        self.devMode = devMode
        self.publisher, self.topic = topic.split("/")
        os.environ[self.topic+'_cfg'] = config_dict[self.topic+'_cfg']
        self.db_cert = db_cert
        self.db_priv = db_priv
        self.db_trust = db_trust
        self.total_number_of_frames = total_number_of_frames
        self.frame_count = 0
        self.start_time = 0.0
        self.done_receiving = False
        self.start_subscribing = True
        conf = {
            "certFile": "",
            "keyFile": "",
            "trustFile": ""
        }
        cfg_mgr = ConfigManager()
        self.config_client = cfg_mgr.get_config_client("etcd", conf)
        # Setting default AppName as Visualizer to act as subscriber
        # for both VideoIngestion and VideoAnalytics
        os.environ["AppName"] = "Visualizer"
        try:
            topic_config = Util.get_messagebus_config(self.topic, "sub",
                                                      self.publisher,
                                                      self.config_client,
                                                      self.devMode)
            if topic_config['type'] == 'opcua':
                if self.devMode:
                    contextConfig = {
                        'endpoint': '{}://{}:{}'.format(topic_config['type'],
                                                        topic_config['host'],
                                                        topic_config['port']),
                        'direction': 'SUB',
                        'name': 'StreamManager',
                        'certFile': "",
                        'privateFile': "",
                        'trustFile': ""
                        }
                else:
                    contextConfig = {
                        'endpoint': '{}://{}:{}'.format(topic_config['type'],
                                                        topic_config['host'],
                                                        topic_config['port']),
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
        """ To subscribe over
        EISMessagebus. """
        config = Util.get_messagebus_config(self.topic, "sub",
                                            self.publisher,
                                            self.config_client,
                                            self.devMode)
        msgbus = mb.MsgbusContext(config)
        subscriber = msgbus.new_subscriber(topic)
        while not self.done_receiving:
            # Discarding both the meta-data & frame
            _, _ = subscriber.recv()
            callback(topic)
        subscriber.close()
        return

    def run(self, topic):
        """ To run the respective data bus subscribers"""
        config = Util.get_messagebus_config(self.topic, "sub",
                                            self.publisher,
                                            self.config_client,
                                            self.devMode)
        if config['type'] == 'opcua':
            topicConfigs = []
            topicConfigs.append({"ns": "streammanager",
                                "name": topic, "dType": "string"})
            self.start_time = time.time()
            self.ieidbus.Subscribe(topicConfigs, len(topicConfigs),
                                   "START", self.cbFunc)
        elif 'zmq' in config['type']:
            self.eisSubscriber(self.topic,
                               callback=self.calculate_fps)
            return

    def calculate_fps(self, topic):
        """ Calculates the FPS of required module"""
        # Setting timestamp after first frame receival
        if self.start_subscribing:
            self.start_time = time.time()
        self.start_subscribing = False

        # Incrementing frame count
        self.frame_count += 1

        # Check if all frames are received
        if self.frame_count == int(self.total_number_of_frames):
            # Calculating average fps
            avg_fps = self.frame_count/(time.time()-self.start_time)

            # Updating fps per topic dict
            global avg_fps_per_topic
            avg_fps_per_topic[self.topic] = avg_fps

            # Notifying caller once all frames are received
            self.done_receiving = True
            return

    def cbFunc(self, topic, msg):
        # Uncomment below line to display classifier results
        # logger.info("Msg: {} received on topic: {}".format(msg, topic))
        self.calculate_fps(topic)


def threadRunner(topic):
    """To run FpsCalculator for each topic"""
    dev_mode = bool(strtobool(config_dict['dev_mode']))
    db_cert = config_dict['server_cert']
    db_priv = config_dict['client_cert']
    db_trust = config_dict['ca_cert']
    fps_app = FpsCalculator(dev_mode,
                            topic,
                            db_cert,
                            db_priv,
                            db_trust,
                            total_number_of_frames)
    fps_app.run(topic)


if __name__ == "__main__":

    config_dict = get_config()
    topics = config_dict['SubTopics']
    export_to_csv = bool(strtobool(config_dict['export_to_csv']))
    total_number_of_frames = int(config_dict['total_number_of_frames'])

    # Calculating FPS for each topic
    threads = []
    for topic in topics:
        thread = threading.Thread(target=threadRunner, args=(topic,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    # Calculating overall fps for all topics
    final_fps = 0.0
    for topic in avg_fps_per_topic.keys():
        final_fps += avg_fps_per_topic[topic]

    if export_to_csv:
        wb = Workbook()
        sheet1 = wb.add_sheet('FPS Results')
        sheet1.write(1, 0, 'Average FPS for each topic {0}'
                     .format(avg_fps_per_topic))
        sheet1.write(2, 0, 'Total FPS for {0} frames {1}'
                     .format(total_number_of_frames, final_fps))
        logger.info('Check FPS_results.xls file for total FPS...')
    else:
        logger.info('Average FPS for each topic {0}'
                    .format(avg_fps_per_topic))
        logger.info('Total FPS for {0} frames {1}'
                    .format(total_number_of_frames,
                            final_fps))
