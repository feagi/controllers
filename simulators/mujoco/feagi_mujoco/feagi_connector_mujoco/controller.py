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

import os
import sys
import time
import copy
import argparse
import threading
import mujoco.viewer
from feagi_connector import retina
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import feagi_interface as feagi


def check_execution_method():
    if __package__ is None:
        return False
    else:
        return True


if check_execution_method():
    from feagi_connector_mujoco import mujoco_helper as mj_lib
else:
    import mujoco_helper as mj_lib

RUNTIME = float('inf')  # (seconds) timeout time
SPEED = 120  # simulation step speed
xml_actuators_type = dict()


def action(obtained_data, data):
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)
    recieve_motor_data = actuators.get_motor_data(obtained_data)

    if recieve_servo_position_data:
        # output like {0:0.50, 1:0.20, 2:0.30} # example but the data comes from your capabilities' servo range
        for real_id in recieve_servo_position_data:
            servo_number = real_id
            power = recieve_servo_position_data[real_id]
            data.ctrl[servo_number] = power

    if recieve_servo_data:
        # example output: {0: 0.245, 2: 1.0}
        for real_id in recieve_servo_data:
            servo_number = real_id
            new_power = recieve_servo_data[real_id]
            data.ctrl[servo_number] = new_power

    if recieve_motor_data:
        for motor_id in recieve_motor_data:
            data_power = recieve_motor_data[motor_id]
            data.ctrl[motor_id] = data_power

def check_the_flag():

    parser = argparse.ArgumentParser(description="Load MuJoCo model from XML path")
    parser.add_argument(
        "--model_xml_path",
        type=str,
        default="./humanoid.xml",
        help="Path to the XML file (default: './humanoid.xml')"
    )

    args, remaining_args = parser.parse_known_args()
    path = args.model_xml_path  # e.g., './humanoid.xml' or 'C:/path/to/humanoid.xml'
    full_path = os.path.abspath(path)
    if check_execution_method():
        if path == "./humanoid.xml":
            import feagi_connector_mujoco
            package_path = os.path.dirname(feagi_connector_mujoco.__file__)
            full_path = os.path.join(package_path, path.lstrip('./'))
    path = full_path
    model = mujoco.MjModel.from_xml_path(path)
    files = mj_lib.check_nest_file_from_xml(path)
    xml_info = mj_lib.get_actuators(files)
    xml_info = mj_lib.get_sensors(files, xml_info)
    print(f"Model loaded successfully from: {path}")
    available_list_from_feagi_connector = feagi.get_flag_list()
    cleaned_args = []
    skip_next = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if arg in available_list_from_feagi_connector:
            cleaned_args.append(arg)
            if i + 1 < len(sys.argv[1:]) and not sys.argv[1:][i + 1].startswith("-"):
                cleaned_args.append(sys.argv[1:][i + 1])
                skip_next = True

    sys.argv = [sys.argv[0]] + cleaned_args

    return model, xml_info


def start(path):
    main(path)


def main(path):
    # Generate runtime dictionary
    runtime_data = {"vision": [], "stimulation_period": None, "feagi_state": None,
                    "feagi_network": None}

    # Step 3: Load the MuJoCo model
    model, xml_actuators_type = check_the_flag()
    previous_frame_data = {}
    rgb = {}
    rgb['camera'] = {}
    camera_data = {"vision": {}}

    config = feagi.build_up_from_configuration(path)
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # MUJOCO CUSTOM CODE USING MUJOCO_LIBRARY FILE
    data = mujoco.MjData(model)

    actuator_information = mj_lib.generate_actuator_list(model, xml_actuators_type)

    sensor_information = mj_lib.generate_sensor_list(model, xml_actuators_type)

    capabilities = mj_lib.generate_pressure_list(model, mujoco, capabilities)

    capabilities = mj_lib.generate_servo_position_list(model, capabilities)

    capabilities = mj_lib.generate_capabilities_based_of_xml(sensor_information,
                                                             actuator_information,
                                                             capabilities)

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    threading.Thread(target=retina.vision_progress,
                     args=(default_capabilities, feagi_settings, camera_data['vision'],),
                     daemon=True).start()
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)

    # Create a dict to store data
    force_list = {}
    for x in range(len(capabilities['input']['pressure'])):
        force_list[str(x)] = [0, 0, 0]

    sensor_slice_size = mj_lib.read_all_sensors_to_identify_type(model)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        mujoco.mj_resetDataKeyframe(model, data, 4)
        start_time = time.time()
        free_joints = [0] * 21  # keep track of which joints to lock and free (for unstable pause method)
        paused = True

        while viewer.is_running() and time.time() - start_time < RUNTIME:
            step_start = time.time()
            mujoco.mj_step(model, data)

            # The controller will grab the data from FEAGI in real-time
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                # Translate from feagi data to human readable data
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                action(obtained_signals, data)

            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'gyro'):
                gyro_data = mj_lib.read_gyro(data, capabilities, sensor_slice_size)

            positions = data.qpos  # all positions
            positions = positions[7:]  # don't know what the first 7 positions are, but they're not joints so ignore

            # Pick up changes to the physics state, apply perturbations, update options from GUI.
            viewer.sync()

            # Tick Speed #
            time_until_next_step = (1 / SPEED) - (time.time() - step_start)
            if time_until_next_step > 0:
                time.sleep(time_until_next_step)

            # Grab data section
            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'pressure'):
                force_list = mj_lib.read_force(data, force_list, mujoco, model)

            # Example to send data to FEAGI. This is basically reading the joint.

            servo_data = {i: pos for i, pos in enumerate(positions[:len(capabilities['input']['servo_position'])]) if
                          pns.full_template_information_corticals}

            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'camera'):
                camera_data['vision'] = copy.deepcopy(mj_lib.read_lidar(data, sensor_slice_size))

                previous_frame_data, rgb, default_capabilities = \
                    retina.process_visual_stimuli(
                        camera_data['vision'],
                        default_capabilities,
                        previous_frame_data,
                        rgb, capabilities)
                message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)

            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'proximity'):
                sensor_data = mj_lib.read_proximity(data, sensor_slice_size)
            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'gyro'):
                message_to_feagi = sensors.create_data_for_feagi('gyro',
                                                                 capabilities,
                                                                 message_to_feagi,
                                                                 current_data=gyro_data,
                                                                 symmetric=True)
            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'servo_position'):
                message_to_feagi = sensors.create_data_for_feagi('servo_position',
                                                                 capabilities,
                                                                 message_to_feagi,
                                                                 current_data=servo_data,
                                                                 symmetric=True)

            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'proximity'):
                message_to_feagi = sensors.create_data_for_feagi('proximity',
                                                                 capabilities,
                                                                 message_to_feagi,
                                                                 current_data=sensor_data,
                                                                 symmetric=True, measure_enable=True)
            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'pressure'):
                message_to_feagi = sensors.create_data_for_feagi('pressure',
                                                                 capabilities,
                                                                 message_to_feagi,
                                                                 current_data=force_list,
                                                                 symmetric=True,
                                                                 measure_enable=False)  # measure enable set to false so
                # that way, it doesn't change 50/-50 in capabilities automatically

            # Sends to feagi data
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()

if __name__ == "__main__":
    start('./')