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

import sys
import time
import argparse
import threading
import numpy as np
import mujoco.viewer
from feagi_connector import retina
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import feagi_interface as feagi

RUNTIME = float('inf')  # (seconds) timeout time
SPEED = 120  # simulation step speed


def action(obtained_data):
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    if recieve_servo_position_data:
        # output like {0:0.50, 1:0.20, 2:0.30} # example but the data comes from your capabilities' servo range
        for real_id in recieve_servo_position_data:
            servo_number = real_id
            power = recieve_servo_position_data[real_id]
            if (len(data.ctrl) - 1) >= servo_number:
                data.ctrl[servo_number] = power

    if recieve_servo_data:
        # example output: {0: 0.245, 2: 1.0}
        for real_id in recieve_servo_data:
            servo_number = real_id
            new_power = recieve_servo_data[real_id]
            data.ctrl[servo_number] = new_power


def quaternion_to_euler(w, x, y, z):
    """Convert quaternion to euler angles (in degrees)"""
    # roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.copysign(np.pi / 2, sinp)
    else:
        pitch = np.arcsin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return np.degrees([roll, pitch, yaw])


def get_head_orientation():
    # Get quaternion data from head sensor
    quat_id = model.sensor('head_gyro').id
    quat = data.sensordata[quat_id:quat_id + 4]  # w, x, y, z

    # Convert to euler angles
    euler_angles = quaternion_to_euler(quat[0], quat[1], quat[2], quat[3])

    return [euler_angles[0], euler_angles[1], euler_angles[2]]

def check_the_flag():
    parser = argparse.ArgumentParser(description="Load MuJoCo model from XML path")
    parser.add_argument(
        "--file",
        type=str,
        default="./humanoid.xml",
        help="Path to the XML file (default: './humanoid.xml')"
    )

    args, remaining_args = parser.parse_known_args()

    path = args.file
    model = mujoco.MjModel.from_xml_path(path)
    print(f"Model loaded successfully from: {path}")

    cleaned_args = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg == "--file":
            skip_next = True
        else:
            cleaned_args.append(arg)

    sys.argv = [sys.argv[0]] + cleaned_args
    return model

if __name__ == "__main__":
    # Generate runtime dictionary
    runtime_data = {"vision": [], "stimulation_period": None, "feagi_state": None,
                    "feagi_network": None}

    # Step 3: Load the MuJoCo model
    model = check_the_flag()

    previous_frame_data = {}
    rgb = {}
    rgb['camera'] = {}
    camera_data = {"vision": {}}

    config = feagi.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    threading.Thread(target=retina.vision_progress,
                     args=(default_capabilities, feagi_settings, camera_data['vision'],),
                     daemon=True).start()
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)
    data = mujoco.MjData(model)

    # Create a dict to store data
    force_list = {}
    for x in range(20):
        force_list[str(x)] = [0, 0, 0]



    actuators.start_servos(capabilities)
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
                # pns.check_genome_status_no_vision(message_from_feagi)
                action(obtained_signals)

            # region READ POSITIONAL DATA HERE ###
            positions = data.qpos  # all positions
            positions = positions[7:]  # don't know what the first 7 positions are, but they're not joints so ignore
            # them

            for i in range(data.ncon):
                force = np.zeros(6)  # Use numpy to allocate blank array

                # Retrieve the contact force data
                mujoco.mj_contactForce(model, data, i, force)
                obtained_data_from_force = force[:3]
                force_list[str(i)] = list((float(obtained_data_from_force[0]), float(obtained_data_from_force[1]),
                                           float(obtained_data_from_force[2])))
            # endregion

            # Pick up changes to the physics state, apply perturbations, update options from GUI.
            viewer.sync()

            # Tick Speed #
            time_until_next_step = (1 / SPEED) - (time.time() - step_start)
            if time_until_next_step > 0:
                time.sleep(time_until_next_step)

            # Example to send data to FEAGI. This is basically reading the joint.

            servo_data = {i: pos for i, pos in enumerate(positions[:20]) if
                          pns.full_template_information_corticals}
            sensor_data = {i: pos for i, pos in enumerate(data.sensordata[3:6]) if
                           pns.full_template_information_corticals}
            # lidar_data = {i: pos for i, pos in enumerate(data.sensordata[7:]) if
            #                pns.full_template_information_corticals}
            # lidar_data = data.sensordata[7:] * 100
            # lidar_2d = lidar_data.reshape(16, 16)
            #
            # # Create 16x16x3 array and flatten it
            # result = np.zeros((16, 16, 3))  # 3 for x,y,z
            # result[:, :, 0] = lidar_2d  # Set first channel to LIDAR data
            # flat_result = result.flatten()  # Makes it 1D array of length 768 (16*16*3)
            # raw_frame = retina.RGB_list_to_ndarray(flat_result,
            #                                        [16, 16])
            # camera_data['vision'] = {"0": retina.update_astype(raw_frame)}


            # previous_frame_data, rgb, default_capabilities = \
            #     retina.process_visual_stimuli(
            #         camera_data['vision'],
            #         default_capabilities,
            #         previous_frame_data,
            #         rgb, capabilities)
            # message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)
            #
            # # Get gyro data
            # gyro = get_head_orientation()
            # gyro_data = {"0": np.array(gyro)}

            # Creating message to send to FEAGI
            # message_to_feagi = sensors.create_data_for_feagi('gyro',
            #                                                  capabilities,
            #                                                  message_to_feagi,
            #                                                  current_data=gyro_data,
            #                                                  symmetric=True)
            message_to_feagi = sensors.create_data_for_feagi('servo_position',
                                                             capabilities,
                                                             message_to_feagi,
                                                             current_data=servo_data,
                                                             symmetric=True)

            message_to_feagi = sensors.create_data_for_feagi('proximity',
                                                             capabilities,
                                                             message_to_feagi,
                                                             current_data=sensor_data,
                                                             symmetric=True, measure_enable=True)
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
