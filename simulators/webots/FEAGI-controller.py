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
import math
import threading
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

# Get inputs that FEAGI can use in capabilities.json
#all_FEAGI_inputs = []

# Get outputs that FEAGI can use in capabilities.json
#all_FEAGI_outputs = []

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# all possible types of sensors
webots_sensor_types = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", "Gyro",
                       "InertialUnit", "Lidar", "LightSensor", "PositionSensor", "Radar", "RangeFinder",
                       "Receiver", "TouchSensor"]

robot_sensors = {"gyro": [], "pressure": [], "servo_position": [], "proximity": [], "accelerometer": [], "camera": []}

robot_actuators = {"motor": [], "servo": [], "LED": []}

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


    #print(f"robot_actuators - {robot_actuators}")



    for feagi_output_type, commands in obtained_data.items():

        if feagi_output_type == "servo_position":
            for feagi_motor_num, feagi_motor_data in commands.items():
                #loop through robot motors to find the number motor commanded
                for num, robot_motor in enumerate(robot_actuators["servo"]):
                    if num is feagi_motor_num:

                        max_value = capabilities["output"]["servo"][str(num)]["max_value"]
                        min_value = capabilities["output"]["servo"][str(num)]["min_value"]

                        
                        #inc_amount = calculate_increment(min_value, max_value)
                        target_position = robot_motor.getPositionSensor().getValue() + feagi_motor_data

                        if target_position < min_value:
                            target_position = min_value

                        if target_position > max_value:
                            target_position = max_value

                        robot_motor.setPosition(target_position)

        if feagi_output_type == "servo":
            for feagi_motor_num, feagi_motor_data in commands.items():
                #loop through robot motors to find the number motor commanded
                for num, robot_motor in enumerate(robot_actuators["servo"]):
                    if num is feagi_motor_num:

                        if capabilities["output"]["servo"][str(num)]["max_power"] > feagi_motor_data:
                            
                            robot_motor.setVelocity(feagi_motor_data)

        if feagi_output_type == "motor":
            for feagi_motor_num, feagi_motor_data in commands.items():
                #loop through robot motors to find the number motor commanded
                for num, robot_motor in enumerate(robot_actuators["motor"]):
                    if num is feagi_motor_num:


                        max_power = capabilities["output"]["motor"][str(num)]["max_power"]

                        if feagi_motor_data > max_power:
                            feagi_motor_data = max_power

                        #put into velocity mode
                        robot_motor.setPosition(float("inf"))
                        robot_motor.setVelocity(feagi_motor_data)
                        






    # for feagi_output_type in obtained_data:
    #     # MOTOR MOVEMENT
    #     if feagi_output_type == "motor":
    #         # print(f"feagi_motor_list: - {obtained_data["motor"]}")
    #         # feagi_motor_list = {0: 1.0, 1: 0.85, 2: 1.0, 3: 1.0}
    #         feagi_motor_list = obtained_data["motor"]

    #         for motor_number in feagi_motor_list:
    #             value = feagi_motor_list[motor_number]
    #             for device in all_FEAGI_outputs:
    #                 # print(f"device - {device}")
    #                 # device = ('motors', [<controller.motor.Motor object at 0x0000021536F1B7A0>, <controller.motor.Motor object at 0x0000021535EF2EA0>])

    #                 motor_list = device[1]
    #                 # print(f"motor_list - {motor_list}")
    #                 # motor_list = [<controller.motor.Motor object at 0x000002960AB10740>, <controller.motor.Motor object at 0x000002966B4A8050>]

    #                 for num, webot_motor in enumerate(motor_list):

    #                     if num == motor_number:
    #                         # velocity control mode
    #                         webot_motor.setPosition(float("inf"))
    #                         webot_motor.setVelocity(value)

    #     # SERVO Power
    #     if feagi_output_type == "servo":
    #         feagi_servo_list = obtained_data["servo"]

    #         for servo_number in feagi_servo_list:
    #             value = feagi_servo_list[servo_number]

    #             for device in all_FEAGI_outputs:
    #                 servo_list = device[1]
    #                 for num, webot_servo in enumerate(servo_list):
    #                     if num == servo_number:
    #                         # velocity control mode
    #                         webot_servo.setPosition(value)

    #     # SERVO Position
    #     if feagi_output_type == "servo_position":
    #         feagi_servo_position_list = obtained_data["servo_position"]

    #         for servo_position_number in feagi_servo_position_list:
    #             value = feagi_servo_position_list[servo_position_number]
    #             for device in all_FEAGI_outputs:
    #                 servo_position_list = device[1]
    #                 for num, webot_servo_position in enumerate(servo_position_list):
    #                     if num == servo_position_number:
    #                         webot_servo_position.setPosition(value)

# returns the data of given sensor
def get_sensor_data(sensor):
    if type(sensor).__name__ == "TouchSensor":
        if sensor.getType() in (0, 1):  # bumper and force touch sensors
            return sensor.getValue()
        else:  # force-3d touch sensor
            return sensor.getValues()

    elif type(sensor).__name__ in ("DistanceSensor", "LightSensor", "PositionSensor"):
        return sensor.getValue()

    elif type(sensor).__name__ in ("Accelerometer", "Compass", "GPS", "Gyro"):
        return sensor.getValues()

    elif type(sensor).__name__ == "Camera":
        return sensor.getImageArray()

    elif type(sensor).__name__ == "InertialUnit":
        return sensor.getRollPitchYaw()

    elif type(sensor).__name__ == "Lidar":
        return sensor.getRangeImageArray()

    elif type(sensor).__name__ == "Radar":
        return sensor.getTargets()

    elif type(sensor).__name__ == "RangeFinder":
        return sensor.getRangeImageArray()

    elif type(sensor).__name__ == "Receiver":
        if sensor.getQueueLength() != 0:
            return sensor.getBytes()


def sort_devices():
    devices = [robot.getDeviceByIndex(i) for i in range(robot.getNumberOfDevices())]

    for dev in devices:
        device_type = type(dev).__name__
        if device_type in webots_sensor_types:
            dev.enable(timestep)

            if device_type in ("Accelerometer", "InertialUnit"):
                robot_sensors["accelerometer"].append(dev)

            # elif device_type == "Camera":
            #     robot_sensors["camera"].append(dev)

            # elif device_type == "Compass":
            #     robot_sensors["compass"].append(dev)

            elif device_type == "DistanceSensor":
                robot_sensors["proximity"].append(dev)

            # elif device_type == "GPS":
            #     robot_sensors["GPS"].append(dev)

            elif device_type == "Gyro":
                robot_sensors["gyro"].append(dev)

            # elif device_type == "Lidar":
            #     robot_sensors["lidar"].append(dev)

            # elif device_type == "LightSensor":
            #     robot_sensors["light_sensor"].append(dev)

            elif device_type == "PositionSensor":
                robot_sensors["servo_position"].append(dev)

            # elif device_type == "Radar":
            #     robot_sensors["radar"].append(dev)

            # elif device_type == "RangeFinder":
            #     robot_sensors["range_finder"].append(dev)

            # elif device_type == "Receiver":
            #     robot_sensors["receiver"].append(dev)

            elif device_type == "TouchSensor":
                robot_sensors["pressure"].append(dev)

        # if the device is a webots actuator
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

    for device_type, device_list in robot_sensors.items():
        device_list.sort(key=lambda device: device.getName())

    for device_type, device_list in robot_actuators.items():
        device_list.sort(key=lambda device: device.getName())



def calculate_increment(min_value, max_value):
    range_value = abs(max_value - min_value)
    target_steps = 30  # Aim for about 30 steps
    magnitude = int(math.log10(range_value))
    increment = pow(10, magnitude) / 10
    if range_value / increment > target_steps * 2:
        increment *= 5
    elif range_value / increment > target_steps:
        increment *= 2
    elif range_value / increment < target_steps / 2:
        increment /= 2
    return increment




# move the motors to make the robot spin
def pioneer2_wheel_movements():
    # gets the motors
    left_wheel = robot.getDevice("left wheel motor")
    right_wheel = robot.getDevice("right wheel motor")

    print("Pre-move sensors")
    # print_all_ds()
    print()

    # sets velocities opposite eachother, moves and then stops
    left_wheel.setVelocity(-3)
    right_wheel.setVelocity(3)
    robot.step(10 * timestep)
    left_wheel.setVelocity(0)
    right_wheel.setVelocity(0)

    print("Post-move sensors")
    # print_all_ds()
    print("\n")

    # 3 seconds
    robot.step(3000)


def pr2_move_arm(arm, positions):
    """
    Move the PR2 arm to a specified position.
    :param arm: "left" or "right"
    :param positions: Dict with joint angles {joint_name: angle}
    """
    """
    Here is an example of how to call this function:
    move_arm("right", {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.5,
        "upper_arm_roll": 0.0,
        "elbow_lift": -0.5,
        "wrist_roll": 0.0
    })
    """
    # Get PR2 motors for the right arm
    right_arm_motors = {
        "shoulder_pan": robot.getDevice("r_shoulder_pan_joint"),
        "shoulder_lift": robot.getDevice("r_shoulder_lift_joint"),
        "upper_arm_roll": robot.getDevice("r_upper_arm_roll_joint"),
        "elbow_lift": robot.getDevice("r_elbow_flex_joint"),
        "wrist_roll": robot.getDevice("r_wrist_roll_joint")
    }
    # Get PR2 motors for the left arm
    left_arm_motors = {
        "shoulder_pan": robot.getDevice("l_shoulder_pan_joint"),
        "shoulder_lift": robot.getDevice("l_shoulder_lift_joint"),
        "upper_arm_roll": robot.getDevice("l_upper_arm_roll_joint"),
        "elbow_lift": robot.getDevice("l_elbow_flex_joint"),
        "wrist_roll": robot.getDevice("l_wrist_roll_joint")
    }
    if arm == "right":
        motors = right_arm_motors
    elif arm == "left":
        motors = left_arm_motors
    else:
        print("Invalid arm name. Use 'left' or 'right'.")
        return
    for joint, angle in positions.items():
        if joint in motors:
            motors[joint].setPosition(angle)
        else:
            print(f"Invalid joint name: {joint}")


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
    make_capabilities(robot_sensors, robot_actuators)

    # Main Loop
    while True:
        # The controller will grab the data from FEAGI in real-time
        message_from_feagi = pns.message_from_feagi
        if message_from_feagi:  # Verify if the feagi data is not empty
            # Translate from feagi data to human readable data
            obtained_signals = pns.obtain_opu_data(message_from_feagi)  # This is getting data from FEAGI
            # print("obtained_signals", obtained_signals)
            action(obtained_signals)  # THis is for actuator#

        # send sensor data to feagi
        data = {}
        for device_type, device_list in robot_sensors.items():
            if robot_sensors[device_type]:
                if device_type not in data:
                    data[device_type] = {}
                for num, dev in enumerate(device_list):
                    data[device_type][str(num)] = get_sensor_data(dev)


        for sensor_name in data:
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