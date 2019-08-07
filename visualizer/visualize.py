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
from libs.ConfigManager import ConfigManager
from libs.common.py.util import Util
import eis.msgbus as mb


class SubscriberCallback:
    """Object for the databus callback to wrap needed state variables for the
    callback in to IEI.
    """
    def __init__(self, topicQueueDict, logger, profiling,
                 labels=None, good_color=(0, 255, 0),
                 bad_color=(0, 0, 255), dir_name=None,
                 save_image=False, display=None):
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
        self.logger = logger
        self.labels = labels
        self.good_color = good_color
        self.bad_color = bad_color
        self.dir_name = dir_name
        self.save_image = bool(strtobool(save_image))
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
            if (key == topic):
                try:
                    self.topicQueueDict[key].put_nowait(frame)
                except queue.Full:
                    self.logger.error("Dropping frames as the queue is full")

    def draw_defect(self, topic, results, blob):
        """Identify the defects and draw boxes on the frames

        :param topic: Topic the message was published on
        :type: str
        :param results: Message received on the given topic (JSON blob)
        :type: str
        """
        self.logger.info(f'Received message: {results}')

        height = int(results['height'])
        width = int(results['width'])
        channels = int(results['channel'])
        encoding = None

        if 'encoding_type' and 'encoding_level' in results:
            encoding = {"type": results['encoding_type'],
                        "level": results['encoding_level']}
        # Convert to Numpy array and reshape to frame
        self.logger.info('Preparing frame for visualization')
        frame = np.frombuffer(blob, dtype=np.uint8)
        if encoding is not None:
            frame = np.reshape(frame, (frame.shape))
            try:
                frame = cv2.imdecode(frame, 1)
            except cv2.error as ex:
                self.logger.error("frame: {}, exception: {}".format(frame, ex))
        else:
            self.logger.info("Encoding not enabled...")
            frame = np.reshape(frame, (height, width, channels))

        # Draw defects
        if 'defects' in results:
            results['defects'] = json.loads(results['defects'])
            for d in results['defects']:
                # Get tuples for top-left and bottom-right coordinates
                tl = tuple(d['tl'])
                br = tuple(d['br'])

                # Draw bounding box
                cv2.rectangle(frame, tl, br, self.bad_color, 2)

                # Draw labels for defects if given the mapping
                if self.labels is not None:
                    # Position of the text below the bounding box
                    pos = (tl[0], br[1] + 20)

                    # The label is the "type" key of the defect, which
                    #  is converted to a string for getting from the labels
                    label = self.labels[str(d['type'])]

                    cv2.putText(frame, label, pos, cv2.FONT_HERSHEY_DUPLEX,
                                0.5, self.bad_color, 2, cv2.LINE_AA)

            # Draw border around frame if has defects or no defects
            if results['defects']:
                outline_color = self.bad_color
            else:
                outline_color = self.good_color

            frame = cv2.copyMakeBorder(frame, 5, 5, 5, 5, cv2.BORDER_CONSTANT,
                                       value=outline_color)

        # Display information about frame
        (dx, dy) = (20, 10)
        if 'display_info' in results:
            results['display_info'] = json.loads(results['display_info'])
            for d_i in results['display_info']:
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

        if self.save_image:
            self.save_images(topic, results, frame)

        if self.display.lower() == 'true':
            self.queue_publish(topic, frame)
        else:
            self.logger.info(f'Classifier_results: {results}')

    def save_images(self, topic, msg, frame):
        img_handle = msg['img_handle']
        if 'defects' in msg:
            if msg['defects']:
                tag = 'bad_'
            else:
                tag = 'good_'
        imgname = tag + img_handle + ".png"
        cv2.imwrite(os.path.join(self.dir_name, imgname),
                    frame,
                    [cv2.IMWRITE_PNG_COMPRESSION, 3])

    def callback(self, topic, msg, blob):
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
                                                      args=(topic, msg, blob,))
            self.drawdefect_thread.start()
        else:
            self.logger.info(f'Classifier_results: {msg}')

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

        per_frame_stats = SubscriberCallback.prepare_per_frame_stats(results)
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
    ap.add_argument('-f', '--fullscreen', default=False, action='store_true',
                    help='Start visualizer in fullscreen mode')
    ap.add_argument('-l', '--labels', default=None,
                    help='JSON file mapping the defect type to labels')

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

    logger = logging.getLogger('visualizer')
    logger.setLevel(logging.INFO)

    # Do basic configuration of logging (just for stdout config)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt_str)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    fh = logging.FileHandler(base_log)
    fh.setLevel(logging.INFO)
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


def zmqSubscriber(msgbus_cfg, queueDict, logger, jsonConfig, args, labels,
                  topic, profiling_mode):
    """
    zmqSubscriber is the ZeroMQ callback to
    subscribe to classified results
    """

    logger.debug('Initializing message bus context')
    msgbus = mb.MsgbusContext(msgbus_cfg)

    logger.debug(f'[INFO] Initializing subscriber for topic \'{topic}\'')
    subscriber = msgbus.new_subscriber(topic)
    sc = SubscriberCallback(queueDict, logger, profiling_mode,
                            labels=labels, dir_name=os.environ["IMAGE_DIR"],
                            save_image=jsonConfig["save_image"],
                            display=jsonConfig["display"])
    while True:
        meta_data, frame = subscriber.recv()
        sc.callback(topic, meta_data, frame)


def main(args):
    """Main method.
    """
    # WIndow name to be used later
    logger = get_logger(__name__)
    app_name = os.environ["AppName"]
    window_name = 'EIS Visualizer App'

    # If user provides labels, read them in
    if args.labels is not None:
        assert_exists(args.labels)
        with open(args.labels, 'r') as f:
            labels = json.load(f)
    else:
        labels = None

    conf = {"certFile": "",
            "keyFile": "",
            "trustFile": ""}
    cfg_mgr = ConfigManager()
    config_client = cfg_mgr.get_config_client("etcd", conf)
    visualizerConfig = config_client.GetConfig("/" + app_name + "/config")
    jsonConfig = json.loads(visualizerConfig)
    image_dir = os.environ["IMAGE_DIR"]
    dev_mode = bool(strtobool(os.environ["DEV_MODE"]))
    profiling_mode = bool(strtobool(os.environ["PROFILING"]))

    # If user provides image_dir, create the directory if don't exists
    if image_dir:
        if not os.path.exists(image_dir):
            os.mkdir(image_dir)

    topicsList = Util.get_topics_from_env("sub")

    queueDict = {}

    for topic in topicsList:
        publisher, topic = topic.split("/")
        queueDict[topic] = queue.Queue(maxsize=10)

    if not dev_mode and jsonConfig["cert_path"] is None:
        logger.error("Kindly Provide certificate directory in etcd config"
                     " when security mode is True")
        sys.exit(1)

    for topic in queueDict.keys():
        msgbus_cfg = Util.get_messagebus_config(topic, "sub", publisher, 
                                                config_client, dev_mode)

        subscribe_thread = threading.Thread(target=zmqSubscriber,
                                            args=(msgbus_cfg, queueDict, logger,
                                                  jsonConfig, args,
                                                  labels, topic,
                                                  profiling_mode))

        subscribe_thread.start()

    if jsonConfig["display"].lower() == 'true':

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
                imageDict[buttonStr] = ImageTk.PhotoImage(image=blankimg)

            buttonCount, rowCount, columnCount = 0, 0, 0
            if(len(topicsList) == 1):
                heightValue = WINDOW_HEIGHT
                widthValue = WINDOW_WIDTH
                topic_text = (topicsList[0].split("/"))[1]
                buttonDict[str(buttonCount)] = Button(rootWin,
                                                      text=topic_text)
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

                        imageDict[
                            "button"+str(
                                buttonCount)] = ImageTk.PhotoImage(
                                                            image=resized_img)

                        buttonDict[str(buttonCount)].config(
                            image=imageDict["button" +
                                            str(buttonCount)],
                            compound=BOTTOM)
                    except Exception:
                        try:
                            buttonDict[str(buttonCount)].config(
                                image=imageDict["button" +
                                                str(buttonCount)],
                                compound=BOTTOM)
                        except Exception:
                            logger.exception("Tkinter exception")
                    buttonCount = buttonCount + 1
                rootWin.update()
        except KeyboardInterrupt:
            logger.info('Quitting...')
        except Exception:
            logger.exception('Error during execution:')
        finally:
            logger.exception('Destroying IEI databus context')
            os._exit(1)


if __name__ == '__main__':

    # Parse command line arguments
    args = parse_args()
    main(args)
