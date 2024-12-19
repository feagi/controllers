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

import json
import mujoco_library as mj_lib
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
xml_actuators_type = dict()


def action(obtained_data):
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

    path = args.model_xml_path
    model = mujoco.MjModel.from_xml_path(path)
    files = mj_lib.check_nest_file_from_xml(path)
    xml_info = mj_lib.get_actuators(files)
    xml_info = mj_lib.get_sensors(files, xml_info)
    print(f"Model loaded successfully from: {path}")

    cleaned_args = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg == "--model_xml_path":
            skip_next = True
        else:
            cleaned_args.append(arg)

    sys.argv = [sys.argv[0]] + cleaned_args
    return model, xml_info


if __name__ == "__main__":
    # Generate runtime dictionary
    runtime_data = {"vision": [], "stimulation_period": None, "feagi_state": None,
                    "feagi_network": None}

    # Step 3: Load the MuJoCo model
    model, xml_actuators_type = check_the_flag()
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
                action(obtained_signals)

            if mj_lib.check_capabilities_with_this_sensor(capabilities, 'gyro'):
                gyro_data = mj_lib.read_gyro(model, data, capabilities)

            # ### actuator section
            # # Number of actuators
            # print("Number of actuators:", model.nu)
            # # Basic actuator states
            # print("Actuator controls (input signals):", data.ctrl)
            # print("Actuator forces:", data.actuator_force)
            # print("Actuator lengths:", data.actuator_length)
            # print("Actuator velocities:", data.actuator_velocity)
            # print("Actuator moments:", data.actuator_moment)
            # # Activation states (if using activation dynamics)
            # print("Activation states:", data.act)
            # print("Activation derivatives:", data.act_dot)
            # # Get actuator names from model
            # print("Actuator names:")
            # for i in range(model.nu):
            #     print(f"Actuator {i}: {model.actuator(i).name}")
            # # Get actuator types from model
            # print("Actuator types:")
            # for i in range(model.nu):
            #     print(f"Actuator {i} type:", model.actuator_trntype[i])
            # # Print actuator types
            # for i in range(model.nu):
            #     gain_type = model.actuator_gaintype[i]
            #     print(f"Bwuk Actuator {i} ({model.actuator(i).name}): {gain_type}")

            # print("Control ranges:")
            # for i in range(model.nu):
            #     actuator_name = model.actuator(i).name
            #     ctrl_range_min = model.actuator_ctrlrange[i][0]
            #     ctrl_range_max = model.actuator_ctrlrange[i][1]
            #     print(f"Actuator {i} ({actuator_name}):")
            #     print(f"  Control range: [{ctrl_range_min}, {ctrl_range_max}]")
            # print("END OF ACTUATOR")
            #
            # # Plugion section
            # print("PLUGIN SECTION")
            # # Number of plugins
            # print("Number of plugins:", data.nplugin)
            # # Print plugin data
            # print("Plugin data:", data.plugin_data)
            # # Print plugin state
            # print("Plugin state:", data.plugin_state)
            # # To see plugin instances directly
            # print("Plugin instances:")
            # for i in range(data.nplugin):
            #     print(f"Plugin {i}:", data.plugin(i))
            # print("Plugin details from model:")
            # for i in range(model.nplugin):
            #     plugin = model.plugin(i)
            #     print(f"Plugin {i}:")
            #     print(f"  Name: {plugin.name}")
            #     print(f"  Type: {plugin.type}")
            # #
            # # # Number of sensors
            # print("SENSOR LIST: ")

            #
            # # # region READ POSITIONAL DATA HERE ###
            # print([attr for attr in dir(data) if not attr.startswith('_')])
            # print(data.cam)
            #
            #
            # # # JOINT SECTION
            # print("JOINT SECTION HERE: ")
            # # Number of joints
            # print("Number of joints:", model.njnt)
            # # Print joint positions (qpos) - but note the first 7 are the free joint as you mentioned
            # print("Joint positions:", data.qpos)
            #
            # # Print joint velocities
            # print("Joint velocities:", data.qvel)
            #
            # # Print detailed joint information
            # print("Joint details:")
            # for i in range(model.njnt):
            #     joint = model.joint(i)
            #     print(f"Joint {i}:")
            #     print(f"  Name: {joint.name}")
            #     print(f"  Type: {joint.type}")
            #     print(f"  Position: {data.joint(i)}")
            #     print(f"  qpos index: {joint.qposadr}")  # index into qpos array
            #     print(f"  qvel index: {joint.dofadr}")  # index into qvel array

            # # GEOM SECTION:
            # print("GEOMS SECTION:")
            # # Number of geoms
            # print("Number of geoms:", model.ngeom)
            #
            # # Print geom positions
            # print("\nGeom positions:", data.geom_xpos)
            #
            # # Print geom orientations (rotation matrices)
            # print("\nGeom orientations:", data.geom_xmat)
            #
            # # Print detailed geom information
            # print("\nGeom details:")
            # for i in range(model.ngeom):
            #     geom = model.geom(i)
            #     print(f"\nGeom {i}:")
            #     print(f"  Name: {geom.name}")
            #     print(
            #         f"  Type: {geom.type}")  # 0=plane, 1=hfield, 2=sphere, 3=capsule, 4=ellipsoid, 5=cylinder, 6=box, 7=mesh
            #     print(f"  Position: {data.geom_xpos[i]}")
            #     print(f"  Orientation: {data.geom_xmat[i]}")
            #     print(f"  Size: {geom.size}")  # dimensions depend on geom type
            #     print(f"  Mass: {geom.mass}")

            # # SITE INFORMATION
            # print("SITE SECTION: ")
            # # Number of sites
            # print("Number of sites:", model.nsite)
            #
            # # Print site positions
            # print("Site positions (xpos):", data.site_xpos)
            #
            # # Print site orientations (rotation matrices)
            # print("Site orientations (xmat):", data.site_xmat)
            #
            # # Print detailed site information
            # print("Site details:")
            # for i in range(model.nsite):
            #     site = model.site(i)
            #     print(f"Site {i}:")
            #     print(f"  Name: {site.name}")
            #     print(f"  Position: {data.site_xpos[i]}")
            #     print(f"  Orientation matrix: {data.site_xmat[i]}")

            ## CAMERA SECTION
            # # Print number of cameras
            # print("Number of cameras:", model.ncam)
            #
            # # Print camera names
            # for i in range(model.ncam):
            #     print(f"Camera {i} name:", model.camera(i).name)
            #
            # # Get camera positions
            # camera_positions = data.cam()
            # print("Camera positions:", camera_positions)

            positions = data.qpos  # all positions
            positions = positions[7:]  # don't know what the first 7 positions are, but they're not joints so ignore
            # them

            # for i in range(data.ncon):
            #     force = np.zeros(6)  # Use numpy to allocate blank array
            #     # Retrieve the contact force data
            #     mujoco.mj_contactForce(model, data, i, force)
            #     obtained_data_from_force = force[:3]
            #     force_list[str(i)] = list((float(obtained_data_from_force[0]), float(obtained_data_from_force[1]),
            #                                float(obtained_data_from_force[2])))
            # endregion

            # FORCE LIST
            # for i in range(data.ncon):
            #     force = np.zeros(6)
            #     mujoco.mj_contactForce(model, data, i, force)
            #     obtained_data_from_force = force[:3]
            #
            #     # Get the contact information
            #     contact = data.contact[i]
            #
            #     # Get the names of the geoms involved
            #     geom1_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom1)
            #     geom2_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom2)
            #
            #     # Store both force and contact information
            #     force_list[f"{geom1_name}_{geom2_name}"] = {
            #         'force': list((float(obtained_data_from_force[0]),
            #                        float(obtained_data_from_force[1]),
            #                        float(obtained_data_from_force[2]))),
            #         'pos': list(contact.pos),
            #         'geom1': geom1_name,
            #         'geom2': geom2_name
            #     }
            #     print(force_list)

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
            # print(servo_data)
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
            # print(data.sensordata[3:6])
            # print("SLICE LIST: ", sensor_slice_size) # I implemented but then end up doesnt even need it
            # print("new data: ", mj_lib.read_proximity(model, data, capabilities))
            # print("SENSOR DATA: ", sensor_data)
            # print("GYRO DATA: ", gyro_data)
            # test = mj_lib.read_proximity(model, data, capabilities)
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
