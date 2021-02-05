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

# Dict to store sps mode results
avg_sps_per_topic = {}

# Dict to store monitor mode results
monitor_mode_results = {}

logger = logging.getLogger(__name__)


class TimeSeriesCalculator:
    """ A sample app to check Average Stats of
    individual modules. """

    def __init__(self, topics_list, msgbus_cfg, config_dict):

        # Initializing dev_mode variable
        self.dev_mode = ctx.is_dev_mode()

        self.monitor_mode, self.sps_mode = False, False
        if config_dict['mode'] == 'monitor':
            self.monitor_mode = True
        elif config_dict['mode'] == 'sps':
            self.sps_mode = True
        else:
            logger.error('Only two modes supported.'
                         ' Please select either sps or monitor mode')
            os._exit(-1)
        # Initializing monitor_mode related variables
        if self.monitor_mode:
            self.monitor_mode_settings = config_dict['monitor_mode_settings']
            logger.info('Please ensure EII containers are '
                        'running with PROFILING_MODE set to true')
        if config_dict['total_number_of_samples'] is (-1):
            if self.monitor_mode:
                # Set total number of samples to infinity
                self.total_number_of_samples = float('inf')
                logger.warning('Total number of samples set to infinity. '
                               'Please stop the time series profiler '
                               'container to exit.')
            elif self.sps_mode:
                logger.error("total_number_of_samples should never be set as"
                             " (-1) for 'sps' mode. Exiting..")
                os._exit(1)

        else:
            self.total_number_of_samples = \
                config_dict['total_number_of_samples']

        # Enabling this switch publishes the results to an external csv file
        self.export_to_csv = config_dict['export_to_csv']

        # Initializing msgbus related variables
        self.msgbus_cfg = msgbus_cfg
        self.topic = topics_list[0]
        self.devMode = dev_mode
        self.sample_count = 0
        self.start_time = 0.0
        self.done_receiving = False
        self.start_subscribing = True

        self.total_records = dict()
        # Initializing variables related to profiling
        self.e2e = 0.0

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
            meta_data, _ = subscriber.recv()
            self.handling_mode(meta_data)
            del meta_data
        subscriber.close()
        return

    def handling_mode(self, meta_data):
        if self.monitor_mode:
            records = dict()
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
            self.add_profile_data(meta_data, records)
            del meta_data
        elif self.sps_mode:
            self.calculate_sps()
            # Discarding the meta-data
            del meta_data
        return

    def prepare_per_sample_stats(self, records):
        """ Method to calculate per sample time metrics

        :param records: dict of time spent in time series pipeline
        for different component
        :type records: dict
        """

        per_sample_stats = dict()
        e2e = int(records['ts_profiler_entry']) - int(records['ts'])
        per_sample_stats["e2e"] = e2e

        # time taken for mqtt publisher to influxdb
        per_sample_stats['mqttpub_to_influx_diff'] = int(records[
            'ts_influx_entry']) - int(records['ts'])

        # time taken for influx to kapacitor-udf
        per_sample_stats['influx_to_kapacitor-udf_diff'] = int(records[
            'ts_kapacitor_udf_entry']) - int(records['ts_influx_entry'])

        # time taken in kapacitor-udf
        per_sample_stats['udf_diff'] = int(records[
            'ts_kapacitor_udf_exit']) - int(records['ts_kapacitor_udf_entry'])

        # time taken for kapacitor-udf to idbconn
        per_sample_stats['kapacitor-udf_to_idbconn_diff'] = int(records[
            'ts_idbconn_pub_entry']) - int(records['ts_kapacitor_udf_exit'])

        # time taken in influxdbconnector
        per_sample_stats['idbconn_pub_diff'] = int(records[
            'ts_idbconn_pub_exit']) - int(records['ts_idbconn_pub_entry'])

        # time taken in influxdbconnector's queue
        per_sample_stats['idbconn_queue_pub_diff'] = int(records[
            'ts_idbconn_pub_queue_exit']) - int(records[
                'ts_idbconn_pub_queue_entry'])

        # time taken in influxdbconnector to spssub
        per_sample_stats['idbconn_to_profiler_diff'] = \
            int(records['ts_profiler_entry']) - \
            int(records['ts_idbconn_pub_exit'])

        # time taken in mqtt publisher to idbconn
        per_sample_stats['mqtt_to_idbconn_diff'] = int(records[
            'ts_idbconn_pub_exit']) - int(records['ts'])

        # time taken in influx to idbconn
        per_sample_stats['influx_to_idbconn_diff'] = int(records[
            'ts_idbconn_pub_exit']) - int(records['ts_influx_entry'])

        return per_sample_stats

    def prepare_avg_stats(self, per_sample_stats):
        """ Method to calculate average metrics
            for the pipeline

        :param per_sample_stats: dict of sample metrics
        :type per_sample_stats: dict
        """
        if self.start_subscribing:
            for key in per_sample_stats:
                temp = key.split("_diff")[0]
                self.total_records[temp + '_total'] = 0

        for key in per_sample_stats:
            if '_diff' in key:
                temp = key.split("_diff")[0]
                self.total_records[temp + '_total'] =\
                    self.total_records[temp + '_total'] +\
                    per_sample_stats[temp + '_diff']

        self.e2e += per_sample_stats["e2e"]
        avg_e2e = self.e2e / self.sample_count

        avg_stats = dict()
        for key in self.total_records:
            if '_total' in key:
                temp = key.split("_total")[0]
                avg_stats[temp + '_avg'] =\
                    int(self.total_records[temp + '_total']) / \
                    self.sample_count

        avg_stats["avg_e2e"] = avg_e2e
        avg_stats.pop('e2e_avg', None)
        return avg_stats

    def add_profile_data(self, metadata, records):
        """ Method to calculate sample rate

        :param metadata: data recieved from msgbus
        :type metadata: dict
        :param records: dict of time spent in time series pipeline
         for different component
        :type records: dict
        """
        self.sample_count += 1
        if self.sample_count == self.total_number_of_samples:
            self.done_receiving = True
        per_sample_stats = self.prepare_per_sample_stats(records)
        avg_value = self.prepare_avg_stats(per_sample_stats)

        csv_writer = None
        if self.start_subscribing and self.export_to_csv:
            # File to write meta-data at runtime
            csv_file = open('./out/timeseries_profiler_runtime_stats.csv', 'w')
            csv_writer = csv.writer(csv_file)
        elif self.export_to_csv:
            csv_file = open('./out/timeseries_profiler_runtime_stats.csv', 'a')
            csv_writer = csv.writer(csv_file)

        if self.export_to_csv:
            if self.monitor_mode_settings['avg_stats']:
                # If only avg_stats is true, write avg_stats to csv
                # and print per_sample_stats or metadata based on their
                # respective keys set to true
                if self.start_subscribing:
                    csv_writer.writerow(avg_value.keys())
                    self.start_subscribing = False
                csv_writer.writerow(avg_value.values())
                if self.monitor_mode_settings['per_sample_stats']:
                    logger.info(
                        f'Per sample stats in miliseconds: {per_sample_stats}')
                if self.monitor_mode_settings['display_metadata']:
                    logger.info(f'Meta data is: {metadata}')
            elif self.monitor_mode_settings['per_sample_stats']:
                # If only per_sample_stats is true,
                # write per_sample_stats to csv
                # and print metadata if its key is set to true
                if self.start_subscribing:
                    csv_writer.writerow(per_sample_stats.keys())
                    self.start_subscribing = False
                csv_writer.writerow(per_sample_stats.values())
                if self.monitor_mode_settings['display_metadata']:
                    logger.info(f'Meta data is: {metadata}')
            elif self.monitor_mode_settings['display_metadata']:
                # If only display_metadata is true, write metadata to csv
                if self.start_subscribing:
                    csv_writer.writerow(metadata.keys())
                    self.start_subscribing = False
                csv_writer.writerow(metadata.values())
        else:
            if self.monitor_mode_settings['display_metadata']:
                logger.info(f'Meta data is: {metadata}')
            if self.monitor_mode_settings['per_sample_stats']:
                logger.info(
                    f'Per sample stats in miliseconds: {per_sample_stats}')
            if self.monitor_mode_settings['avg_stats']:
                logger.info(f'sample avg stats in milliseconds: {avg_value}')

        if self.export_to_csv:
            csv_file.close()
        if self.done_receiving:
            global monitor_mode_results
            # Updating avg values of all streams
            # after subscription is done
            monitor_mode_results.update(avg_value)

    def calculate_sps(self):
        """ Method to calculate SPS of provided stream """
        # Setting timestamp after first Sample receival
        if self.start_subscribing:
            self.start_time = datetime.datetime.now()
            self.start_subscribing = False

        # Incrementing sample count
        self.sample_count += 1

        # Check if all sample are received
        if self.sample_count == self.total_number_of_samples:
            # Get time in milliseconds
            end_time = datetime.datetime.now()
            delta = end_time - self.start_time
            diff = delta.total_seconds() * 1000

            # Calculating average sps
            avg_sps = self.sample_count/diff

            # Updating sps per topic dict
            global avg_sps_per_topic
            avg_sps_per_topic[self.topic] = avg_sps * 1000

            # Notifying caller once all samples are received
            self.done_receiving = True
            return


def threadRunner(topics_list, msgbus_cfg, config_dict):
    """ To run TimeSeriesCalculator for each topic """
    tsc_app = TimeSeriesCalculator(topics_list, msgbus_cfg,
                                   config_dict)

    tsc_app.eiiSubscriber()


if __name__ == "__main__":

    try:
        ctx = cfg.ConfigMgr()
        config_dict = ctx.get_app_config()
        app_name = ctx.get_app_name()
        dev_mode = ctx.is_dev_mode()
        logger.info("app name is{}".format(app_name))
        # Fetching total number of subscribers
        num_of_elements = ctx.get_num_subscribers()

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

    export_to_csv = config_dict['export_to_csv']
    total_number_of_samples = config_dict['total_number_of_samples']
    logger.info("total_number_of_samples is {}"
                .format(total_number_of_samples))

    # Calculating Average stats for each topic
    threads = []
    for index in range(0, num_of_elements):
        sub_ctx = ctx.get_subscriber_by_index(index)
        msgbus_cfg = sub_ctx.get_msgbus_config()
        topics_list = sub_ctx.get_topics()
        thread = threading.Thread(target=threadRunner, args=(topics_list,
                                                             msgbus_cfg,
                                                             config_dict,))

        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    # Calculating overall sps for all topics
    final_sps = 0.0
    for topic in avg_sps_per_topic.keys():
        final_sps += avg_sps_per_topic[topic]

    if export_to_csv:
        csv_columns = ['Stream Name', 'Average SPS']
        avg_sps_per_topic['Total Sps'] = final_sps
        try:
            if config_dict['mode'] == 'monitor':
                # Generating excel sheet for monitor_mode
                with open('./out/TSP_Results.csv', 'w') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(csv_columns)
                    for key, value in monitor_mode_results.items():
                        writer.writerow([key, value])
                logger.info('Check TSP_Results.csv file '
                            'inside build dir for results...')
            if config_dict['mode'] == 'sps':
                # Generating excel sheet for SPS mode
                with open('./out/SPS_Results.csv', 'w') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(csv_columns)
                    for key, value in avg_sps_per_topic.items():
                        writer.writerow([key, value])
                logger.info('Check SPS_Results.csv file '
                            'inside build dir for results...')
        except IOError:
            logger.error("I/O error")
    else:
        if config_dict['mode'] == 'sps':
            logger.info('Average SPS for each topic {0}'
                        .format(avg_sps_per_topic))
            logger.info('Total SPS for {0} samples {1}'
                        .format(total_number_of_samples,
                                final_sps))
        if config_dict['mode'] == 'monitor':
            logger.info('Monitor mode results {}'
                        .format(monitor_mode_results))

    # Exiting after metrics are calculated
    os._exit(0)
