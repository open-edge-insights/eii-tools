from DataBusAbstraction.py.DataBus import databus
from ImageStore.client.py.client import GrpcImageStoreClient
import sys
import subprocess
import visualize as vi
import queue
import unittest
import os
import json
import time
import logging
import io


class CallbackTestCase(unittest.TestCase):
    """ Tests for visualize.py"""

    @classmethod
    def setUpClass(cls):
        with open('test/config.json') as config_file:
            config = json.load(config_file)
        root_ca_cert = os.path.join(config["cert_dir"], 'ca',
                                    'ca_certificate.pem')
        im_client_cert = os.path.join(config["cert_dir"], 'imagestore',
                                      'imagestore_client_certificate.pem')
        im_client_key = os.path.join(config["cert_dir"], 'imagestore',
                                     'imagestore_client_key.pem')
        db_cert = os.path.join(config["cert_dir"], 'opcua',
                               'opcua_client_certificate.der')
        db_priv = os.path.join(config["cert_dir"], 'opcua',
                               'opcua_client_key.der')
        db_trust = os.path.join(config["cert_dir"], 'ca', 'ca_certificate.der')

        frames = queue.Queue()

        try:
            output = subprocess.check_output(["hostname", "-I"])
            output = output.decode('utf-8')
            hostip = output.split(" ")[0]
        except Exception as err:
            print("Exception Occured in certificates generation" + str(err))

        im_client = GrpcImageStoreClient(im_client_cert, im_client_key,
                                         root_ca_cert, hostname=hostip)
        logger = logging.getLogger("test_visualize")
        cls.dc = vi.DatabusCallback(frames, im_client, logger,
                                    dir_name=config["d_name"])
        cls.ctx_config = {
            'endpoint': 'opcua://{0}:{1}'.format(hostip, 4840),
            'direction': 'SUB',
            'name': 'streammanager',
            'certFile': db_cert,
            'privateFile': db_priv,
            'trustFile': db_trust
        }
        cls.dbus = databus(logging.getLogger(__name__))

    def test_callback_logs_and_image(self):

        self.dbus.ContextCreate(self.ctx_config)
        topic_config = {'name': 'stream1_results', 'type': 'string'}
        capturedoutput = io.StringIO()
        self.dbus.Subscribe(topic_config, 'START',
                            self.dc.callback)
        sys.stdout = sys.__stdout__
        self.assertIsNotNone(capturedoutput.getvalue())
        time.sleep(5)

    @classmethod
    def tearDownClass(cls):
        cls.dbus.ContextDestroy()


if __name__ == '__main__':
    unittest.main()
