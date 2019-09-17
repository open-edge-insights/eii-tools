# Copyright (c) 2019 Intel Corporation.
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
import eis.msgbus as mb
import common

msgbus = None
service = None
logging.basicConfig(level=logging.DEBUG)
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
def query_influxdb(eis_config,query_config,img_handle_queue):
    try:
        logger.info(f'[INFO] Initializing message bus context')
        msgbus = mb.MsgbusContext(eis_config)
        logger.info('[INFO] Initializing service for topic \'{"influxconnector_service"}\'')
        service = msgbus.get_service("influxconnector_service")
        request = {'command':query_config["query"]}
        logger.info(f'[INFO] Running...')
        logger.info(f'[INFO] Sending request {request}')
        service.request(request)
        logger.info('[INFO] Waiting for response')
        response = service.recv()
        if len(response['Data']) > 0:
            loaded_json = json.loads(response['Data'])
            index = -1
            valid_input=['channel','defects','encoding_level','encoding_type','height','width']         
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
                        
                    img_handle_queue.put(temp_dict)
                    

            output_dir = "/output/" + "/" + "data"
            now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            filename = str(now) + ".dat"
            common.write_to_file(filename, str.encode(response['Data']), output_dir)

        service.close()     

    except KeyboardInterrupt:
        logger.info(f'[INFO] Quitting...')
        service.close()
