#!/usr/bin/python3

# Copyright (c) 2020 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import json
import subprocess
import argparse
import os
import inspect
import etcd3
import logging
from jsonschema import validate
logging.basicConfig(level=logging.INFO, format='%(message)s')


def make_pipeline(pfs_config_map, config_table):
    """Building pipeline for gstreamer

    :param pfs_config_map: Mapping between pfs file and config.json
    :type pfs_config_map: Dict
    :param config_table: Contents of config.json for specified plugin
    :type : Dict
    :return: gstreamer_pipeline
    :rtype: String
    """
    gstreamer_pipeline = config_table["plugin_name"] + " "
    if "device_serial_number" in config_table:
        gstreamer_pipeline += "serial=" + \
                              config_table["device_serial_number"] + " "
    video_raw = ""
    if "mono" in pfs_config_map["pixel-format"]:
        pfs_config_map["pixel-format"] = "mono8"
    elif "yuv411" in pfs_config_map["pixel-format"]:
        pfs_config_map["pixel-format"] = "ycbcr411_8"
    elif "yuv422" in pfs_config_map["pixel-format"]:
        pfs_config_map["pixel-format"] = "ycbcr422_8"
    elif "rgb" in pfs_config_map["pixel-format"]:
        pfs_config_map["pixel-format"] = "rgb8"
    elif "bgr" in pfs_config_map["pixel-format"]:
        pfs_config_map["pixel-format"] = "bgr8"
    elif "bayer" in pfs_config_map["pixel-format"]:
        if "bayerrg" in pfs_config_map["pixel-format"]:
            pfs_config_map["pixel-format"] = "bayerrggb"
        elif "bayerbg" in pfs_config_map["pixel-format"]:
            pfs_config_map["pixel-format"] = "bayerbggr"
        elif "bayergr" in pfs_config_map["pixel-format"]:
            pfs_config_map["pixel-format"] = "bayergrbg"
        elif "bayergb" in pfs_config_map["pixel-format"]:
            pfs_config_map["pixel-format"] = "bayergbrg"
        else:
            logging.info("{} bayer format not supported".format(
                         pfs_config_map["pixel-format"]))
        video_raw = "bayer2rgb !"
    else:
        logging.info("{} pixel-format not supported".format(
                     pfs_config_map["pixel-format"]))
    for key, value in pfs_config_map.items():
        gstreamer_pipeline += key+"="+value+" "
    gstreamer_pipeline += "! "
    # Building pipeline
    gstreamer_pipeline += video_raw + " " + config_table["pipeline_constant"]
    return gstreamer_pipeline


def pfs_file_parser(pfs_file, config_table):
    """Mapping pfs to config properties

    :param pfs: Contents of pfs file
    :type pfs: Dict
    :param config_table: Contents of config.json
    :type config_table: Dict
    :return: pfs_config_map
    :rtype: Dict
    """
    pfs_config_map = {}
    look_up_table = config_table["plugin_properties"]
    look_up_table = dict((str(key).lower(), str(value).lower())
                         for key, value in look_up_table.items())
    # Processing pfs file
    with open(pfs_file) as fr:
        for line in fr.readlines():
            line = line.split("\n")
            value = line[0].split("\t")
            # Checking if pfs element present in config.json
            if(look_up_table.get(value[0].lower())):
                pfs_config_map[look_up_table.get(value[0].lower())]\
                    = value[-1].lower()
    return pfs_config_map


def etcd_config(hostname, port, ca_cert, root_key, root_cert):
    """Creates an EtcdCli instance, checks for
        the etcd service port availability

    :param hostname: Etcd host IP name
    :type hostname: String
    :param port: Etcd host port
    :type port: String
    :param ca_cert: Path of ca_certificate.pem
    :type ca_cert: String
    :param root_key: Path of root_client_key.pem
    :type root_key: String
    :param root_cert: Path of root_client_certificate.pem
    :type root_cert: String
    :return: etcd
    :rtype: etcd3.client()
    """
    if(len(hostname) == 0):
        hostname = "localhost"

    if(len(port) == 0):
        port = "2379"

    try:
        if ca_cert is None and root_key is None and root_cert is None:
            etcd = etcd3.client(host=hostname, port=port)
        else:
            etcd = etcd3.client(host=hostname, port=port,
                                ca_cert=ca_cert,
                                cert_key=root_key,
                                cert_cert=root_cert)
    except Exception as e:
        sys.exit("Exception raised when creating etcd \
                client instance with error:{}".format(e))
    return etcd


if __name__ == '__main__':
    my_parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Tool for updating pipeline according to\
                          user requirements"
    )
    my_parser.add_argument(
        '--pfs_file', '-f', action='store', required=True,
        help="To process pfs file genrated by PylonViwerApp"
    )
    my_parser.add_argument(
        '--etcd', '-e', action='store_true',
        help="Set for updating etcd config"
    )
    my_parser.add_argument(
        '--ca_cert', '-c', action='store', default=None,
        help="Provide path of ca_certificate.pem"
    )
    my_parser.add_argument(
        '--root_key', '-r_k', action='store', default=None,
        help="Provide path of root_client_key.pem"
    )
    my_parser.add_argument(
        '--root_cert', '-r_c', action='store', default=None,
        help="Provide path of root_client_certificate.pem"
    )
    my_parser.add_argument(
        '--app_name', '-a', action='store', default="VideoIngestion",
        help="For providing appname of VideoIngestion instance"
    )
    my_parser.add_argument(
        '--hostname', '-host', default='localhost',
        help='Etcd host IP'
    )
    my_parser.add_argument(
        '--port', '-port', default='2379',
        help='Etcd host port'
    )

    args = my_parser.parse_args()
    pfs_file = args.pfs_file
    etcd_flag = args.etcd
    ca_cert = args.ca_cert
    root_key = args.root_key
    root_cert = args.root_cert
    hostname = args.hostname
    port = args.port
    app_name = "/" + args.app_name+"/config"
    # Creates an EtcdCli instance
    etcd_client = etcd_config(hostname, port, ca_cert, root_key, root_cert)
    etcd_value = {}
    # Command to get etcd data
    if etcd_flag:
        try:
            cmd = etcd_client.get(app_name)
            etcd_value = json.loads(cmd[0].decode('utf-8'))
        except Exception as e:
            sys.exit("{}error in reading config from etcd".format(e))
    # Getting config.json data
    config_content = {}
    with open("config.json") as file_reader,\
            open("config.json") as file_check:
        try:
            config_content = json.load(file_reader)
            config_check = json.load(file_check)
            validate(instance=config_content, schema=config_check)
        except Exception as e:
            sys.exit("Exception raised in JSON schema validation \
                    with error: {}".format(e))
    # For extracting values from pfs file
    pfs_config_map = pfs_file_parser(pfs_file, config_content)
    # For creating new pipeline
    pipeline = make_pipeline(pfs_config_map, config_content)
    logging.info("\nGstreamer pipeline generated:\n{}".format(pipeline))
    # For modifing etcd config
    if(etcd_flag):
        etcd_value["ingestor"]["pipeline"] = pipeline
        etcd_value["ingestor"]["type"] = "gstreamer"
        etcd_value = json.dumps(etcd_value, sort_keys=True, indent=4)
        # Command to modify etcd
        try:
            status = etcd_client.put(app_name, etcd_value)
            logging.info("etcd successfully updated")
        except Exception as e:
            sys.exit("Exception raised in etcd put \
                with error:{}".format(e))
