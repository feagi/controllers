#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2016-2025 Neuraville Inc. All Rights Reserved.

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
import json
import copy
import threading
import flask_server
from time import sleep
from process_image import *
from datetime import datetime
from feagi_connector import retina
from feagi_connector import testing_mode
from feagi_connector import pns_gateway as pns
import dynamic_image_coordinates as img_coords
from feagi_connector.version import __version__
from feagi_connector import feagi_interface as feagi
from feagi_connector import trainer as feagi_trainer

config = feagi.build_up_from_configuration()
capabilities = config["capabilities"].copy()
fcap = open('configuration.json')
configuration = json.load(fcap)
fcap.close()
image_reader_config = configuration["image_reader"]["0"]
feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator



# Start Flask server
def run_app():
    flask_server.apply_config_settings(image_reader_config)
    flask_server.start_app()


# Need to add configuration to toggle this. It should default to false.
app_thread = threading.Thread(target=run_app)
app_thread.start()


if __name__ == "__main__":
    runtime_data = {
        "vision": {},
        "current_burst_id": None,
        "stimulation_period": None,
        "feagi_state": None,
        "feagi_network": None,
    }

    # Load configurations and settings
    feagi_settings = config["feagi_settings"].copy()
    agent_settings = config["agent_settings"].copy()
    default_capabilities = config["default_capabilities"].copy()
    message_to_feagi = config["message_to_feagi"].copy()

    # FEAGI registration - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = (
        feagi.connect_to_feagi(
            feagi_settings, runtime_data, agent_settings, capabilities, __version__
        )
    )
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # Initialize a message counter from the FEAGI state
    msg_counter = runtime_data["feagi_state"]["burst_counter"]

    # Fetch the full dimensions if not already set
    if not pns.full_list_dimension:
        pns.full_list_dimension = pns.fetch_full_dimensions()

    # Initialize variables for vision processing
    rgb = dict()
    rgb["camera"] = dict()
    previous_frame_data = {}
    start_timer = 0
    raw_frame = []
    continue_loop = True
    total = 0
    success = 0
    success_rate = 0
    # overwrite manual
    flag = True
    camera_data = dict()
    camera_data["vision"] = []
    temporary_previous = dict()

    # Create runtime default capabilities list
    default_capabilities = {}  # It will be generated in process_visual_stimuli. See the
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)
    threading.Thread(target=retina.vision_progress, args=(default_capabilities,feagi_settings,camera_data["vision"],),daemon=True,).start()

    one_time_run = True
    image_obj = feagi_trainer.scan_the_folder(configuration['image_reader']['0']['image_path'])
    information_files = list(image_obj)
    # raw_frame = image_obj[0]
    if information_files:
        name_id = information_files[0][1]
        if information_files[0][1] in feagi_trainer.image_extensions:
            raw_frame = information_files[0][0]
            camera_data['vision'] = raw_frame
    else:
        name_id = ''
    previous_name = ''
    previous_capabilities = {}
    modified_data = {}
    counter = 0

    latest_vals = flask_server.latest_static
    image_reader_config["image_path"] = latest_vals.image_path
    image_reader_config["loop"] = latest_vals.loop
    image_obj = feagi_trainer.scan_the_folder(image_reader_config["image_path"])
    latest_image_id = None

    while True:
        message_from_feagi = pns.message_from_feagi
        latest_vals = flask_server.latest_static
        image_reader_config["image_display_duration"] = latest_vals.image_display_duration
        image_reader_config["test_mode"] = latest_vals.test_mode
        image_reader_config["image_gap_duration"] = latest_vals.image_gap_duration
        image_reader_config["feagi_controlled"] = latest_vals.feagi_controlled

        if image_reader_config["feagi_controlled"]:
            # Static here
            if counter == 5 / feagi_settings['burst_duration']:
                print(name_id, " is not in folder.")
                counter = 0
                flask_server.latest_image = blank_image()
                flask_server.latest_raw_image = flask_server.latest_image



            if rgb=={}:
                rgb['camera'] = {}
            # Print each variable before evaluating the condition
            if (previous_name != name_id) or (previous_capabilities != default_capabilities) or (not rgb['camera']):
                rgb['camera'].clear()
                previous_name = name_id  # Update name so it wont need to recaluate the vision
                previous_capabilities = copy.deepcopy(default_capabilities)
                failed_to_find_file = True
                for index in range(len(information_files)):
                    if information_files[index][1] == name_id:
                        raw_frame = information_files[index][0]
                        failed_to_find_file = False

            if failed_to_find_file:
                image_obj = feagi_trainer.scan_the_folder(configuration['image_reader']['0']['image_path'])
                information_files = list(image_obj)
                counter += 1
            else:
                if information_files[0][2] in feagi_trainer.video_extensions:
                    cap = information_files[0][0]
                    while cap.isOpened():
                        if not latest_vals.feagi_controlled:
                            break
                        message_from_feagi = pns.message_from_feagi
                        ret, raw_frame = cap.read()
                        if ret:
                            pass
                        else:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        temporary_previous, rgb, default_capabilities, modified_data = retina.process_visual_stimuli_trainer(
                            raw_frame,
                            default_capabilities,
                            previous_frame_data,
                            rgb, capabilities, False)  # processes visual data into FEAGI-comprehensible form
                        flask_server.latest_raw_image = raw_frame
                        if "00_C" in modified_data:
                            flask_server.latest_image = process_image(modified_data["00_C"])
                        if 'opu_data' in message_from_feagi:
                            recognition_id = pns.detect_ID_data(message_from_feagi)
                            if recognition_id:
                                name_id = recognition_id
                                for i in name_id:
                                    feagi_image_id = i
                                    break
                                flask_server.latest_static = img_coords.update_image_ids(new_image_id=None, new_feagi_image_id=feagi_image_id, static=flask_server.latest_static)
                                if information_files[0][1] != name_id:
                                    break

                        # Show user image currently sent to FEAGI, with a bounding box showing FEAGI's location data if it exists
                        location_data = pns.recognize_location_data(message_from_feagi)
                        if previous_frame_data:
                            flask_server.latest_static.image_dimensions = f"{modified_data['00_C'].shape[1]} x {modified_data['00_C'].shape[0]}"
                            new_image_id = getattr(flask_server.latest_static, "image_id", "")
                            feagi_image_id = getattr(flask_server.latest_static, "feagi_image_id", "")
                            if location_data:
                                if "00_C" in modified_data:
                                    flask_server.latest_image = process_image(modified_data["00_C"], location_data, size_of_cortical)
                            elif latest_image_id != new_image_id:
                                latest_image_id = new_image_id
                                if "00_C" in modified_data:
                                    flask_server.latest_image = process_image(modified_data["00_C"])

                        # If camera data is available, generate data for FEAGI
                        if 'camera' in rgb:  # This is the data wrapped for feagi data to read
                            if rgb['camera'] == {}:
                                # break
                                pass
                            else:
                                message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)

                        # location section
                        location_data = pns.recognize_location_data(message_from_feagi)
                        # Testing mode section
                        if configuration['image_reader']['0']['test_mode']:
                            success_rate, success, total = testing_mode.mode_testing(name_id,
                                                                                     message_from_feagi,
                                                                                     total, success,
                                                                                     success_rate)
                        else:
                            success_rate, success, total = 0, 0, 0
                        # Send signals to FEAGI
                        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings,
                                             feagi_settings)

                        sleep(feagi_settings['burst_duration'])
                        previous_frame_data = temporary_previous.copy()
                else:
                    temporary_previous, rgb, default_capabilities, modified_data = retina.process_visual_stimuli_trainer(
                        raw_frame,
                        default_capabilities,
                        previous_frame_data,
                        rgb, capabilities, False)  # processes visual data into FEAGI-comprehensible form
                    flask_server.latest_raw_image = raw_frame
                    if "00_C" in modified_data:
                        flask_server.latest_image = process_image(modified_data["00_C"])
                if 'opu_data' in message_from_feagi:
                    recognition_id = pns.detect_ID_data(message_from_feagi)
                    if recognition_id:
                        name_id = recognition_id
                        for i in name_id:
                            feagi_image_id = i
                            break
                        flask_server.latest_static = img_coords.update_image_ids(new_image_id=None,
                                                                                 new_feagi_image_id=feagi_image_id,
                                                                                 static=flask_server.latest_static)

                        # Show user image currently sent to FEAGI, with a bounding box showing FEAGI's location data if it exists
                    location_data = pns.recognize_location_data(message_from_feagi)
                    if previous_frame_data:
                        flask_server.latest_static.image_dimensions = f"{modified_data['00_C'].shape[1]} x {modified_data['00_C'].shape[0]}"
                        new_image_id = getattr(flask_server.latest_static, "image_id", "")
                        feagi_image_id = getattr(flask_server.latest_static, "feagi_image_id", "")
                        if location_data:
                            if "00_C" in modified_data:
                                flask_server.latest_image = process_image(modified_data["00_C"], location_data,
                                                                          size_of_cortical)
                        elif latest_image_id != new_image_id:
                            latest_image_id = new_image_id
                            if "00_C" in modified_data:
                                flask_server.latest_image = process_image(modified_data["00_C"])

                    # If camera data is available, generate data for FEAGI
                    if 'camera' in rgb:  # This is the data wrapped for feagi data to read
                        if rgb['camera'] == {}:
                            # break
                            pass
                        else:
                            message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)

                    # location section
                    location_data = pns.recognize_location_data(message_from_feagi)
                    # Testing mode section
                    if configuration['image_reader']['0']['test_mode']:
                        success_rate, success, total = testing_mode.mode_testing(name_id,
                                                                                 message_from_feagi,
                                                                                 total, success,
                                                                                 success_rate)
                    else:
                        success_rate, success, total = 0, 0, 0
                    # Send signals to FEAGI

                    pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings,
                                         feagi_settings)

                    sleep(feagi_settings['burst_duration'])
                    previous_frame_data = temporary_previous.copy()
        else:
            # Previous design
        # while continue_loop:
            # Iterate through images
            image_obj = feagi_trainer.scan_the_folder(
                configuration['image_reader']['0']['image_path'])
            for image in image_obj:
                name_id = image[1]
                image_id = key = next(iter(name_id))
                extension = image[2]
                if extension in feagi_trainer.video_extensions:
                    cap = image[0]
                    # check, raw_frame = new_cam.read() # webcam
                    raw_frame = cap.read()[1]

                    # Carry on with the image processing
                    if not image_reader_config["test_mode"]:
                        message_to_feagi = feagi_trainer.id_training_with_image(message_to_feagi, name_id)
                    if start_timer == 0.0:
                        start_timer = datetime.now()


                    while cap.isOpened():
                        message_from_feagi = pns.message_from_feagi
                        ret, raw_frame = cap.read()
                        if ret:
                            pass
                        else:
                            if float(image_reader_config["image_display_duration"]) >= (datetime.now() - start_timer).total_seconds():
                                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                continue
                            else:
                                break
                        camera_data["vision"] = raw_frame
                        # Update the latest image data for Flask server to display
                        flask_server.latest_raw_image = raw_frame
                        flask_server.latest_static.raw_image_dimensions = (f"{raw_frame.shape[1]} x {raw_frame.shape[0]}")
                        flask_server.latest_static = img_coords.update_image_ids(new_image_id=image_id,
                                                                                 new_feagi_image_id=None,
                                                                                 static=flask_server.latest_static)
                        # Apply any browser UI user changes to config data
                        latest_vals = flask_server.latest_static
                        image_reader_config["image_display_duration"] = (latest_vals.image_display_duration)
                        image_reader_config["test_mode"] = latest_vals.test_mode
                        image_reader_config["image_gap_duration"] = (latest_vals.image_gap_duration)
                        # image_reader_config["feagi_controlled"] = latest_vals.feagi_controlled # this is fraud AI. we dont do it here
                        if latest_vals.feagi_controlled:
                            break

                        # Set variables & process image
                        size_list = pns.resize_list
                        message_from_feagi = pns.message_from_feagi
                        temporary_previous, rgb, default_capabilities, modified_data = (
                            retina.process_visual_stimuli_trainer(
                                raw_frame,
                                default_capabilities,
                                previous_frame_data,
                                rgb,
                                capabilities,
                                False))



                        # When FEAGI sends a recognition ID (like {'0-5-0': 100}), update it for Flask server to display
                        if "opu_data" in message_from_feagi:
                            recognition_id = pns.detect_ID_data(message_from_feagi)
                            if recognition_id:
                                feagi_image_id = key = next(iter(recognition_id))
                                flask_server.latest_static = img_coords.update_image_ids(
                                    new_image_id=None,
                                    new_feagi_image_id=feagi_image_id,
                                    static=flask_server.latest_static,
                                )

                        # Process current image sent to FEAGI with bounding box
                        location_data = pns.recognize_location_data(message_from_feagi)
                        if pns.full_list_dimension:
                            o_loc = pns.full_list_dimension.get("o__loc")
                            if o_loc:
                                size_of_cortical = o_loc["cortical_dimensions"]

                        # Add image's dimensions to HTML display data
                        if previous_frame_data:
                            if len(modified_data['00_C']) > 0:
                                flask_server.latest_static.image_dimensions = f"{modified_data['00_C'].shape[1]} x {modified_data['00_C'].shape[0]}"
                                new_image_id = getattr(flask_server.latest_static, "image_id", "")
                                feagi_image_id = getattr(
                                    flask_server.latest_static, "feagi_image_id", ""
                                )
                                if location_data:
                                    if "00_C" in modified_data:
                                        flask_server.latest_image = process_image(
                                            modified_data["00_C"], location_data, size_of_cortical
                                        )
                                latest_image_id = new_image_id
                                if "00_C" in modified_data:
                                    flask_server.latest_image = process_image(
                                        modified_data["00_C"]
                                    )

                        # If camera data is available, generate data for FEAGI
                        if "camera" in rgb:  # This is the data wrapped for feagi data to read
                            if rgb["camera"] == {}:
                                break
                            else:
                                message_to_feagi = pns.generate_feagi_data(
                                    rgb, message_to_feagi
                                )
                        message_from_feagi = (
                            pns.message_from_feagi
                        )  # Need to re-structure this code to be more consistent

                        # location section
                        location_data = pns.recognize_location_data(message_from_feagi)
                        if image_reader_config["test_mode"] and "opu" in message_from_feagi:
                            success_rate, success, total = testing_mode.mode_testing(name_id, message_from_feagi, total,
                                                                                     success, success_rate)
                        else:
                            success_rate, success, total = 0, 0, 0

                        # Send signals to FEAGI
                        pns.signals_to_feagi(
                            message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings
                        )

                        # Sleep for the burst duration specified in the settings
                        sleep(feagi_settings["burst_duration"])
                    blank_image()  # reset the image or during gap
                    sleep(image_reader_config["image_gap_duration"])
                    previous_frame_data = temporary_previous.copy()
                    start_timer = 0.0
                    message_to_feagi.clear()
                else:
                    raw_frame = image[0]
                    # Update the latest image data for Flask server to display
                    flask_server.latest_raw_image = raw_frame
                    flask_server.latest_static.raw_image_dimensions = (f"{raw_frame.shape[1]} x {raw_frame.shape[0]}")
                    flask_server.latest_static = img_coords.update_image_ids(new_image_id=image_id,
                                                                             new_feagi_image_id=None,
                                                                             static=flask_server.latest_static)
                    # Carry on with the image processing
                    if not image_reader_config["test_mode"]:
                        message_to_feagi = feagi_trainer.id_training_with_image(message_to_feagi, name_id)
                    if start_timer == 0.0:
                        start_timer = datetime.now()

                    while (float(image_reader_config["image_display_duration"]) >= (
                            datetime.now() - start_timer).total_seconds()):
                        # Apply any browser UI user changes to config data
                        latest_vals = flask_server.latest_static
                        image_reader_config["image_display_duration"] = (latest_vals.image_display_duration)
                        image_reader_config["test_mode"] = latest_vals.test_mode
                        image_reader_config["image_gap_duration"] = (latest_vals.image_gap_duration)
                        # image_reader_config["feagi_controlled"] = latest_vals.feagi_controlled # this is fraud AI. we dont do it here

                        # Set variables & process image
                        size_list = pns.resize_list
                        message_from_feagi = pns.message_from_feagi
                        temporary_previous, rgb, default_capabilities, modified_data = (
                            retina.process_visual_stimuli_trainer(
                                raw_frame,
                                default_capabilities,
                                previous_frame_data,
                                rgb,
                                capabilities,
                                False))

                        # When FEAGI sends a recognition ID (like {'0-5-0': 100}), update it for Flask server to display
                        if "opu_data" in message_from_feagi:
                            recognition_id = pns.detect_ID_data(message_from_feagi)
                            if recognition_id:
                                feagi_image_id = key = next(iter(recognition_id))
                                flask_server.latest_static = img_coords.update_image_ids(
                                    new_image_id=None,
                                    new_feagi_image_id=feagi_image_id,
                                    static=flask_server.latest_static)
                            # if "o__sid" in message_from_feagi["opu_data"]:
                            #     if message_from_feagi["opu_data"]["o__sid"]:
                            #

                        # Process current image sent to FEAGI with bounding box
                        location_data = pns.recognize_location_data(message_from_feagi)
                        if pns.full_list_dimension:
                            o_loc = pns.full_list_dimension.get("o__loc")
                            if o_loc:
                                size_of_cortical = o_loc["cortical_dimensions"]

                        # Add image's dimensions to HTML display data
                        if previous_frame_data:
                            if len(modified_data['00_C']) > 0:
                                flask_server.latest_static.image_dimensions = f"{modified_data['00_C'].shape[1]} x {modified_data['00_C'].shape[0]}"
                                new_image_id = getattr(flask_server.latest_static, "image_id", "")
                                feagi_image_id = getattr(
                                    flask_server.latest_static, "feagi_image_id", ""
                                )
                                if location_data:
                                    if "00_C" in modified_data:
                                        flask_server.latest_image = process_image(
                                            modified_data["00_C"], location_data, size_of_cortical
                                        )
                                elif latest_image_id != new_image_id:
                                    latest_image_id = new_image_id
                                    if "00_C" in modified_data:
                                        flask_server.latest_image = process_image(
                                            modified_data["00_C"]
                                        )

                        # If camera data is available, generate data for FEAGI
                        if "camera" in rgb:  # This is the data wrapped for feagi data to read
                            if rgb["camera"] == {}:
                                break
                            else:
                                message_to_feagi = pns.generate_feagi_data(
                                    rgb, message_to_feagi
                                )
                        message_from_feagi = pns.message_from_feagi  # Need to re-structure this code to be more consistent

                        # location section
                        location_data = pns.recognize_location_data(message_from_feagi)
                        if image_reader_config["test_mode"] and "opu" in message_from_feagi:
                            success_rate, success, total = testing_mode.mode_testing(name_id, message_from_feagi, total, success, success_rate)

                        else:
                            success_rate, success, total = 0, 0, 0

                        # Send signals to FEAGI
                        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)

                        # Sleep for the burst duration specified in the settings
                        sleep(feagi_settings["burst_duration"])
                    blank_image()  # reset the image or during gap
                    sleep(image_reader_config["image_gap_duration"])
                    previous_frame_data = temporary_previous.copy()
                    start_timer = 0.0
                    message_to_feagi.clear()
            # Sleep for the burst duration before the next iteration
            sleep(feagi_settings["burst_duration"])
            continue_loop = image_reader_config["loop"]