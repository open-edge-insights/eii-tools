"""Simple visualizer for images processed by ETA.
"""
import os
import time
import sys
import cv2
import json
import queue
import logging
import argparse
import numpy as np
from distutils.util import strtobool
from tkinter import *
from PIL import Image, ImageTk
import threading

# NOTE: You must update the PYTHONPATH environmental variable to have these
# in your Python environment
from DataBusAbstraction.py.DataBus import databus
from ImageStore.client.py.client import GrpcImageStoreClient


def get_config():
    with open('config.json') as f:
        config_dict = json.load(f)
        return config_dict


class DatabusCallback:
    """Object for the databus callback to wrap needed state variables for the
    callback in to IEI.
    """
    def __init__(self, topicQueueDict, im_client, logger, profiling,
                 labels=None, good_color=(0, 255, 0),
                 bad_color=(0, 0, 255), dir_name=None, display=None):
        """Constructor

        :param frame_queue: Queue to put frames in as they become available
        :type: queue.Queue
        :param im_client: Image store client
        :type: GrpcImageStoreClient
        :param labels: (Optional) Label mapping for text to draw on the frame
        :type: dict
        :param good_color: (Optional) Tuple for RGB color to use for outlining
            a good image
        :type: tuple
        :param bad_color: (Optional) Tuple for RGB color to use for outlining a
            bad image
        :type: tuple
        """
        self.topicQueueDict = topicQueueDict
        self.im_client = im_client
        self.logger = logger
        self.labels = labels
        self.good_color = good_color
        self.bad_color = bad_color
        self.dir_name = dir_name
        self.display = display

        self.profiling = profiling
        self.logger.debug(f'Profiling is : {self.profiling}')

        self.curr_frame = 0
        self.ts_iev_fps_vi = 0.0
        self.ts_iev_img_write = 0.0

        self.ts_iev_fps_va = 0.0
        self.ts_iev_va_avg_wait = 0.0
        self.ts_iev_va_algo = 0.0
        self.ts_iev_img_read = 0.0

        self.ts_iev_total_proc = 0.0
        self.ts_da_to_visualizer = 0.0
        self.ts_va_to_da = 0.0

    def queue_publish(self, topic, frame):
        """queue_publish called after defects bounding box is drawn
        on the image. These images are published over the queue.

        :param topic: Topic the message was published on
        :type: str
        :param frame: Images with the bounding box
        :type: numpy.ndarray
        :param topicQueueDict: Dictionary to maintain multiple queues.
        :type: dict
        """

        for key in self.topicQueueDict:
            if(key == topic):
                self.topicQueueDict[key].put_nowait(frame)

    def draw_defect(self, topic, msg):
        """Identify the defects and draw boxes on the frames

        :param topic: Topic the message was published on
        :type: str
        :param msg: Message received on the given topic (JSON blob)
        :type: str
        """
        self.logger.info(f'Received message: {msg}')
        results = json.loads(msg)

        img_handle = results['ImgHandle']
        height = int(results['Height'])
        width = int(results['Width'])
        channels = int(results['Channels'])

        if 'encoding' in results:
            encoding = results['encoding']
        else:
            encoding = None

        # Read frame from Image Store
        self.logger.info(f'Reteiving frame from Image Store: {img_handle}')
        blob = self.im_client.Read(img_handle)

        # Convert to Numpy array and reshape to frame
        self.logger.info('Preparing frame for visualization')
        frame = np.frombuffer(blob, dtype=np.uint8)
        if encoding is not None:
            frame = np.reshape(frame, (frame.shape))
            frame = cv2.imdecode(frame, 1)
        else:
            frame = np.reshape(frame, (height, width, channels))

        # Draw defects
        defects = json.loads(results['defects'])

        for d in defects:
            # Get tuples for top-left and bottom-right coordinates
            tl = tuple(d['tl'])
            br = tuple(d['br'])

            # Draw bounding box
            cv2.rectangle(frame, tl, br, self.bad_color, 2)

            # Draw labels for defects if given the mapping
            if self.labels is not None:
                # Position of the text below the bounding box
                pos = (tl[0], br[1] + 20)

                # The label is the "type" key of the defect, which is converted
                # to a string for getting from the labels
                label = self.labels[str(d['type'])]

                cv2.putText(frame, label, pos, cv2.FONT_HERSHEY_DUPLEX,
                            0.5, self.bad_color, 2, cv2.LINE_AA)

        # Draw border around frame if has defects or no defects
        if defects:
            outline_color = self.bad_color
        else:
            outline_color = self.good_color

        frame = cv2.copyMakeBorder(frame, 5, 5, 5, 5, cv2.BORDER_CONSTANT,
                                   value=outline_color)

        # Display information about frame
        display_info = json.loads(results['display_info'])
        (dx, dy) = (20, 10)
        for d_i in display_info:
            # Get priority
            priority = d_i['priority']
            info = d_i['info']
            dy = dy + 10

            #  LOW
            if priority == 0:
                cv2.putText(frame, info, (dx, dy), cv2.FONT_HERSHEY_DUPLEX,
                            0.5, (0, 255, 0), 1, cv2.LINE_AA)
            #  MEDIUM
            if priority == 1:
                cv2.putText(frame, info, (dx, dy), cv2.FONT_HERSHEY_DUPLEX,
                            0.5, (0, 150, 170), 1, cv2.LINE_AA)
            #  HIGH
            if priority == 2:
                cv2.putText(frame, info, (dx, dy), cv2.FONT_HERSHEY_DUPLEX,
                            0.5, (0, 0, 255), 1, cv2.LINE_AA)

        if self.dir_name:
            self.save_image(topic, msg, frame)

        if self.display.lower() == 'true':
            self.queue_publish(topic, frame)
        else:
            self.logger.info(f'Classifier_results: {msg}')

    def save_image(self, topic, msg, frame):
        results = json.loads(msg)
        img_handle = results['ImgHandle']
        defects = json.loads(results['defects'])
        if defects:
            tag = 'bad'
        else:
            tag = 'good'
        imgname = tag + '_' + img_handle + ".png"
        cv2.imwrite(os.path.join(self.dir_name, imgname),
                    frame,
                    [cv2.IMWRITE_PNG_COMPRESSION, 3])

    def callback(self, topic, msg):
        """Callback called when the databus has a new message.

        :param topic: Topic the message was published on
        :type: str
        :param msg: Message received on the given topic (JSON blob)
        :type: str
        """

        if self.profiling is True:
            msg = self.add_profile_data(msg)

        if self.dir_name or self.display.lower() == 'true':
            self.drawdefect_thread = threading.Thread(target=self.draw_defect,
                                                      args=(topic, msg, ))
            self.drawdefect_thread.start()

    @staticmethod
    def prepare_per_frame_stats(results):
        # Total time in vi + vi->va transfer
        vi_diff = results["ts_va_entry"] - \
            results["ts_vi_fr_store_entry"]

        vi_fr_encode = results["ts_vi_fr_encode_exit"] -\
            results["ts_vi_fr_encode_entry"]

        # Total time in img write
        vi_img_write_diff = results["ts_vi_fr_store_exit"] -\
            results["ts_vi_fr_store_entry"]

        # Total time in va
        va_diff = results["ts_va_analy_exit"] - \
            results["ts_va_entry"]

        va_wait = results["ts_va_proc_entry"] - \
            results["ts_va_img_read_exit"]

        # Time taken to read image in va
        va_img_read = results["ts_va_img_read_exit"] -\
            results["ts_va_img_read_entry"]

        va_algo_diff = results["ts_va_analy_exit"] -\
            results["ts_va_analy_entry"]

        va_np_proc_diff = results["ts_va_proc_np_exit"] -\
            results["ts_va_proc_np_entry"]

        va_np_reshape = results["ts_va_proc_np_reshape_exit"] - \
            results["ts_va_proc_np_reshape_entry"]

        va_to_da = results["ts_sm_pub_entry"] - \
            results["ts_va_analy_exit"]

        da_to_visualizer = results["ts_iev_entry"] -\
            results["ts_sm_pub_entry"]

        fps_diff = results["ts_iev_entry"] - \
            results["ts_vi_fr_store_entry"]

        per_frame_stats = dict()

        per_frame_stats["vi_and_vi_to_va"] = vi_diff
        per_frame_stats["vi_img_write"] = vi_img_write_diff
        per_frame_stats["vi_fr_encode"] = vi_fr_encode
        per_frame_stats["va_total"] = va_diff
        per_frame_stats["va_np_proc_diff"] = va_np_proc_diff
        per_frame_stats["va_np_reshape"] = va_np_reshape
        per_frame_stats["va_wait"] = va_wait
        per_frame_stats["va_img_read"] = va_img_read
        per_frame_stats["va_algo"] = va_algo_diff
        per_frame_stats["va_to_da"] = va_to_da
        per_frame_stats["da_to_visualizer"] = da_to_visualizer
        per_frame_stats["e2e"] = fps_diff

        return per_frame_stats

    def prepare_avg_stats(self, per_frame_stats, results):
        self.curr_frame = self.curr_frame + 1
        self.ts_iev_fps_vi += per_frame_stats["vi_and_vi_to_va"]
        ts_avg_vi = self.ts_iev_fps_vi/self.curr_frame

        self.ts_iev_img_write += per_frame_stats["vi_img_write"]
        ts_avg_vi_img_write = self.ts_iev_img_write/self.curr_frame

        self.ts_iev_fps_va += per_frame_stats["va_total"]
        ts_avg_va = self.ts_iev_fps_va / self.curr_frame

        self.ts_iev_va_avg_wait += per_frame_stats["va_wait"]
        ts_avg_va_wait = self.ts_iev_va_avg_wait / self.curr_frame

        self.ts_iev_img_read += per_frame_stats["va_img_read"]
        ts_avg_va_img_read = self.ts_iev_img_read / self.curr_frame

        self.ts_iev_va_algo += per_frame_stats["va_algo"]
        ts_avg_va_algo = self.ts_iev_va_algo / self.curr_frame

        self.ts_va_to_da += per_frame_stats["va_to_da"]
        ts_avg_va_to_da = self.ts_va_to_da / self.curr_frame

        self.ts_da_to_visualizer += per_frame_stats["da_to_visualizer"]
        ts_avg_da_to_visualizer = self.ts_da_to_visualizer / self.curr_frame

        fps_diff = results["ts_iev_entry"] - \
            results["ts_vi_fr_store_entry"]

        self.ts_iev_total_proc += fps_diff
        ts_avg_e2e = self.ts_iev_total_proc/self.curr_frame

        avg_stats = dict()
        avg_stats["avg_vi_and_vi_to_va"] = ts_avg_vi
        avg_stats["avg_vi_img_write"] = ts_avg_vi_img_write
        avg_stats["avg_va_total"] = ts_avg_va
        avg_stats["avg_va_wait"] = ts_avg_va_wait
        avg_stats["avg_va_img_read"] = ts_avg_va_img_read
        avg_stats["avg_va_algo"] = ts_avg_va_algo
        avg_stats["ts_avg_va_to_da"] = ts_avg_va_to_da
        avg_stats["ts_avg_da_to_visualizer"] = ts_avg_da_to_visualizer
        avg_stats["avg_e2e"] = ts_avg_e2e

        return avg_stats

    def add_profile_data(self, msg):
        results = json.loads(msg)
        results["ts_iev_entry"] = float(time.time()*1000)
        diff = int(results["ts_iev_entry"]) - \
            int(results["ts_vi_fr_store_entry"])
        results["ts_iev_e2e"] = float(diff)

        per_frame_stats = DatabusCallback.prepare_per_frame_stats(results)
        avg_value = self.prepare_avg_stats(per_frame_stats, results)

        self.logger.info(f'==========STATS START==========')
        self.logger.info(f'Per frame stats: {per_frame_stats}')
        self.logger.info(f'frame avg stats: {avg_value}')
        self.logger.info(f'==========STATS END==========')

        return json.dumps(results)


def parse_args():
    """Parse command line arguments.
    """
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument('-c', '--cert_dir', default=None,
                    help='IEI certificates directory')
    ap.add_argument('-host', '--host', default='localhost',
                    help='Hosts IP address')
    ap.add_argument('-p', '--port', type=int, default=4840,
                    help='ETA databus port')
    ap.add_argument('-f', '--fullscreen', default=False, action='store_true',
                    help='Start visualizer in fullscreen mode')
    ap.add_argument('-l', '--labels', default=None,
                    help='JSON file mapping the defect type to labels')
    ap.add_argument('-d', '--display', default='true',
                    help='live preview of classified images(true/false)')
    ap.add_argument('-i', '--image_dir', default=None,
                    help='directory name to save the images')
    ap.add_argument('-D', '--dev_mode', default='false',
                    help='dev_mode can be true or false')
    ap.add_argument('-P', '--profiling_mode', default='false',
                    help='profiling_mode can be true or false')

    return ap.parse_args()


def assert_exists(path):
    """Assert given path exists.

    :param path: Path to assert
    :type: str
    """
    assert os.path.exists(path), 'Path: {} does not exist'.format(path)


def get_logger(name):
    """gets the logger object.

    :param name: module name
    :type: str
    """
    fmt_str = ('%(asctime)s : %(levelname)s : %(name)s : [%(filename)s] :' +
               '%(funcName)s : in line : [%(lineno)d] : %(message)s')
    base_log = os.path.join(
               os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'visualize.log'))
    # Do basic configuration of logging (just for stdout config)
    logging.basicConfig(format=fmt_str, level=logging.DEBUG)

    logger = logging.getLogger("visualize")

    fh = logging.FileHandler(base_log)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt_str)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

# TODO: Enlarge individual frame on respective bnutton click

# def button_click(rootWin, frames, key):
#     topRoot=Toplevel(rootWin)
#     topRoot.title(key)

#     while True:
#         frame=frames.get()

#         img=Image.fromarray(frame)
#         image= ImageTk.PhotoImage(image=img)

#         lbl=Label(topRoot,image=image)
#         lbl.grid(row=0, column=0)
#         topRoot.update()


def main(args):
    """Main method.
    """
    # WIndow name to be used later
    window_name = 'EIS Visualizer App'

    # If user provides labels, read them in
    if args.labels is not None:
        assert_exists(args.labels)
        with open(args.labels, 'r') as f:
            labels = json.load(f)
    else:
        labels = None

    # If user provides image_dir, create the directory if don't exists
    if args.image_dir:
        if not os.path.exists(args.image_dir):
            os.mkdir(args.image_dir)

    app_config = get_config()
    topicsList = app_config['output_streams']
    queueDict = {}

    for topic in topicsList:
        queueDict[topic] = queue.Queue()

    logger = get_logger(__name__)

    args.dev_mode = bool(strtobool(args.dev_mode))
    args.profiling_mode = bool(strtobool(args.profiling_mode))

    if not args.dev_mode and args.cert_dir is None:
        logger.error("Kindly Provide certificate directory(--cert_dir)"
                     " when security mode is True")
        sys.exit(1)

    # Check for the requirement of im_client
    need_im_handle = False
    im_client = None

    if args.image_dir or args.display.lower() == 'true':
        logger.debug("Requires IM client ")
        need_im_handle = True
    else:
        logger.debug("IM client not required")

    # Initilize image store client
    if args.dev_mode:
        if need_im_handle:
            im_client = GrpcImageStoreClient(hostname=args.host)
    else:
        # Certificates
        root_ca_cert = os.path.join(args.cert_dir, 'ca', 'ca_certificate.pem')
        im_client_cert = os.path.join(args.cert_dir, 'imagestore',
                                      'imagestore_client_certificate.pem')
        im_client_key = os.path.join(args.cert_dir, 'imagestore',
                                     'imagestore_client_key.pem')
        db_cert = os.path.join(args.cert_dir, 'opcua',
                               'opcua_client_certificate.der')
        db_priv = os.path.join(args.cert_dir, 'opcua',
                               'opcua_client_key.der')
        db_trust = os.path.join(args.cert_dir, 'ca', 'ca_certificate.der')

        logger.info("cert path is: {0}".format(args.cert_dir))

        # Verify all certificates exist
        assert_exists(args.cert_dir)
        assert_exists(root_ca_cert)
        assert_exists(im_client_cert)
        assert_exists(im_client_key)
        assert_exists(db_cert)
        assert_exists(db_priv)
        assert_exists(db_trust)
        if need_im_handle:
            im_client = GrpcImageStoreClient(im_client_cert, im_client_key,
                                             root_ca_cert, hostname=args.host)

    # Initialize IEI databus callback
    dc = DatabusCallback(queueDict, im_client, logger, args.profiling_mode,
                         labels=labels, dir_name=args.image_dir,
                         display=args.display)

    # Initalize IEI databus
    if args.dev_mode:
        ctx_config = {
            'endpoint': 'opcua://{0}:{1}'.format(args.host, args.port),
            'direction': 'SUB',
            'certFile': "",
            'privateFile': "",
            'trustFile': ""
        }
    else:
        ctx_config = {
            'endpoint': 'opcua://{0}:{1}'.format(args.host, args.port),
            'direction': 'SUB',
            'certFile': db_cert,
            'privateFile': db_priv,
            'trustFile': db_trust
        }

    logger.info("ctx_config: {0}".format(ctx_config))
    dbus = databus(logging.getLogger(__name__))
    dbus.ContextCreate(ctx_config)
    topicConfigs = []
    for topic in topicsList:
        topicConfigs.append({"ns": "streammanager",
                             "name": topic,
                             "dType": "string"})

    dbus.Subscribe(topicConfigs, len(topicConfigs), 'START', dc.callback)

    if args.display.lower() == 'true':

        try:
            rootWin = Tk()
            buttonDict = {}
            imageDict = {}

            WINDOW_WIDTH = 600
            WINDOW_HEIGHT = 600
            windowGeometry = str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT)

            rootWin.geometry(windowGeometry)
            rootWin.title(window_name)

            columnValue = len(topicsList)//2
            rowValue = len(topicsList) % 2

            heightValue = int(WINDOW_HEIGHT/(rowValue+1))
            widthValue = int(WINDOW_WIDTH/(columnValue+1))

            blankImageShape = (300, 300, 3)
            blankImage = np.zeros(blankImageShape, dtype=np.uint8)

            text = 'Disconnected'
            textPosition = (20, 250)
            textFont = cv2.FONT_HERSHEY_PLAIN
            textColor = (255, 255, 255)

            cv2.putText(blankImage, text, textPosition, textFont, 2,
                        textColor, 2, cv2.LINE_AA)

            blankimg = Image.fromarray(blankImage)

            for buttonCount in range(len(topicsList)):
                buttonStr = "button{}".format(buttonCount)
                imageDict[buttonStr] = []
                imageDict[buttonStr].append(ImageTk.PhotoImage(image=blankimg))

            buttonCount, rowCount, columnCount = 0, 0, 0
            if(len(topicsList) == 1):
                heightValue = WINDOW_HEIGHT
                widthValue = WINDOW_WIDTH
                buttonDict[str(buttonCount)] = Button(rootWin,
                                                      text=topicsList[0])
                buttonDict[str(buttonCount)].grid(sticky='NSEW')
                Grid.rowconfigure(rootWin, 0, weight=1)
                Grid.columnconfigure(rootWin, 0, weight=1)
            else:
                for key in queueDict:
                    buttonDict[str(buttonCount)] = Button(rootWin, text=key)

                    if(columnCount > columnValue):
                        rowCount = rowCount+1
                        columnCount = 0

                    if rowCount > 0:
                        heightValue = int(WINDOW_HEIGHT/(rowCount+1))
                        for key2 in buttonDict:
                            buttonDict[key2].config(height=heightValue,
                                                    width=widthValue)
                    else:
                        for key2 in buttonDict:
                            buttonDict[key2].config(height=heightValue,
                                                    width=widthValue)

                    buttonDict[str(buttonCount)].grid(row=rowCount,
                                                      column=columnCount,
                                                      sticky='NSEW')
                    Grid.rowconfigure(rootWin, rowCount, weight=1)
                    Grid.columnconfigure(rootWin, columnCount, weight=1)

                    buttonCount = buttonCount + 1
                    columnCount = columnCount + 1

            rootWin.update()

            while True:
                buttonCount = 0
                for key1 in queueDict:
                    try:
                        frame = queueDict[key1].get_nowait()
                        img = Image.fromarray(frame)
                        blue, green, red = img.split()
                        img = Image.merge("RGB", (red, green, blue))
                        imgwidth, imgheight = img.size

                        aspect_ratio = (imgwidth/imgheight) + 0.1

                        resized_width = buttonDict[
                                        str(buttonCount)].winfo_width()

                        resized_height = round(buttonDict[
                                str(buttonCount)].winfo_width()/aspect_ratio)

                        resized_img = img.resize((resized_width,
                                                  resized_height))

                        imageDict["button"+str(buttonCount)].append(
                                        ImageTk.PhotoImage(image=resized_img))

                        imagedictList = len(
                                        imageDict["button"+str(buttonCount)])

                        buttonDict[str(buttonCount)].config(
                            image=imageDict["button" +
                                            str(buttonCount)][imagedictList-1],
                            compound=BOTTOM)
                    except Exception:
                        imagedictList = len(
                                        imageDict["button"+str(buttonCount)])

                        buttonDict[str(buttonCount)].config(
                            image=imageDict["button" +
                                            str(buttonCount)][imagedictList-1],
                            compound=BOTTOM)
                        pass
                    buttonCount = buttonCount + 1
                rootWin.update()
        except KeyboardInterrupt:
            logger.info('Quitting...')
        except Exception:
            logger.exception('Error during execution:')
        finally:
            logger.exception('Destroying IEI databus context')
            dbus.ContextDestroy()
            os._exit(1)


if __name__ == '__main__':

    # Parse command line arguments
    args = parse_args()
    main(args)
