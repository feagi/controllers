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

import copy
import xml.etree.ElementTree as ET

TRANSMISSION_TYPES = {
    'position': 'servo',
    'motor': 'motor'
}

SENSING_TYPES = {
    'framequat': 'gyro',
    'distance': 'proximity',
    'rangefinder': 'camera'
}


def generate_actuator_list(model, xml_actuators_type):
    actuator_information = {}
    for i in range(model.nu):
        actuator_name = model.actuator(i).name
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
    list_to_not_delete_device = []
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
                print("worked")
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
                actuators['output'][name] = {
                    'type': actuator.tag}
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
    return sensors
