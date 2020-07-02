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
import csv
from distutils.util import strtobool
# IMPORT the library to read from EIS
from util.util import Util
from eis.env_config import EnvConfig
from eis.config_manager import ConfigManager
import eis.msgbus as mb
import coloredlogs

coloredlogs.install()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


# Dict to store Fps mode results
avg_fps_per_topic = {}
# Dict to store monitor mode results
monitor_mode_results = {}
# Keys related to monitor mode settings
dict_of_keys = {
                "VideoIngestion_ingestor_blocked_ts":
                "VI ingestor/UDF input queue is blocked,"
                "consider reducing ingestion rate",

                "VideoAnalytics_subscriber_blocked_ts":
                "VA subs/UDF input queue is blocked, "
                "consider reducing ZMQ_RECV_HWM value "
                "or reducing ingestion rate",

                "VideoIngestion_UDF_output_queue_blocked_ts":
                "UDF VI output queue blocked",

                "VideoAnalytics_UDF_output_queue_blocked_ts":
                "UDF VA output queue blocked"
               }


def get_config():
    """ Method to fetch config. """
    with open('config.json') as f:
        config_dict = json.load(f)
        return config_dict


class VideoProfiler:
    """ A sample app to measure frame rate
        related info across Video Pipeline
    """

    def __init__(self, topic,
                 config_dict):
        """Constructor for VideoProfiler

        :param topic: name of the topic
        :type topic: str
        :param config_dict: VideoProfiler config
        :type config_dict: dict
        """
        # Initializing dev_mode variable
        self.dev_mode = config_dict['dev_mode']

        self.monitor_mode, self.fps_mode = False, False
        if config_dict['mode'] == 'monitor':
            self.monitor_mode = True
        elif config_dict['mode'] == 'fps':
            self.fps_mode = True
        else:
            logger.error('Only two modes supported.'
                         ' Please select either fps or monitor mode')
            os._exit(-1)

        # Initializing monitor_mode related variables
        if self.monitor_mode:
            self.monitor_mode_settings = config_dict['monitor_mode_settings']
            logger.info('Please ensure EIS containers are '
                        'running with PROFILING_MODE set to true')
        if config_dict['total_number_of_frames'] is (-1):
            # Set total number of frames to infinity
            self.total_frames = float('inf')
            logger.warning('Total number of frames set to infinity. Please '
                            'use Ctrl+C to exit.')
        else:
            self.total_frames = \
                config_dict['total_number_of_frames']

        # Enabling this switch publishes the results to an external csv file
        self.export_to_csv = config_dict['export_to_csv']

        # Initializing msgbus related variables
        self.publisher, self.topic = topic.split("/")
        os.environ[self.topic+'_cfg'] = config_dict[self.topic+'_cfg']

        self.frame_count = 0
        self.start_time = 0.0
        self.done_receiving = False
        self.start_subscribing = True
        self.total_records = dict()

        # Initializing variables related to profiling
        self.VI_time_to_push_to_queue = 0.0
        self.e2e = 0.0

        conf = {
            "certFile": "",
            "keyFile": "",
            "trustFile": ""
        }
        if not self.dev_mode:
            conf = {
                "certFile": config_dict["certFile"],
                "keyFile": config_dict["keyFile"],
                "trustFile": config_dict["trustFile"]
            }
        cfg_mgr = ConfigManager()
        self.config_client = cfg_mgr.get_config_client("etcd", conf)
        # Setting default AppName as Visualizer to act as subscriber
        # for both VideoIngestion and VideoAnalytics
        os.environ["AppName"] = "Visualizer"

    def eisSubscriber(self):
        """ To subscribe over
        EISMessagebus. """
        config = EnvConfig.get_messagebus_config(self.topic, "sub",
                                                 self.publisher,
                                                 self.config_client,
                                                 self.dev_mode)

        self.topic = self.topic.strip()
        mode_address = os.environ[self.topic + "_cfg"].split(",")
        mode = mode_address[0].strip()
        if (not self.dev_mode and mode == "zmq_tcp"):
            for key in config[self.topic]:
                if config[self.topic][key] is None:
                    raise ValueError("Invalid Config")

        msgbus = mb.MsgbusContext(config)
        subscriber = msgbus.new_subscriber(self.topic)
        if self.monitor_mode:
            while not self.done_receiving:
                md, fr = subscriber.recv()
                md['ts_vp_sub'] = int(round(time.time()*1000))
                self.add_profile_data(md)
                for keys in md.keys():
                    for di_keys in dict_of_keys.keys():
                        if(di_keys in keys):
                            logger.critical(dict_of_keys[di_keys])
        elif self.fps_mode:
            while not self.done_receiving:
                md, fr = subscriber.recv()
                self.calculate_fps()
                # Discarding both the meta-data & frame
                del md
                del fr
        subscriber.close()
        return

    def prepare_per_frame_stats(self, metadata):
        """ Method to calculate per frame time metrics

        :param per_frame_stats: Topic name
        :type per_frame_stats: dict
        """
        per_frame_stats = dict()
        VI_time_to_push_to_queue = \
            metadata["ts_filterQ_exit"] - metadata["ts_filterQ_entry"]
        e2e = metadata["ts_vp_sub"] - metadata["ts_Ingestor_entry"]
        per_frame_stats['VI_time_to_push_to_queue'] = \
            VI_time_to_push_to_queue
        per_frame_stats["e2e"] = e2e
        for key in metadata:
            if 'entry' in key and 'Ingestor' not in key and\
               'filter' not in key and 'e2e' not in key:
                temp = key.split("_entry")[0]
                per_frame_stats[temp + "_diff"] = metadata[temp+"_exit"] -\
                    metadata[temp+"_entry"]

        if 'VideoAnalytics_subscriber_ts' in metadata:
            # VI-VA enabled scenario
            per_frame_stats['VI_to_VA_and_zmq_wait_diff'] = \
                metadata['VideoAnalytics_subscriber_ts'] -\
                metadata['VideoIngestion_publisher_ts']
            per_frame_stats['VA_to_profiler_and_zmq_wait_diff'] = \
                metadata['ts_vp_sub'] -\
                metadata['VideoAnalytics_publisher_ts']
        else:
            # Only VI scenario
            per_frame_stats['VI_profiler_transfer_time_diff'] = \
                metadata['ts_vp_sub'] -\
                metadata['VideoIngestion_publisher_ts']
        if ('VideoAnalytics_first' in key for key in metadata) and\
           ('VideoIngestion_first' in key for key in metadata):
            va_temp = None
            vi_temp = None
            for key in metadata:
                if 'VideoAnalytics_first' in key:
                    va_temp = key.split("VideoAnalytics_first")[0]
                if 'VideoIngestion_first' in key:
                    vi_temp = key.split("VideoIngestion_first")[0]
                if va_temp is not None and vi_temp is not None:
                    break
            if vi_temp is not None:
                per_frame_stats['VI_UDF_input_queue_time_spent_diff'] =\
                    metadata[vi_temp+'VideoIngestion_first_entry'] -\
                    metadata['ts_filterQ_exit']
            if 'VideoAnalytics_subscriber_blocked_ts' in metadata and\
               va_temp is not None:
                per_frame_stats['VA_UDF_input_queue_time_spent_diff'] =\
                    metadata[va_temp+'VideoAnalytics_first_entry'] -\
                    metadata['VideoAnalytics_subscriber_blocked_ts']
            elif 'VideoAnalytics_subscriber_ts' in metadata and\
                 va_temp is not None:
                per_frame_stats['VA_UDF_input_queue_time_spent_diff'] =\
                    metadata[va_temp+'VideoAnalytics_first_entry'] -\
                    metadata['VideoAnalytics_subscriber_ts']

        return per_frame_stats

    def prepare_avg_stats(self, per_frame_stats):
        """ Method to calculate average metrics
            for the pipeline

        :param per_frame_stats: dict of frame metrics
        :type per_frame_stats: dict
        """
        if self.start_subscribing:
            for key in per_frame_stats:
                temp = key.split("_diff")[0]
                self.total_records[temp + '_total'] = 0

        for key in per_frame_stats:
            if '_diff' in key:
                temp = key.split("_diff")[0]
                self.total_records[temp + '_total'] =\
                    self.total_records[temp + '_total'] +\
                    per_frame_stats[temp + '_diff']

        self.VI_time_to_push_to_queue += \
            per_frame_stats['VI_time_to_push_to_queue']
        avg_VI_time_to_push_to_queue = \
            self.VI_time_to_push_to_queue / self.frame_count

        self.e2e += per_frame_stats["e2e"]
        avg_e2e = self.e2e / self.frame_count

        avg_stats = dict()
        for key in self.total_records:
            if '_total' in key:
                temp = key.split("_total")[0]
                avg_stats[temp + '_avg'] =\
                    int(self.total_records[temp + '_total']) / self.frame_count

        avg_stats["avg_VI_time_to_push_to_queue"] = \
            avg_VI_time_to_push_to_queue
        avg_stats["avg_e2e"] = avg_e2e
        avg_stats.pop('VI_time_to_push_to_queue_avg', None)
        avg_stats.pop('e2e_avg', None)
        return avg_stats

    def add_profile_data(self, metadata):
        """ Method to calculate frame rate

        :param metadata: Topic name
        :type metadata: dict
        """
        self.frame_count += 1
        if self.frame_count == self.total_frames:
            self.done_receiving = True
        per_frame_stats = self.prepare_per_frame_stats(metadata)
        avg_value = self.prepare_avg_stats(per_frame_stats)

        csv_writer = None
        if self.start_subscribing and self.export_to_csv:
            # File to write meta-data at runtime
            csv_file = open('video_profiler_runtime_stats.csv', 'w')
            csv_writer = csv.writer(csv_file)
        elif self.export_to_csv:
            csv_file = open('video_profiler_runtime_stats.csv', 'a')
            csv_writer = csv.writer(csv_file)

        if self.export_to_csv:
            if self.monitor_mode_settings['avg_stats']:
                # If only avg_stats is true, write avg_stats to csv
                # and print per_frame_stats or metadata based on their
                # respective keys set to true
                if self.start_subscribing:
                    csv_writer.writerow(avg_value.keys())
                    self.start_subscribing = False
                csv_writer.writerow(avg_value.values())
                if self.monitor_mode_settings['per_frame_stats']:
                    logger.info(f'Per frame stats'
                                ' in miliseconds: {per_frame_stats}')
                if self.monitor_mode_settings['display_metadata']:
                    logger.info(f'Meta data is: {metadata}')
            elif self.monitor_mode_settings['per_frame_stats']:
                # If only per_frame_stats is true, write per_frame_stats to csv
                # and print metadata if its key is set to true
                if self.start_subscribing:
                    csv_writer.writerow(per_frame_stats.keys())
                    self.start_subscribing = False
                csv_writer.writerow(per_frame_stats.values())
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
            if self.monitor_mode_settings['per_frame_stats']:
                logger.info(f'Per frame stats '
                            'in miliseconds: {per_frame_stats}')
            if self.monitor_mode_settings['avg_stats']:
                logger.info(f'Frame avg stats in miliseconds: {avg_value}')

        if self.export_to_csv:
            csv_file.close()
        if self.done_receiving:
            global monitor_mode_results
            monitor_mode_results = avg_value

    def calculate_fps(self):
        """ Method to calculate FPS of provided stream """
        # Setting timestamp after first frame receival
        if self.start_subscribing:
            self.start_time = datetime.datetime.now()
            self.start_subscribing = False

        # Incrementing frame count
        self.frame_count += 1

        # Check if all frames are received
        if self.frame_count == self.total_frames:
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


def invoke_gc():
    """Method to invoke gc manually
        to avoid memory bloats
    """
    while True:
        gc.enable()
        gc.collect(generation=2)
        time.sleep(3)


def thread_runner(topic, config_dict):
    """Start VideoProfiler for every topic

    :param topic: Topic name
    :type topic: str
    :param config_dict: config required for Video Profiler
    :type config_dict: dict
    """
    fps_app = VideoProfiler(topic,
                            config_dict)
    fps_app.eisSubscriber()


if __name__ == "__main__":
    """Main method
    """

    config_dict = get_config()

    if config_dict['dev_mode']:
        fmt_str = ('%(asctime)s : %(levelname)s  : {}'
                   ': %(name)s : [%(filename)s] :' .format("Insecure Mode") +
                   '%(funcName)s : in line : [%(lineno)d] : %(message)s')
    else:
        fmt_str = ('%(asctime)s : %(levelname)s : %(name)s'
                   ': [%(filename)s] :' + '%(funcName)s : in line'
                   ': [%(lineno)d] : %(message)s')

    logging.basicConfig(level=logging.DEBUG, format=fmt_str)

    topics = config_dict['SubTopics']
    export_to_csv = config_dict['export_to_csv']
    total_frames = config_dict['total_number_of_frames']

    gc_thread = threading.Thread(target=invoke_gc)
    gc_thread.start()

    # Calculating FPS for each topic
    threads = []
    for topic in topics:
        thread = threading.Thread(target=thread_runner,
                                  args=(topic, config_dict, ))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    # Calculating overall fps for all topics
    final_fps = 0.0
    for topic in avg_fps_per_topic.keys():
        final_fps += avg_fps_per_topic[topic]

    if export_to_csv:
        csv_columns = ['Stream Name', 'Average FPS']
        avg_fps_per_topic['Total Fps'] = final_fps
        try:
            if config_dict['mode'] == 'monitor':
                # Generating excel sheet for monitor_mode
                with open('VP_Results.csv', 'w') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(csv_columns)
                    for key, value in avg_fps_per_topic.items():
                        writer.writerow([key, value])
                    writer.writerow('\n')
                    for key, value in monitor_mode_results.items():
                        writer.writerow([key, value])
                logger.info('Check VP_Results.csv file for results...')
            if config_dict['mode'] == 'fps':
                # Generating excel sheet for FPS mode
                with open('FPS_Results.csv', 'w') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(csv_columns)
                    for key, value in avg_fps_per_topic.items():
                        writer.writerow([key, value])
                logger.info('Check FPS_Results.csv file for results...')
        except IOError:
            logger.error("I/O error")
    else:
        if config_dict['mode'] == 'fps':
            logger.info('Average FPS for each topic {0}'
                        .format(avg_fps_per_topic))
            logger.info('Total FPS for {0} frames {1}'
                        .format(total_frames,
                                final_fps))
        if config_dict['mode'] == 'monitor':
            logger.info('Monitor mode results {}'
                        .format(monitor_mode_results))

    # Exiting after metrics are calculated
    os._exit(-1)
