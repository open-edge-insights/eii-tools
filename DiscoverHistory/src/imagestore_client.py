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
"""Retrieve image frames from the queue and process them according to the
   presence or absence of defects.
"""

from datetime import datetime
import json
import argparse
import eis.msgbus as mb
import os
import logging
import cv2
import numpy as np 
import influxdbconnector_client

bad_color=(0, 0, 255)
good_color=(0, 255, 0)
logger=logging.getLogger()

def save_images(elm, frame, dir,tag):
    img_handle = elm['img_handle']
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    imgname = str(now) + "_" + tag + img_handle + ".png"
    if not os.path.exists(dir):
        os.makedirs(dir)
    cv2.imwrite(os.path.join(dir, imgname),
                    frame,
                    [cv2.IMWRITE_PNG_COMPRESSION, 3])

def draw_defects(elm, frame, dir_name) :
    
    if 'defects' in elm.keys():
        defect_json = json.loads(elm['defects'])
        if elm['encoding_type'] and elm['encoding_level']:
            encoding = {"type": elm['encoding_type'],
                        "level": elm['encoding_level']}
        logger.info(elm)
        # Convert to Numpy array and reshape to frame
        logger.info('Preparing frame for visualization')
        frame = np.frombuffer(frame, dtype=np.uint8)
        if encoding is not None:
            frame = np.reshape(frame, (frame.shape))
            try:
                frame = cv2.imdecode(frame, 1)
            except cv2.error as ex:
                logger.error("frame: {}, exception: {}".format(frame, ex))
        else:
            logger.info("Encoding not enabled...")
            frame = np.reshape(frame, (height, width, channel))

         # Display information about frame
        (dx, dy) = (20, 10)
        if  'display_info' in elm.keys():
            display_info = json.loads(elm['display_info'])
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
        #PROCESS IF THE FRAME HAS DEFECTS        
        if len(defect_json)>0:
            for d in defect_json:
                # Get tuples for top-left and bottom-right coordinates
                tl = tuple(d['tl'])
                br = tuple(d['br'])

                # Draw bounding box
                cv2.rectangle(frame, tl, br, bad_color, 2)

                # Draw labels for defects if given the mapping
                if d['type'] is not None:
                    # Position of the text below the bounding box
                    pos = (tl[0], br[1] + 20)

                    # The label is the "type" key of the defect, which
                    #  is converted to a string for getting from the labels
                    label = str(d['type'])
                    cv2.putText(frame, label, pos, cv2.FONT_HERSHEY_DUPLEX,
                                0.5, bad_color, 2, cv2.LINE_AA)

            # Draw border around frame if has defects
            outline_color = bad_color
            frame = cv2.copyMakeBorder(frame, 5, 5, 5, 5, cv2.BORDER_CONSTANT,
                                        value=outline_color)
            tag = 'bad_'
            dir=dir_name +"/bad_frames"
            save_images(elm, frame, dir,tag)
        #PROCESS IF THE FRAME DOES NOT HAVE DEFECTS
        else:
            outline_color = good_color
            frame = cv2.copyMakeBorder(frame, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=outline_color)
            dir=dir_name +"/good_frames"
            tag = 'good_'
            save_images(elm, frame, dir,tag)
            
        
# Argument parsing
def retrieve_image_frames(eis_config,query_config,img_handle_queue):
    msgbus = None
    service = None
    dir_name="/output/"
    try:
        msgbus = mb.MsgbusContext(eis_config)

        logger.info(f'[INFO] Initializing service for topic \'imagestore_service\'')
        service = msgbus.get_service('imagestore_service')

        logger.info(f'[INFO] Running...')
        while True:
            elm = img_handle_queue.get()
            img_handle = elm['img_handle']
            request = {'command': 'read', 'img_handle': img_handle}
            logger.info(f'[INFO] Sending request {request}')
            service.request(request)
            logger.info(f'[INFO] Waiting for response')
            response = service.recv()
            output_dir = "/output/" + "/" + "frames"
            draw_defects(elm, response[1],output_dir)

    except KeyboardInterrupt:
        logger.info(f'[INFO] Quitting...')
    finally:
        if service is not None:
            service.close()
