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
import mujoco.viewer
import config_parse as mj_lib

xml_actuators_type = dict()


def obtain_xml(xml):
    return xml


def update_actuator_and_sensor(xml_file):
    model = mujoco.MjModel.from_xml_path(xml_file)
    files = mj_lib.check_nest_file_from_xml(xml_file)
    xml_info = mj_lib.get_actuators(files)
    xml_info = mj_lib.get_sensors(files, xml_info)
    return model, xml_info, files


if __name__ == '__main__':
    xml_file = "./humanoid.xml"  # This is where you can change file or use xml string, up to u
    model, xml_actuators_type, files = update_actuator_and_sensor(
        xml_file)  # This will generate all necessary for actuator and sensor information

    # MUJOCO CUSTOM CODE USING MUJOCO_LIBRARY FILE
    data = mujoco.MjData(
        model)  # loads mujoco data to generate list from engine (not using actual engine at this point)

    actuator_information = mj_lib.generate_actuator_list(model,
                                                         xml_actuators_type)  # Just obtain the actuator list that mujoco_tree_config needs

    sensor_information = mj_lib.generate_sensor_list(model,
                                                     xml_actuators_type)  # Just obtain the sensor list that mujoco_tree_config needs

    config_dict = mj_lib.mujoco_tree_config(files, actuator_information, sensor_information)  # get dict of config

    mj_lib.convert_dict_to_json(config_dict)  # This is where you just send json to anywhere.
