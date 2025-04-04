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
import json
import math
import traceback
import threading
import numpy as np
from time import sleep
from controller import Robot
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import retina as retina
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from capabilities_generator import make_capabilities
from feagi_connector import feagi_interface as feagi

# Global variable section
camera_data = {"vision": []}  # This will be heavily relies for vision

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# all possible types of sensors
webots_sensor_types = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", "Gyro",
                       "InertialUnit", "Lidar", "LightSensor", "PositionSensor", "Radar", "RangeFinder",
                       "Receiver", "TouchSensor"]

# All data inputs read from the webot robot
robot_sensors = {"gyro": [], "pressure": [], "servo_position": [], "proximity": [], "accelerometer": [], "camera": [], "lidar": []}

testing_sensors = {"compass": []}

# All outputs read from webot robot
robot_actuators = {"motor": [], "servo": [], "LED": []}

# Total number of devices on webot robot
num_devices = robot.getNumberOfDevices()


def action(obtained_data):
    """
    This is where you can make the robot do something based on FEAGI data. The variable
    obtained_data contains the data from FEAGI. The variable capabilities comes from
    the configuration.json file. It will need the capability to measure how much power it can control
    and calculate using the FEAGI data.

    obtained_data: dictionary.
    capabilities: dictionary.
    """

    # Splits obtained_data into motor types
    recieve_motor_data = actuators.get_motor_data(obtained_data)
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    #Will fully move the servo to the recieved position
    if recieve_servo_position_data:
        for device_num in recieve_servo_position_data:
            robot_actuators["servo"][device_num].setPosition(recieve_servo_position_data[device_num])

    #Will increment the servo by recieved amount
    if recieve_servo_data:
        for device_num in recieve_servo_data:  # example output: {0: 100, 2: 100}
            robot_actuators["servo"][device_num].setPosition(recieve_servo_data[device_num])

    #Will set motor velocity by recieved amount
    if recieve_motor_data:
        for device_num in recieve_motor_data:
            robot_actuators["motor"][device_num].setVelocity(recieve_motor_data[device_num])


# Returns the data of given sensor
def get_sensor_data(sensor):
    if type(sensor).__name__ == "TouchSensor":
        if sensor.getType() in (0, 1):  # bumper and force touch sensors
            return [sensor.getValue(), 0, 0] # getValue only returns info about the x direction
        else:  # force-3d touch sensor
            return sensor.getValues()

    elif type(sensor).__name__ in ("DistanceSensor", "LightSensor", "PositionSensor"):
        return sensor.getValue()

    elif type(sensor).__name__ in ("Accelerometer", "Compass", "GPS", "Gyro"):
        return sensor.getValues()

    elif type(sensor).__name__ == "Camera":
        # print(f"height ---- {sensor.getWidth()}")
        # print(f"width ---- {sensor.getHeight()}")
        # print(f"LENGTH ---- {len(sensor.getImage().tolist())}")
    #           for (i = width / 3; i < 2 * width / 3; i++) {
    #     for (j = height / 2; j < 3 * height / 4; j++) {
    #       red += wb_camera_image_get_red(image, width, i, j);
    #       blue += wb_camera_image_get_blue(image, width, i, j);
    #       green += wb_camera_image_get_green(image, width, i, j);
    #     }
    #   }


        image_string = sensor.getImage()
        image_width = sensor.getWidth()
        image_height = sensor.getHeight()
        # for x in sensor.getWidth():
        #     for y in sensor.getHeight():
        #         print(Camera.imageGetRed(image, image_width,))


        # print(sensor.getImage())
        uint8_array = np.frombuffer(image_string, dtype=np.uint8)
        #put it in 4 channels but then delete alpha channel.
        rgb_image = uint8_array.reshape((image_height, image_width, 4))[:, :, :3]
        cv2.imshow("RGB Image", rgb_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return uint8_array

    elif type(sensor).__name__ == "InertialUnit":
        return sensor.getRollPitchYaw()

    elif type(sensor).__name__ == "Lidar":
        return sensor.getRangeImageArray()

    elif type(sensor).__name__ == "Radar":
        data = sensor.getTargets()
        if data:
            return data[0].distance
        else:
            return data

    elif type(sensor).__name__ == "RangeFinder":
        return sensor.getRangeImageArray()

    elif type(sensor).__name__ == "Receiver":
        if sensor.getQueueLength() != 0:
            return sensor.getBytes()

# Reads all devices on webots robot and sorts into its type list

def convert_lidar_to_feagi_data(full_lidar_data, cortical_size, max_data, min_data):
    result = {'ilidar': {}}
    total_array = []
    counter = 0
    length_based_off_cortical = int(len(full_lidar_data) / cortical_size)
    for x in range(len(full_lidar_data)): # grab
        if full_lidar_data[x] == float('inf'):
            full_lidar_data[x] = max_data
        if full_lidar_data[x] == float('-inf'):
            full_lidar_data[x] = min_data
        total_array.append(1 / full_lidar_data[x])
        if len(total_array) == length_based_off_cortical:
            name = (counter, 0, 0)
            counter += 1
            try:
                result['ilidar'][name] = sum(total_array) // len(total_array)
                total_array.clear()
            except:
                traceback.print_exc()
    return result

def sort_devices():
    devices = [robot.getDeviceByIndex(i) for i in range(robot.getNumberOfDevices())]

    for dev in devices:
        device_type = type(dev).__name__
        if device_type in webots_sensor_types:
            dev.enable(timestep)

            if device_type in ("Accelerometer", "InertialUnit"):
                robot_sensors["accelerometer"].append(dev)

            elif device_type == "Camera":
                robot_sensors["camera"].append(dev)

            elif device_type == "Compass":
                if "compass" not in robot_sensors:
                    robot_sensors['compass'] = []
                robot_sensors["compass"].append(dev)

            elif device_type == "DistanceSensor":
                robot_sensors["proximity"].append(dev)

            # elif device_type == "GPS":
            #     robot_sensors["GPS"].append(dev)

            elif device_type == "Gyro":
                robot_sensors["gyro"].append(dev)

            elif device_type == "Lidar":
                robot_sensors["lidar"].append(dev)

            # elif device_type == "LightSensor":
            #     robot_sensors["light_sensor"].append(dev)

            elif device_type == "PositionSensor":
                robot_sensors["servo_position"].append(dev)

            elif device_type == "Radar":
                robot_sensors["proximity"].append(dev)

            # elif device_type == "RangeFinder":
            #     robot_sensors["range_finder"].append(dev)

            # elif device_type == "Receiver":
            #     robot_sensors["receiver"].append(dev)

            elif device_type == "TouchSensor":
                robot_sensors["pressure"].append(dev)

        # Sorts robots actuators
        else:
            # if device_name == "Brake":
            #     robot_actuators["brake"].append(dev)

            # elif device_name == "Connector":
            #     robot_actuators["connector"].append(dev)

            # elif device_name == "Display":
            #     robot_actuators["display"].append(dev)

            # elif device_name == "Emitter":
            #     robot_actuators["emitter"].append(dev)

            if device_type == "LED":
                robot_actuators["LED"].append(dev)

            if device_type == "Motor":
                if (dev.getMinPosition() == 0 and dev.getMaxPosition() == 0):

                    #put into velocity mode
                    dev.setPosition(float("inf"))

                    robot_actuators["motor"].append(dev)
                else:
                    robot_actuators["servo"].append(dev)

            # elif device_name == "Muscle":
            #     robot_actuators["muscle"].append(dev)

            # elif device_name == "Pen":
            #     robot_actuators["pen"].append(dev)

            # elif device_name == "Propeller":
            #     robot_actuators["propeller"].append(dev)

            # elif device_name == "Speaker":
            #     robot_actuators["speaker"].append(dev)

            # elif device_name == "Track":
            #     robot_actuators["track"].append(dev)


    # Sorts lists by alphabetical order of its specific name
    for device_type, device_list in robot_sensors.items():
        device_list.sort(key=lambda device: device.getName())

    for device_type, device_list in robot_actuators.items():
        device_list.sort(key=lambda device: device.getName())


if __name__ == "__main__":

    # Generate runtime dictionary
    runtime_data = {"vision": [], "stimulation_period": None, "feagi_state": None,
                    "feagi_network": None}

    # This function will build the capabilities from your configuration.json and read the
    # args input. First, it will gather all details from your configuration.json. Once it's done,
    # it will read all input args, such as flags. Once it detects flags from the user, it will override
    # the configuration and use the input provided by the user.
    config = feagi.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # Simply copying and pasting the code below will do the full work for you. It basically checks
    # and updates the network to ensure that it can connect with FEAGI. If it doesn't find FEAGI,
    # it will just wait and display "waiting on FEAGI...".
    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # The function `create_runtime_default_list` will design and generate a complete JSON object
    # in the configuration, mainly for vision only. Once it's done, it will get the configuration JSON,
    # override all keys generated by this function, and store them into the same capabilities for
    # the rest of controller runtime.
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)

    threading.Thread(target=retina.vision_progress,
                     args=(default_capabilities, feagi_settings, camera_data), daemon=True).start()

    sort_devices()
    robot.step(timestep)  # ensures that all sensors have had time to make a measurement, avoids null pointers
    # make_capabilities(all_FEAGI_inputs, all_FEAGI_outputs)
    make_capabilities(robot_sensors, robot_actuators, robot)

    # Main Loop
    while True:
        # The controller will grab the data from FEAGI in real-time
        message_from_feagi = pns.message_from_feagi
        if message_from_feagi:  # Verify if the feagi data is not empty
            # Translate from feagi data to human readable data
            obtained_signals = pns.obtain_opu_data(message_from_feagi)  # This is getting data from FEAGI
            # print("obtained_signals", obtained_signals)
            action(obtained_signals)  # THis is for actuator#



        test_data = {}
        for device_type, device_list in testing_sensors.items():
            if testing_sensors[device_type]:
                if device_type not in test_data:
                    test_data[device_type] = {}
                for num, dev in enumerate(device_list):
                    test_data[device_type][str(num)] = get_sensor_data(dev)
        
        print(f"compass - {test_data}")








        # send sensor data to feagi
        data = {}
        for device_type, device_list in robot_sensors.items():
            if robot_sensors[device_type]:
                if device_type not in data:
                    data[device_type] = {}
                for num, dev in enumerate(device_list):
                    data[device_type][str(num)] = get_sensor_data(dev)


        for sensor_name in data:
            if sensor_name == "lidar":
                for index in data[sensor_name]:
                    max_range = robot_sensors[sensor_name][int(index)].getMaxRange()
                    min_range = robot_sensors[sensor_name][int(index)].getMinRange()
                    new_data = convert_lidar_to_feagi_data(data[sensor_name][index][0], len(data[sensor_name][index][0]), max_range, min_range)
                    message_to_feagi = sensors.add_generic_input_to_feagi_data(
                        new_data,
                        message_to_feagi)
            else:
                message_to_feagi = sensors.create_data_for_feagi(
                                        sensor_name,
                                        capabilities,
                                        message_to_feagi,
                                        current_data=data[sensor_name],
                                        symmetric=True,
                                        measure_enable=True)


        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        message_to_feagi.clear()

        # cool down everytime
        sleep(feagi_settings['feagi_burst_speed'])
        robot.step(timestep)