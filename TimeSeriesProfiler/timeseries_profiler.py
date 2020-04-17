# Copyright (c) 2020 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import os
import sys
import csv
import json
import logging
import time
import datetime
import threading
import gc
import time
from distutils.util import strtobool
# IMPORT the library to read from EIS
from util.util import Util
from util.msgbusutil import MsgBusUtil
from libs.ConfigManager.python.eis.config_manager import ConfigManager
import eis.msgbus as mb

avg_sps_per_topic = {}


def get_config():
    with open('config.json') as f:
        config_dict = json.load(f)
        return config_dict


logger = logging.getLogger(__name__)


class TimeSeriesCalculator:
    """ A sample app to check SPS of
    individual modules. """

    def __init__(self, devMode, topic,
                 total_number_of_samples, config_dict):
        self.devMode = devMode
        self.publisher, self.topic = topic.split("/")
        os.environ[self.topic+'_cfg'] = config_dict[self.topic+'_cfg']
        self.total_number_of_samples = total_number_of_samples
        self.sample_count = 0
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
                "certFile": config_dict["certFile"],
                "keyFile": config_dict["keyFile"],
                "trustFile": config_dict["trustFile"]
            }
        cfg_mgr = ConfigManager()
        self.config_client = cfg_mgr.get_config_client("etcd", conf)
        self.total_records = dict()

        self.total_records['total_mqttpub_to_influx'] = '0'
        self.total_records['total_influx_to_kapacitor-udf'] = '0'
        self.total_records['total_kapacitor-udf_to_idbconn'] = '0'

        self.total_records['total_udf'] = '0'
        self.total_records['total_idbconn_pub'] = '0'
        self.total_records['total_idbconn_queue_pub'] = '0'
        self.total_records['total_idbconn_to_profiler'] = '0'
        self.total_records['total_e2e'] = '0'
        self.total_records['total_mqtt_to_idbconn'] = '0'
        self.total_records['total_influx_to_idbconn'] = '0'

    def eisSubscriber(self):
        """ To subscribe over
        EISMessagebus. """
        config = MsgBusUtil.get_messagebus_config(self.topic, "sub",
                                                  self.publisher,
                                                  self.config_client,
                                                  self.devMode)

        mode = config["type"]
        if (not self.devMode and mode == "zmq_tcp"):
            for key in config[self.topic]:
                if config[self.topic][key] is None:
                    raise ValueError("Invalid Config")

        msgbus = mb.MsgbusContext(config)
        subscriber = msgbus.new_subscriber(self.topic)

        logger.info('Before for loop: {0}'.format(config))

        while not self.done_receiving:
            records = dict()

            meta_data, _ = subscriber.recv()
            ts_profiler_entry = int(round(time.time() * 1000))
            data = meta_data['data'].split(' ')
            metrics = data[1].split(',')
            for i in metrics:
                key, value = i.split('=')
                records[key] = value

            records['ts_influx_entry'] = int(int(data[2])/1000000)
            records['ts'] = int(float(records['ts']) * 1000)
            records['ts_kapacitor_udf_entry'] = \
                records['ts_kapacitor_udf_entry'][0:13]
            records['ts_kapacitor_udf_exit'] =  \
                records['ts_kapacitor_udf_exit'][0:13]
            records['ts_profiler_entry'] = ts_profiler_entry

            diff = self.process_single_record(records)
            self.calculate_total(diff)
            self.sample_count += 1
            del meta_data

            # Can uncomment and build, below log statments, to see
            # the end to end time of, every metric
            # logger.info('-----------------')
            # logger.info('Record info : {0}'.format(records))
            # logger.info('Diff info : {0}'.format(diff))
            # logger.info('-----------------')

            self.calculate_sps()

        avg_records = self.calculate_avg()
        logger.info('Average stats are : {0}'.format(avg_records))

        subscriber.close()
        return

    def process_single_record(self, records):
        diff = dict()

        # time taken for mqtt publisher to influxdb
        diff['ts_mqttpub_to_influx'] = int(records[
            'ts_influx_entry']) - int(records['ts'])

        # time taken for influx to kapacitor-udf
        diff['ts_influx_to_kapacitor-udf'] = int(records[
            'ts_kapacitor_udf_entry']) - int(records['ts_influx_entry'])

        # time taken in kapacitor-udf
        diff['ts_udf'] = int(records[
            'ts_kapacitor_udf_exit']) - int(records['ts_kapacitor_udf_entry'])

        # time taken for kapacitor-udf to idbconn
        diff['ts_kapacitor-udf_to_idbconn'] = int(records[
            'ts_idbconn_pub_entry']) - int(records['ts_kapacitor_udf_exit'])

        # time taken in influxdbconnector
        diff['ts_idbconn_pub'] = int(records[
            'ts_idbconn_pub_exit']) - int(records['ts_idbconn_pub_entry'])

        # time taken in influxdbconnector's queue
        diff['ts_idbconn_queue_pub'] = int(records[
            'ts_idbconn_pub_queue_exit']) - int(records[
                'ts_idbconn_pub_queue_entry'])

        # time taken in influxdbconnector to spssub
        diff['ts_idbconn_to_profiler'] = int(records['ts_profiler_entry']) - \
            int(records['ts_idbconn_pub_exit'])

        # time taken in mqtt publisher to spssub
        diff['ts_e2e'] = int(records['ts_profiler_entry']) - int(records['ts'])

        # time taken in mqtt publisher to idbconn
        diff['ts_mqtt_to_idbconn'] = int(records[
            'ts_idbconn_pub_exit']) - int(records['ts'])

        # time taken in influx to idbconn
        diff['ts_influx_to_idbconn'] = int(records[
            'ts_idbconn_pub_exit']) - int(records['ts_influx_entry'])

        return diff

    def calculate_total(self, diff):
        self.total_records['total_mqttpub_to_influx'] = int(self.total_records[
            'total_mqttpub_to_influx']) + int(diff['ts_mqttpub_to_influx'])

        self.total_records['total_influx_to_kapacitor-udf'] = \
            int(self.total_records['total_influx_to_kapacitor-udf']) + \
            int(diff['ts_influx_to_kapacitor-udf'])

        self.total_records['total_kapacitor-udf_to_idbconn'] = \
            int(self.total_records['total_kapacitor-udf_to_idbconn']) + \
            int(diff['ts_kapacitor-udf_to_idbconn'])

        self.total_records['total_udf'] = int(self.total_records[
            'total_udf']) + int(diff['ts_udf'])

        self.total_records['total_idbconn_pub'] = int(self.total_records[
            'total_idbconn_pub']) + int(diff['ts_idbconn_pub'])

        self.total_records['total_idbconn_queue_pub'] = \
            int(self.total_records['total_idbconn_queue_pub']) + \
            int(diff['ts_idbconn_queue_pub'])

        self.total_records['total_idbconn_to_profiler'] = \
            int(self.total_records['total_idbconn_to_profiler']) + \
            int(diff['ts_idbconn_to_profiler'])

        self.total_records['total_e2e'] = int(self.total_records[
            'total_e2e']) + int(diff['ts_e2e'])

        self.total_records['total_mqtt_to_idbconn'] = \
            int(self.total_records['total_mqtt_to_idbconn']) + \
            int(diff['ts_mqtt_to_idbconn'])

        self.total_records['total_influx_to_idbconn'] = \
            int(self.total_records['total_influx_to_idbconn']) + \
            int(diff['ts_influx_to_idbconn'])

    def calculate_avg(self):
        avg_records = dict()

        avg_records['avg_mqttpub_to_influx'] = \
            int(self.total_records[
                'total_mqttpub_to_influx']) / self.sample_count

        avg_records['avg_influx_to_kapacitor-udf'] = \
            int(self.total_records[
                'total_influx_to_kapacitor-udf']) / self.sample_count

        avg_records['avg_kapacitor-udf_to_idbconn'] = \
            int(self.total_records[
                'total_kapacitor-udf_to_idbconn']) / self.sample_count

        avg_records['avg_udf'] = \
            int(self.total_records[
                'total_udf']) / self.sample_count

        avg_records['avg_idbconn_pub'] = \
            int(self.total_records[
                'total_idbconn_pub']) / self.sample_count

        avg_records['avg_idbconn_queue_pub'] = \
            int(self.total_records[
                'total_idbconn_queue_pub']) / self.sample_count

        avg_records['avg_idbconn_to_profiler'] = \
            int(self.total_records[
                'total_idbconn_to_profiler']) / self.sample_count

        avg_records['avg_e2e'] = \
            int(self.total_records['total_e2e']) / self.sample_count

        avg_records['avg_mqtt_to_idbconn'] = \
            int(self.total_records[
                'total_mqtt_to_idbconn']) / self.sample_count

        avg_records['avg_influx_to_idbconn'] = \
            int(self.total_records[
                'total_influx_to_idbconn']) / self.sample_count

        return avg_records

    def calculate_sps(self):
        """ Calculates the SPS of required module"""
        # Setting timestamp after first sample receival
        if self.start_subscribing:
            self.start_time = int(round(time.time()))
            self.start_subscribing = False

        # Check if all samples are received
        if self.sample_count == self.total_number_of_samples:
            # Get time in milliseconds
            end_time = int(round(time.time()))

            logger.info('start-time and end-time are : {0} {1}'.
                        format(self.start_time, end_time))

            diff = end_time - self.start_time
            # Calculating average sps
            avg_sps = self.sample_count/diff

            # Updating sps per topic dict
            global avg_sps_per_topic
            avg_sps_per_topic[self.topic] = avg_sps

            # Notifying caller once all samples are received
            self.done_receiving = True
            return


def threadRunner(topic, config_dict):
    """ To run TimeSeriesCalculator for each topic """
    tsc_app = TimeSeriesCalculator(dev_mode, topic, total_number_of_samples,
                                   config_dict)

    tsc_app.eisSubscriber()


if __name__ == "__main__":

    config_dict = get_config()

    dev_mode = bool(strtobool(config_dict['dev_mode']))

    if dev_mode:
        fmt_str = (
            '%(asctime)s : %(levelname)s  : {} : %(name)s : [%(filename)s] :'
            .format("Insecure Mode") +
            '%(funcName)s : in line : [%(lineno)d] : %(message)s')
    else:
        fmt_str = ('%(asctime)s : %(levelname)s : %(name)s : [%(filename)s] :'
                   + '%(funcName)s : in line : [%(lineno)d] : %(message)s')

    logging.basicConfig(level=logging.DEBUG, format=fmt_str)

    topics = config_dict['SubTopics']
    export_to_csv = bool(strtobool(config_dict['export_to_csv']))
    total_number_of_samples = int(config_dict['total_number_of_samples'])

    # Calculating SPS for each topic
    threads = []
    for topic in topics:
        thread = threading.Thread(target=threadRunner,
                                  args=(topic, config_dict,))

        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    # Calculating overall sps for all topics
    final_sps = 0.0
    for topic in avg_sps_per_topic.keys():
        final_sps += avg_sps_per_topic[topic]

    if export_to_csv:

        f = open('./out/SPS_Results.csv', 'wt')
        try:
            writer = csv.writer(f)
            writer.writerow(('total number of samples', 'final sps'))
            writer.writerow((total_number_of_samples, final_sps))
        finally:
            f.close()

        logger.info('Check SPS_Results.csv file for total SPS...')
    else:
        logger.info('Average SPS for each topic {0}'
                    .format(avg_sps_per_topic))
        logger.info('Total SPS for {0} samples {1}'
                    .format(total_number_of_samples,
                            final_sps))

    # Exiting after SPS is calculated
    sys.exit()
