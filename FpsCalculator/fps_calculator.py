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
import datetime
import threading
import gc
import xlwt
from xlwt import Workbook

from distutils.util import strtobool
# IMPORT the library to read from IES
from util.util import Util
from util.msgbusutil import MsgBusUtil
from common.libs.ConfigManager import ConfigManager
import eis.msgbus as mb

avg_fps_per_topic = {}


def get_config():
    with open('config.json') as f:
        config_dict = json.load(f)
        return config_dict

logger = logging.getLogger(__name__)

class FpsCalculator:
    """ A sample app to check FPS of
    individual modules. """

    def __init__(self, devMode, topics,
                 total_number_of_frames):
        self.devMode = devMode
        self.publisher, self.topic = topic.split("/")
        os.environ[self.topic+'_cfg'] = config_dict[self.topic+'_cfg']
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
        if not self.devMode:
            conf = {
                "certFile": "../../docker_setup/provision\
                /Certificates/root/root_client_certificate.pem",
                "keyFile": "../../docker_setup/provision\
                /Certificates/root/root_client_key.pem",
                "trustFile": "../../docker_setup/provision\
                /Certificates/ca/ca_certificate.pem"
            }
        cfg_mgr = ConfigManager()
        self.config_client = cfg_mgr.get_config_client("etcd", conf)
        # Setting default AppName as Visualizer to act as subscriber
        # for both VideoIngestion and VideoAnalytics
        os.environ["AppName"] = "Visualizer"

    def eisSubscriber(self):
        """ To subscribe over
        EISMessagebus. """
        config = MsgBusUtil.get_messagebus_config(self.topic, "sub",
                                                  self.publisher,
                                                  self.config_client,
                                                  self.devMode)

        self.topic = self.topic.strip()
        mode_address = os.environ[self.topic + "_cfg"].split(",")
        mode = mode_address[0].strip()
        if (not self.devMode and mode == "zmq_tcp"):
            for key in config[self.topic]:
                if config[self.topic][key] is None:
                    raise ValueError("Invalid Config")

        msgbus = mb.MsgbusContext(config)
        subscriber = msgbus.new_subscriber(self.topic)
        while not self.done_receiving:
            # Discarding both the meta-data & frame
            md, fr = subscriber.recv()
            del md
            del fr
            self.calculate_fps()
        subscriber.close()
        return

    def calculate_fps(self):
        """ Calculates the FPS of required module"""
        # Setting timestamp after first frame receival
        if self.start_subscribing:
            self.start_time = datetime.datetime.now()
            self.start_subscribing = False

        # Incrementing frame count
        self.frame_count += 1

        # Check if all frames are received
        if self.frame_count == int(self.total_number_of_frames):
            # Get time in milliseconds
            end_time = datetime.datetime.now()
            delta = end_time - self.start_time
            diff = delta.total_seconds() * 1000

            # Calculating average fps
            avg_fps = self.frame_count/diff

            # Updating fps per topic dict
            global avg_fps_per_topic
            avg_fps_per_topic[self.topic] = avg_fps * 1000

            # Notifying caller once all frames are received
            self.done_receiving = True
            return


def invokeGC():
    while True:
        gc.enable()
        gc.collect(generation=2)
        time.sleep(3)


def threadRunner(topic):
    """To run FpsCalculator for each topic"""
    fps_app = FpsCalculator(dev_mode,
                            topic,
                            total_number_of_frames)
    fps_app.eisSubscriber()


if __name__ == "__main__":

    config_dict = get_config()

    dev_mode = bool(strtobool(config_dict['dev_mode']))

    if dev_mode == True:
        fmt_str = ('%(asctime)s : %(levelname)s  : {} : %(name)s : [%(filename)s] :' .format("Insecure Mode")+
               '%(funcName)s : in line : [%(lineno)d] : %(message)s')
    else:
        fmt_str = ('%(asctime)s : %(levelname)s : %(name)s : [%(filename)s] :' +
               '%(funcName)s : in line : [%(lineno)d] : %(message)s')

    logging.basicConfig(level=logging.DEBUG,format=fmt_str)

    topics = config_dict['SubTopics']
    export_to_csv = bool(strtobool(config_dict['export_to_csv']))
    total_number_of_frames = int(config_dict['total_number_of_frames'])

    gc_thread = threading.Thread(target=invokeGC)
    gc_thread.start()

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
