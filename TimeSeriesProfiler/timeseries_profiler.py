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
from distutils.util import strtobool
# IMPORT the library to read from EII
from util.util import Util
import cfgmgr.config_manager as cfg
import eii.msgbus as mb

avg_records = {}

logger = logging.getLogger(__name__)


class TimeSeriesCalculator:
    """ A sample app to check Average Stats of
    individual modules. """

    def __init__(self, topic, msgbus_cfg, dev_mode, total_number_of_samples):
        self.devMode = dev_mode
        self.topic = topic
        self.total_number_of_samples = total_number_of_samples
        self.sample_count = 0
        self.start_time = 0.0
        self.done_receiving = False

        self.total_records = dict()
        self.msgbus_cfg = msgbus_cfg
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

    def eiiSubscriber(self):
        """ To subscribe over
        EIIMessagebus. """

        mode = self.msgbus_cfg["type"]
        if (not self.devMode and mode == "zmq_tcp"):
            for key in self.msgbus_cfg[self.topic]:
                if self.msgbus_cfg[self.topic][key] is None:
                    raise ValueError("Invalid Config")

        msgbus = mb.MsgbusContext(self.msgbus_cfg)
        subscriber = msgbus.new_subscriber(self.topic)

        logger.info('Ready to receive data from msgbus')

        while not self.done_receiving:
            records = dict()

            meta_data, _ = subscriber.recv()
            ts_profiler_entry = int(round(time.time() * 1000))
            data = meta_data['data'].split(' ')
            metrics = data[1].split(',')
            for i in metrics:
                key, value = i.split('=')
                records[key] = value

            required_timestamps = ["ts", "ts_kapacitor_udf_entry",
                                   "ts_kapacitor_udf_exit",
                                   "ts_idbconn_pub_entry",
                                   "ts_idbconn_pub_queue_entry",
                                   "ts_idbconn_influx_respose_write",
                                   "ts_idbconn_pub_queue_exit",
                                   "ts_idbconn_pub_exit"]
            missing_timestamps = \
                [x for x in required_timestamps if x not in records.keys()]
            if len(missing_timestamps) != 0:
                logger.error("These timestamps are missing! {}. Exiting.."
                             .format(missing_timestamps))
                os._exit(1)
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

            if self.sample_count == self.total_number_of_samples:
                self.done_receiving = True

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
        global avg_records

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

def threadRunner(topic, msgbus_cfg, dev_mode, total_number_of_samples):
    """ To run TimeSeriesCalculator for each topic """
    tsc_app = TimeSeriesCalculator(topic, msgbus_cfg,
                                   dev_mode, total_number_of_samples)

    tsc_app.eiiSubscriber()


if __name__ == "__main__":

    try:
        ctx = cfg.ConfigMgr()
        app_cfg = ctx.get_app_config()
        app_name = ctx.get_app_name()
        dev_mode = ctx.is_dev_mode()
        logger.info("app name is{}".format(app_name))
        sub_ctx = ctx.get_subscriber_by_index(0)
        msgbus_cfg = sub_ctx.get_msgbus_config()
        topics = sub_ctx.get_topics()
    except Exception as e:
        logger.error("{}".format(e))
    if dev_mode:
        fmt_str = (
            '%(asctime)s : %(levelname)s  : {} : %(name)s : [%(filename)s] :'
            .format("Insecure Mode") +
            '%(funcName)s : in line : [%(lineno)d] : %(message)s')
    else:
        fmt_str = ('%(asctime)s : %(levelname)s : %(name)s : [%(filename)s] :'
                   + '%(funcName)s : in line : [%(lineno)d] : %(message)s')

    logging.basicConfig(level=logging.DEBUG, format=fmt_str)

    export_to_csv = bool(strtobool(app_cfg['export_to_csv']))
    total_number_of_samples = int(app_cfg['total_number_of_samples'])
    logger.info("total_number_of_samples is {}"
                .format(total_number_of_samples))
    # Calculating Average stats for each topic
    threads = []
    for topic in topics:
        thread = threading.Thread(target=threadRunner, args=(topic, msgbus_cfg,
                                  dev_mode, total_number_of_samples,))

        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    if export_to_csv:
        f = open('./out/avg_latency_Results.csv', 'wt')
        try:
            writer = csv.writer(f)
            writer.writerow(avg_records.keys())
            writer.writerow(avg_records.values())
        finally:
            f.close()
        logger.info('Check avg_latency_Results.csv file for Average stats...')

    # Exiting after Average stats is calculated
    sys.exit()
