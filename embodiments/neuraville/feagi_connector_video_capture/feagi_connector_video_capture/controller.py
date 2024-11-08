#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2016-present Neuraville Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================
"""

import cv2
import requests
from time import sleep
from datetime import datetime
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import retina as retina
from feagi_connector import feagi_interface as feagi
import traceback
import threading
import os
import screeninfo
import mss
import numpy

camera_data = {"vision": []}


def process_video(video_path, capabilities):
    webcam_list = list()
    webcam_data_each = dict()
    if capabilities['input']['camera']['0']["image"] == "":
        for device in video_path:
            new_cam = cv2.VideoCapture(device)
            webcam_list.append(new_cam)
    # cam.set(3, 320)
    # cam.set(4, 240)
    if capabilities['input']['camera']['0']['video_device_index'] == "monitor":
        all_monitors = screeninfo.get_monitors()  # Needs to create an IPU for this
    pixels = []
    static_image = []
    while True:
        if capabilities['input']['camera']['0']['video_device_index'] != "monitor":
            if capabilities['input']['camera']['0']["image"] != "":
                if static_image == []:
                    pixels = cv2.imread(capabilities['input']['camera']['0']["image"], -1)
                    static_image = pixels
                else:
                    pixels = static_image
                    # pixels = adjust_gamma(pixels)
            else:
                number_of_device = 0
                for i in webcam_list:
                    check, new_data = i.read()
                    webcam_data_each[number_of_device] = new_data
                    number_of_device += 1
                # else:
                #     check, pixels = cam.read()
        else:
            check = True
        if capabilities['input']['camera']['0']['video_device_index'] != "monitor":
            if bool(capabilities['input']['camera']['0']["video_loop"]):
                if check:
                    sleep(0.05)
                else:
                    cam.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if capabilities['input']['camera']['0']['video_device_index'] == "monitor":
            with mss.mss() as sct:
                monitors = all_monitors[capabilities['input']['camera']['0']['monitor']]
                monitor = {
                    "top": monitors.y,
                    "left": monitors.x,
                    "width": monitors.width,
                    "height": monitors.height}

                img = numpy.array(sct.grab(monitor))
                pixels = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            if capabilities['input']['camera']['0']["mirror"]:
                pixels = cv2.flip(pixels, 1)
            camera_data["vision"] = pixels
        else:
            for index in capabilities['input']['camera']:
                if capabilities['input']['camera'][index]["mirror"]:
                    if webcam_data_each:
                        for device in webcam_data_each:
                            webcam_data_each[device] = cv2.flip(webcam_data_each[device], 1)
            if webcam_data_each:
                camera_data["vision"] = webcam_data_each.copy()
            # print(camera_data)
    cam.release()
    cv2.destroyAllWindows()


def adjust_gamma(image, gamma=5.0):
    invGamma = 1.0 / gamma
    table = numpy.array([((i / 255.0) ** invGamma) * 255
                         for i in numpy.arange(0, 256)]).astype("uint8")
    # apply gamma correction using the lookup table
    return cv2.LUT(image, table)


def main(feagi_auth_url, feagi_settings, agent_settings, capabilities, message_to_feagi):
    webcam_list = []
    for index in capabilities['input']['camera']:
        webcam_list.append(capabilities['input']['camera'][index]['video_device_index'])
    threading.Thread(target=process_video, args=(webcam_list, capabilities), daemon=True).start()
    # Generate runtime dictionary
    runtime_data = {"vision": {}, "current_burst_id": None, "stimulation_period": None,
                    "feagi_state": None,
                    "feagi_network": None}
    # FEAGI_FLAG = False
    # print("Waiting on FEAGI...")
    # while not FEAGI_FLAG:
    #     FEAGI_FLAG = feagi.is_FEAGI_reachable(
    #         os.environ.get('FEAGI_HOST_INTERNAL', feagi_settings["feagi_host"]),
    #         int(os.environ.get('FEAGI_OPU_PORT', "3000")))
    #     print((
    #         os.environ.get('FEAGI_HOST_INTERNAL', feagi_settings["feagi_host"]),
    #         int(os.environ.get('FEAGI_OPU_PORT', "3000"))))
    #     print("retrying...")
    #     sleep(2)
    # print("FEAGI is reachable!")
    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # FEAGI registration - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = (
        feagi.connect_to_feagi(
            feagi_settings, runtime_data, agent_settings, capabilities, __version__
        )
    )
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    msg_counter = runtime_data["feagi_state"]['burst_counter']
    rgb = dict()
    rgb['camera'] = dict()
    previous_frame_data = {}
    raw_frame = []
    default_capabilities = {}  # It will be generated in process_visual_stimuli. See the
    # overwrite manual
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)
    # default_capabilities = retina.convert_new_json_to_old_json(default_capabilities)  # temporary
    threading.Thread(target=retina.vision_progress, args=(default_capabilities, feagi_settings, camera_data['vision'],), daemon=True).start()
    while True:
        try:
            if len(camera_data['vision']) > 0:
                previous_frame_data, rgb, default_capabilities = retina.process_visual_stimuli(
                    camera_data['vision'],
                    default_capabilities,
                    previous_frame_data,
                    rgb, capabilities)
            for index in default_capabilities['input']['camera']:
                default_capabilities['input']['camera'][index]['blink'].clear()
            if rgb:
                message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)
            sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()
            if 'camera' in rgb:
                for i in rgb['camera']:
                    rgb['camera'][i].clear()
        except Exception as e:
            # pass
            print("ERROR! : ", e)
            traceback.print_exc()
            break
