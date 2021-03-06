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

"""Retrieve data from InfluxDB and put it in a queue.
   Write the recieved data into a File.
"""

from datetime import datetime
import json
import logging
import queue
import threading
import imagestore_client
import argparse
import eii.msgbus as mb
import common
import os

msgbus = None
service = None

logger = logging.getLogger()


def query_influxdb(ctx, query, img_handle_queue, condition):
    try:
        logger.info(f'Initializing message bus context')
        client_ctx = ctx.get_client_by_index(0)
        config = client_ctx.get_msgbus_config()
        interface_value = client_ctx.get_interface_value("Name")
        msgbus = mb.MsgbusContext(config)
        logger.info(
            'Initializing service for topic \'{"influxconnector_service"}\'')
        service = msgbus.get_service(interface_value)
        request = {'command': query}
        logger.info(f'Running...')
        logger.info(f'Sending request {request}')
        service.request(request)
        logger.info('Waiting for response')
        response, _ = service.recv()
        if len(response['Data']) > 0:
            loaded_json = json.loads(response['Data'])
            index = -1
            valid_input = ['channels',
                           'defects',
                           'encoding_level',
                           'encoding_type',
                           'height',
                           'width']
            check = all(item in loaded_json['columns'] for item in valid_input)
            if check is True:
                for key in loaded_json['columns']:
                    if key == "img_handle":
                        index = (loaded_json['columns'].index(key))
            if index >= 0:
                for elm in loaded_json['values']:
                    temp_dict = dict()
                    count = 0
                    for key in loaded_json['columns']:
                        temp_dict[key] = elm[count]
                        count = count + 1

                    is_queue_empty = img_handle_queue.empty()
                    img_handle_queue.put(temp_dict)
                    if is_queue_empty:
                        with condition:
                            condition.notifyAll()

            output_dir = "/output" + "/" + "data"
            now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            filename = str(now) + ".dat"
            common.write_to_file(filename,
                                 str.encode(response['Data']),
                                 output_dir)
        with condition:
            condition.notifyAll()

        service.close()
    except KeyboardInterrupt:
        logger.info(f' Quitting...')
        service.close()
