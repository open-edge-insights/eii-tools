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

import queue
import threading
import imagestore_client
import time
import json
import influxdbconnector_client
import common
import sys
import os
import logging
import cfgmgr.config_manager as cfg

logger = logging.getLogger()


def main():
    try:
        ctx = cfg.ConfigMgr()
        app_name = ctx.get_app_name()
        dev_mode = ctx.is_dev_mode()
        app_cfg = ctx.get_app_config()
    except Exception as e:
        logger.error("{}".format(e))

    if dev_mode:
        fmt_str = ('%(asctime)s : %(levelname)s  : {} : %(name)s \
                   : [%(filename)s] :'.format("Insecure Mode") +
                   '%(funcName)s : in line : [%(lineno)d] : %(message)s')
    else:
        fmt_str = ('%(asctime)s : %(levelname)s : %(name)s \
                   : [%(filename)s] :' +
                   '%(funcName)s : in line : [%(lineno)d] : %(message)s')

    logging.basicConfig(format=fmt_str, level=logging.DEBUG)
    query = app_cfg["query"]
    img_handle_queue = queue.Queue(maxsize=10000)

    # This thread will retrieve the image from imagestore service
    # and will store into frames directory
    condition = threading.Condition()
    img_query_thread = threading.Thread(
        target=imagestore_client.retrieve_image_frames,
        args=(ctx, query, img_handle_queue, condition))
    img_query_thread.start()

    influx_query_thread = threading.Thread(
        target=retrieve_measurement_data,
        args=(ctx, query, img_handle_queue, condition))
    influx_query_thread.start()

    influx_query_thread.join()
    logger.info("Influx query processing done")
    img_query_thread.join()
    logger.info("Retrieved all the frames exiting....")
    sys.exit(0)


def retrieve_measurement_data(ctx, query, img_handle_queue, condition):
    influxdbconnector_client.query_influxdb(
        ctx, query, img_handle_queue, condition)
    imagestore_client.influxdb_query_done = True


if __name__ == "__main__":
    main()
