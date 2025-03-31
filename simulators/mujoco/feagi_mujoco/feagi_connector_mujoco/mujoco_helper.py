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
import numpy as np
import feagi_connector_mujoco
from feagi_connector import retina
import xml.etree.ElementTree as ET

current_path = feagi_connector_mujoco.__path__
with open(str(current_path[0]) + '/mujoco_config_template.json', 'r') as f:
    config = json.load(f)
TRANSMISSION_TYPES = config['TRANSMISSION_TYPES']
SENSING_TYPES = config['SENSING_TYPES']


def validate_name(name):
    symbols = ['/', '\\']
    for i in symbols:
        if i in name:
            name = name.replace(i, '_')
    return name

def generate_actuator_list(model, xml_actuators_type):
    actuator_information = {}
    counter = 0
    for i in range(model.nu):
        actuator_name = model.actuator(i).name
        if actuator_name == '':
            actuator_name = "actuator_" + str(counter)
            counter += 1
        actuator_name = validate_name(actuator_name)
        actuator_type = xml_actuators_type['output'][actuator_name]['type']
        actuator_information[actuator_name] = {"type": actuator_type, "range": model.actuator_ctrlrange[i]}
    return actuator_information


def generate_sensor_list(model, xml_actuators_type):
    sensor_information = {}
    for i in range(model.nsensor):
        sensor = model.sensor(i)
        sensor_name = sensor.name
        if sensor.type == 7:
            sensor_name = sensor_name[:-4]
        sensor_type = xml_actuators_type['input'][sensor_name]['type']
        sensor_information[sensor_name] = {"type": sensor_type}
    return sensor_information


def generate_capabilities_based_of_xml(sensor_information, actuator_information, capabilities):
    list_to_not_delete_device = ['pressure', 'servo_position']  # Those are automatically exist in mujoco
    temp_copy_property_input = {}
    increment = 0
    # Reading sensors
    for mujoco_device_name in sensor_information:
        device_name = SENSING_TYPES.get(sensor_information[mujoco_device_name]['type'], None)
        if device_name in capabilities['input']:
            if device_name not in list_to_not_delete_device:
                increment = 0
                list_to_not_delete_device.append(device_name)
            elif device_name in list_to_not_delete_device:
                increment += 1
            device_id = str(increment)
            if increment == 0:
                temp_copy_property_input = copy.deepcopy(capabilities['input'][device_name][device_id])
            temp_copy_property_input['custom_name'] = mujoco_device_name
            temp_copy_property_input['feagi_index'] = increment
            capabilities['input'][device_name][device_id] = copy.deepcopy(temp_copy_property_input)

    temp_copy_property_output = {}
    increment = 0
    # Reading actuators
    for mujoco_device_name in actuator_information:
        device_name = TRANSMISSION_TYPES.get(actuator_information[mujoco_device_name]['type'], None)
        range_control = actuator_information[mujoco_device_name]['range']
        if device_name in capabilities['output']:
            if device_name not in list_to_not_delete_device:
                increment = 0
                list_to_not_delete_device.append(device_name)
            elif device_name in list_to_not_delete_device:
                increment += 1
            device_id = str(increment)
            if increment == 0:
                temp_copy_property_output = copy.deepcopy(capabilities['output'][device_name][device_id])
            if device_name == 'servo':
                temp_copy_property_output['max_value'] = range_control[1]
                temp_copy_property_output['min_value'] = range_control[0]
            elif device_name == 'motor':
                temp_copy_property_output['max_power'] = range_control[1]
                temp_copy_property_output['rolling_window_len'] = 2
            temp_copy_property_output['custom_name'] = mujoco_device_name
            temp_copy_property_output['feagi_index'] = increment
            capabilities['output'][device_name][device_id] = copy.deepcopy(temp_copy_property_output)

    temp_capabilities = copy.deepcopy(capabilities)
    for I_O in temp_capabilities:
        for device_name in temp_capabilities[I_O]:
            if device_name not in list_to_not_delete_device:
                del capabilities[I_O][device_name]
    return capabilities


def check_nest_file_from_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Store file paths
    files = [xml_path]

    # Find all include elements directly
    include_elements = root.findall('.//include')

    if include_elements:
        for include in include_elements:
            file_path = include.get('file')
            if file_path:
                print("Found included file:", file_path)
                files.append(file_path)
    return files


def get_actuators(files):
    # Store actuator information in a dictionary
    actuators = {'output': {}}
    counter = 0
    for xml_path in files:
        # Parse the XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the actuator section
        actuator_section = root.find('actuator')

        if actuator_section is not None:
            # Get all children of actuator section (all types of actuators)
            for actuator in actuator_section:
                name = actuator.get('name')
                if name is None:
                    name = "actuator_" + str(counter)
                    counter += 1
                name = validate_name(name)
                actuators['output'][name] = {'type': actuator.tag}
    return actuators


def get_sensors(files, sensors):
    sensors['input'] = {}
    for xml_path in files:
        # Parse the XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the sensor section
        sensor_section = root.find('sensor')

        if sensor_section is not None:
            # Get all children of sensor section (all types of sensors)
            for sensor in sensor_section:
                name = sensor.get('name')
                sensors['input'][name] = {'type': sensor.tag}

                # Get all attributes of the sensor
                for attr_name, attr_value in sensor.attrib.items():
                    if attr_name != 'name':  # Skip name as we already stored it
                        sensors['input'][name][attr_name] = attr_value

                # Get text content if it exists
                if sensor.text and sensor.text.strip():
                    sensors['input'][name]['value'] = sensor.text.strip()

    return sensors


def read_position_from_all_joint(model, data):
    position_list = {}
    for i in range(model.njnt):
        joint = model.joint(i)
        name = joint.name
        if name != '' and name != 'root':
            position_list[name] = data.joint(i).qpos


def generate_pressure_list(model, mujoco, capabilities):
    force_list = get_all_geom_pairs(model, mujoco)
    index = 0
    if 'pressure' in capabilities['input']:
        temp_property = copy.deepcopy(capabilities['input']['pressure'])
        for pair, info in force_list.items():
            if str(index) not in temp_property:
                temp_property[str(index)] = {}
                temp_property[str(index)] = copy.deepcopy(capabilities['input']['pressure']['0'])

            temp_property[str(index)].update({
                'custom_name': pair,
                'feagi_index': index * 3
            })
            index += 1
        del capabilities['input']['pressure']['0']
        capabilities['input']['pressure'] = copy.deepcopy(temp_property)

        return capabilities
    else:
        return {}


def generate_servo_position_list(model, capabilities):
    position_list = get_all_position_data(model)
    temp_property = copy.deepcopy(capabilities['input']['servo_position'])
    for device_index in position_list:
        index = str(device_index)
        for name in position_list[device_index]:
            if index not in temp_property:
                temp_property[index] = {}
                temp_property[index] = copy.deepcopy(capabilities['input']['servo_position']['0'])
            temp_property[index].update({
                'custom_name': name,
                'feagi_index': device_index,
                'max_value': position_list[device_index][name][1],
                'min_value': position_list[device_index][name][0]
            })
    del capabilities['input']['servo_position']['0']
    capabilities['input']['servo_position'] = copy.deepcopy(temp_property)
    return capabilities


def get_all_position_data(model):
    position_list = {}
    for i in range(model.nu):
        actuator_name = model.actuator(i).name
        position_list[i] = {
            actuator_name: model.actuator_ctrlrange[i]
        }
    return position_list


def get_all_geom_pairs(model, mujoco):
    geom_pairs = {}

    # Get total number of geoms
    ngeom = model.ngeom

    # Get all geom names
    for i in range(ngeom):
        for j in range(i + 1, ngeom):  # Only need one direction of pairs
            geom1_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i)
            geom2_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, j)

            # Create key for the pair
            pair_key = f"{geom1_name}_{geom2_name}"

            # Initialize with zero force and None position
            geom_pairs[pair_key] = {
                'force': [0.0, 0.0, 0.0],
                'pos': [0.0, 0.0, 0.0],
                'geom1': geom1_name,
                'geom2': geom2_name,
                'active': False
            }
    return geom_pairs


def read_force(data, force_list, mujoco, model):
    for i in range(data.ncon):
        index = str(i)
        force = np.zeros(6)
        mujoco.mj_contactForce(model, data, i, force)
        obtained_data_from_force = force[:3]
        force_list[index] = list((float(obtained_data_from_force[0]),
                                  float(obtained_data_from_force[1]),
                                  float(obtained_data_from_force[2])))
    return force_list


def read_all_sensors_to_identify_type(model):
    sensor_slice_sizes = {}
    number_to_sensor_name = {26: {'name': 'gyro', "channels": 3}, 37: {'name': 'proximity', 'channels': 1},
                             7: {'name': 'camera', 'channels': 1}}
    start_index = 0
    device_ids = {}  # Dictionary to keep track of device IDs per sensor type

    for i in range(model.nsensor):
        sensor = model.sensor(i)
        id_type_plugin = sensor.type[0]

        if id_type_plugin in [26, 37, 7]:
            name_sensor = number_to_sensor_name[id_type_plugin]['name']

            # Handle camera name differently
            if id_type_plugin == 7:
                device_name = sensor.name[:-4]
            else:
                device_name = sensor.name

            # Initialize device_ids for this sensor type if not exists
            if name_sensor not in device_ids:
                device_ids[name_sensor] = 0

            # If this device hasn't been processed yet
            if device_name not in sensor_slice_sizes:
                sensor_slice_sizes[device_name] = {
                    'name': device_name,
                    'device_id': device_ids[name_sensor],
                    'frame': [start_index, (start_index + number_to_sensor_name[id_type_plugin]['channels'])],
                    'type_plugin': name_sensor
                }
                device_ids[name_sensor] += 1  # Increment the device ID for this sensor type

            # Update frame end index for cameras (and potentially other cumulative sensors)
            if id_type_plugin == 7:
                sensor_slice_sizes[device_name]['frame'][1] = start_index + number_to_sensor_name[id_type_plugin][
                    'channels']

            start_index = start_index + number_to_sensor_name[id_type_plugin]['channels']
    return sensor_slice_sizes


def check_capabilities_with_this_sensor(capabilities, sensor_name):
    return sensor_name in capabilities['input']


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


def read_gyro(data, capabilities, sensor_information):
    gyro_data = {}
    for device_id in sensor_information:
        if sensor_information[device_id]['type_plugin'] == 'gyro':
            for index in capabilities['input']['gyro']:
                quat_id = sensor_information[device_id]['frame'][0]
                quat = data.sensordata[quat_id:quat_id + 4]
                euler_angles = quaternion_to_euler(quat[0], quat[1], quat[2], quat[3])
                gyro_data[index] = np.array([euler_angles[0], euler_angles[1], euler_angles[2]])
    return gyro_data


def read_proximity(data, sensor_information):
    proximity_data = {}
    for device_id in sensor_information:
        if sensor_information[device_id]['type_plugin'] == 'proximity':
            index = sensor_information[device_id]['device_id']
            proximity_data[int(index)] = data.sensordata[sensor_information[device_id]['frame'][0]]
    return proximity_data

def read_lidar(data, sensor_information):
    camera_data = {}
    for device_id in sensor_information:
        if sensor_information[device_id]['type_plugin'] == 'camera':
            index = sensor_information[device_id]['device_id']
            lidar_data = data.sensordata[sensor_information[device_id]['frame'][0]:sensor_information[device_id]['frame'][1]] * 100
            lidar_2d = lidar_data.reshape(16, 16)
            result = np.zeros((16, 16, 3))
            result[:, :, 0] = lidar_2d
            flat_result = result.flatten()

            raw_frame = retina.RGB_list_to_ndarray(flat_result, [16, 16])
            camera_data = {str(index): retina.update_astype(raw_frame)}
    return camera_data


def mujoco_config_parser(category_type, parts_dictionary, config_tree):
    """
    Adds parts configuration to the MuJoCo config tree.

    Args:
        category_type (str): Type category of the parts (e.g., 'sensor', 'actuator')
        parts_dictionary (dict): Dictionary containing part configurations
        config_tree (list): List to store the processed configurations

    Returns:
        list: Updated config tree with new part configurations
    """
    part_config = {
        'name': None,
        'type': category_type,
        'subtype': None,
        'properties': {},
        'children': []
    }

    for part_name, part_data in parts_dictionary.items():
        # Create a new configuration for each part
        current_config = part_config.copy()
        current_config['name'] = part_name
        current_config['subtype'] = part_data['type']


        current_config['properties'] = {
            key: value for key, value in part_data.items()
            if key != 'type' and key != 'name'
        }

        config_tree.append(copy.deepcopy(current_config))
    return config_tree



def generate_config(element, actuator_list, sensor_list):
    part_config = {
        'name': None,
        'type': element.tag,  # Changed from category_type to element.tag
        'feagi device type': None,
        'properties': {},
        'description': '',
        'children': []
    }

    part_config['name'] = element.attrib.get('name')
    if part_config['name'] in actuator_list:
        part_config['feagi device type'] = TRANSMISSION_TYPES[actuator_list[part_config['name']]['type']]
        part_config['type'] = 'output'
        part_config['properties'] = {
            key: element.attrib[key]
            for key in element.attrib
            if key != 'type' and key != 'name'
        }
    elif part_config['name'] in sensor_list:
        part_config['feagi device type'] = SENSING_TYPES[sensor_list[part_config['name']]['type']]
        part_config['type'] = 'input'
        part_config['properties'] = {
            key: element.attrib[key]
            for key in element.attrib
            if key != 'type' and key != 'name'
        }
        # part_config['properties'] = element.attrib.copy()
    else:
        del part_config['feagi device type']
        del part_config['properties']
        part_config['type'] = 'body'

    # Recursively process children
    for child in list(element):
        child_config = generate_config(child, actuator_list, sensor_list)  # inception movie
        if child.tag in ['body', 'joint', 'motor', 'framequat', 'distance', 'rangefinder']: # whatever gets the ball rolling
            part_config['children'].append(child_config)

    return part_config  # Important to return the config!


def mujoco_tree_config(xml_file, actuator_list, sensor_list):
    configs = []  # List to store configurations for each file

    for xml_path in xml_file:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        body_elements = root.findall('.//worldbody')

        for body in body_elements:
            for element in list(body):
                if element.tag == 'body':
                    body_config = generate_config(element, actuator_list, sensor_list)
                    configs.append(body_config)
    # Save first config to JSON with nice formatting
    with open('sample_json.json', 'w') as f:
        json.dump(configs, f, indent=4)

    print("Saved configuration to test.json")
    print("***" * 20)

    return configs
    # print("test: ", xml_file)
    # for xml_path in xml_file:
    #     # Parse the XML file
    #     print("HERE: ", xml_path)
    #     tree = ET.parse(xml_path)
    #     root = tree.getroot()
    #     child_elements = list(root)  # or root.getchildren() in older versions
    #     print("Child elements:", [child.tag for child in child_elements])
    #     print(root, "\n\n")
    #
    #     # Find the sensor section
    #     sensor_section = root.find('worldbody')
    #     child_elements = list(sensor_section)  # or root.getchildren() in older versions
    #     for i in child_elements:
    #         print(list(i))