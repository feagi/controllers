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
all_FEAGI_inputs = []

# Get outputs that FEAGI can use in capabilities.json
all_FEAGI_outputs = []


# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

#all possible types of sensors           
webots_sensor_types = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", "Gyro", 
            "InertialUnit", "Lidar", "LightSensor", "PositionSensor", "Radar", "RangeFinder",
            "Receiver", "TouchSensor"]

robot_sensors = {"gyro" : [], "pressure" : [], "servo_position" : [], "proximity" : [], "accelerometer" : [], "camera" : []}

robot_actuators = {"motor" : [], "servo" : [], "LED" : []}

num_devices = robot.getNumberOfDevices()

def action(obtained_data, capabilities):
    """
    This is where you can make the robot do something based on FEAGI data. The variable
    obtained_data contains the data from FEAGI. The variable capabilities comes from
    the configuration.json file. It will need the capability to measure how much power it can control
    and calculate using the FEAGI data.

    obtained_data: dictionary.
    capabilities: dictionary.
    """

    print(f"ACTION METHOD-----{obtained_data}")
    #print(all_FEAGI_outputs)

    #print(f"obtained_data - {obtained_data}")
    #obtained_data = {'motor': {0: 0.85, 2: 1.0, 3: 1.0, 1: 0.95}, 'servo': {0: 0.85, 2: 1.0, 1: 0.95, 3: 1.0}}

    for feagi_output_type in obtained_data:
        #print(f"feagi_output_type in obtained_data: - {feagi_output_type}")
        #feagi_output_type = motor


        #MOTOR MOVEMENT
        if feagi_output_type == "motor":
            #print(f"feagi_motor_list: - {obtained_data["motor"]}")
            #feagi_motor_list = {0: 1.0, 1: 0.85, 2: 1.0, 3: 1.0}

            feagi_motor_list = obtained_data["motor"]

            for motor_number in feagi_motor_list:
                #print(f"motor: - {motor_number}")
                #motor = 2

                value = feagi_motor_list[motor_number]
                #print(f"value - {value}")
                #value = 2.0

                for device in all_FEAGI_outputs:
                    #print(f"device - {device}")
                    #device = ('motors', [<controller.motor.Motor object at 0x0000021536F1B7A0>, <controller.motor.Motor object at 0x0000021535EF2EA0>])

                    motor_list = device[1]
                    #print(f"motor_list - {motor_list}")
                    # motor_list = [<controller.motor.Motor object at 0x000002960AB10740>, <controller.motor.Motor object at 0x000002966B4A8050>]

                    for num, webot_motor in enumerate(motor_list):
                        #print(f"webot_motor - {webot_motor.getName()}")
                        #webot_motor = right wheel motor

                        if num == motor_number:
                            #velocity control mode
                            webot_motor.setPosition(float("inf"))
                            webot_motor.setVelocity(value)


        #SERVO Power
        if feagi_output_type == "servo":
            #print(f"feagi_motor_list: - {obtained_data["motor"]}")
            #feagi_motor_list = {0: 1.0, 1: 0.85, 2: 1.0, 3: 1.0}

            feagi_servo_list = obtained_data["servo"]

            for servo_number in feagi_servo_list:
                #print(f"motor: - {motor_number}")
                #motor = 2

                value = feagi_servo_list[servo_number]
                #print(f"value - {value}")
                #value = 2.0

                for device in all_FEAGI_outputs:
                    #print(f"device - {device}")
                    #device = ('motors', [<controller.motor.Motor object at 0x0000021536F1B7A0>, <controller.motor.Motor object at 0x0000021535EF2EA0>])

                    servo_list = device[1]
                    #print(f"motor_list - {motor_list}")
                    # motor_list = [<controller.motor.Motor object at 0x000002960AB10740>, <controller.motor.Motor object at 0x000002966B4A8050>]

                    for num, webot_servo in enumerate(servo_list):
                        #print(f"webot_motor - {webot_motor.getName()}")
                        #webot_motor = right wheel motor

                        if num == servo_number:
                            #velocity control mode
                            webot_servo.setVelocity(value)
            
        #SERVO Position
        if feagi_output_type == "servo_position":
            #print(f"feagi_motor_list: - {obtained_data["motor"]}")
            #feagi_motor_list = {0: 1.0, 1: 0.85, 2: 1.0, 3: 1.0}

            feagi_servo_position_list = obtained_data["servo_position"]

            for servo_position_number in feagi_servo_position_list:
                #print(f"motor: - {motor_number}")
                #motor = 2

                value = feagi_servo_position_list[servo_position_number]
                #print(f"value - {value}")
                #value = 2.0

                for device in all_FEAGI_outputs:
                    #print(f"device - {device}")
                    #device = ('motors', [<controller.motor.Motor object at 0x0000021536F1B7A0>, <controller.motor.Motor object at 0x0000021535EF2EA0>])

                    servo_position_list = device[1]
                    #print(f"motor_list - {motor_list}")
                    # motor_list = [<controller.motor.Motor object at 0x000002960AB10740>, <controller.motor.Motor object at 0x000002966B4A8050>]

                    for num, webot_servo_position in enumerate(servo_position_list):
                        #print(f"webot_motor - {webot_motor.getName()}")
                        #webot_motor = right wheel motor

                        if num == servo_position_number:
                            #velocity control mode
                            webot_servo_position.setPosition(value)








            # for deviceType in all_FEAGI_outputs:

            #     if deviceType[0] == "motors":

            #         for motor in deviceType[1]:
                         
            #              motor.setVelocity(feagi_output_type.get())
                #print(deviceType)
                #if deviceType[0] == "motor":
                #    print(f"motor list - {deviceType[1]}")

    
    # if recieve_motor_data:
    #     print(f"recieve_motor_data -- {recieve_motor_data}")

    #     for outputType in all_FEAGI_outputs:
    #         if outputType == 'motors':
    #             for num, motor in enumerate(outputType):
    #                 if num in recieve_motor_data:
    #                     motor.setVelocity(recieve_motor_data[num])

    # if recieve_servo_data:
    #     print(f"recieve_servo_data -- {recieve_servo_data}")

    #     for outputType in all_FEAGI_outputs:
    #         if outputType == 'motors':
    #             for num, motor in enumerate(outputType):
    #                 if num in recieve_motor_data:
    #                     motor.setVelocity(recieve_motor_data[num])

    # if recieve_servo_position_data:
    #     print(f"recieve_servo_position_data -- {recieve_servo_position_data}")
    #     for outputType in all_FEAGI_outputs:
    #         if outputType == 'motors':
    #             for num,motor in enumerate(motors):
    #                 positionSensor = motor.getPositionSensor()
    #                 current_position = get_sensor_data(positionSensor)
    #                 motor.setPosition(float('inf'))
    #                 if abs(current_position - recieve_servo_position_data[num]) < 0.05:
    #                     motor.setVelocity(0.0)


    # pass # output like {0:0.50, 1:0.20, 2:0.30} # example but the data comes from your capabilities' servo range


#returns the data of given sensor
def get_sensor_data(sensor):
    if type(sensor).__name__ == "TouchSensor":
        if sensor.getType() in (0, 1): #bumper and force touch sensors
            return sensor.getValue()
        else: #force-3d touch sensor
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

            elif device_type == "Camera":
                robot_sensors["camera"].append(dev)

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

        #if the device is a webots actuator
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
                if (dev.getMinPosition == 0 and dev.getMaxPosition == 0):
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

#move the motors to make the robot spin
def pioneer2_wheel_movements():
    #gets the motors
    left_wheel = robot.getDevice("left wheel motor")
    right_wheel = robot.getDevice("right wheel motor")

    print("Pre-move sensors")
    #print_all_ds()
    print()
            
    #sets velocities opposite eachother, moves and then stops
    left_wheel.setVelocity(-3)
    right_wheel.setVelocity(3)
    robot.step(10 * timestep)
    left_wheel.setVelocity(0)
    right_wheel.setVelocity(0)

    print("Post-move sensors")
    #print_all_ds()
    print("\n")
    
    #3 seconds
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
                     args=(default_capabilities,feagi_settings, camera_data), daemon=True).start()


    sort_devices()
    robot.step(timestep) #ensures that all sensors have had time to make a measurement, avoids null pointers
    # make_capabilities(all_FEAGI_inputs, all_FEAGI_outputs)
    make_capabilities(robot_sensors, robot_actuators)



    # Main Loop
    while True:
        # The controller will grab the data from FEAGI in real-time
        message_from_feagi = pns.message_from_feagi
        if message_from_feagi: # Verify if the feagi data is not empty
            # Translate from feagi data to human readable data
            obtained_signals = pns.obtain_opu_data(message_from_feagi) # This is getting data from FEAGI
            print("obtained_signals",obtained_signals)
            action(obtained_signals, capabilities) # THis is for actuator#

        #send sensor data to feagi
        for device_type, device_list in robot_sensors.items():
            for num, dev in enumerate(device_list):
                data = {str(num): get_sensor_data(dev)}
                message_to_feagi = sensors.create_data_for_feagi(device_type, capabilities, message_to_feagi, current_data = data, symmetric= True, measure_enable = True)
                pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)

        # # Send Gyro Sensor data to FEAGI
        # gyro = robot_sensors.get("gyro")
        # for num, gyro_sensor in enumerate(gyro):

        #     gyro_data = {str(num): get_sensor_data(gyro_sensor)}
        #     #print(gyro_data)

        #     message_to_feagi = sensors.create_data_for_feagi('gyro', capabilities, message_to_feagi, current_data=gyro_data, symmetric=True, measure_enable=True)
            
        #     pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        #     #message_to_feagi.clear()



        # # Send Motor Position Sensor data to FEAGI
        # servo_position = robot_sensors.get("servo_position")
        # for num, positionSensor in enumerate(servo_position):

        #     positionSensor_data = {str(num): get_sensor_data(positionSensor)}
        #     #print(positionSensor_data)

        #     message_to_feagi = sensors.create_data_for_feagi('servo_position', capabilities, message_to_feagi, current_data=positionSensor_data, symmetric=True, measure_enable=True)

        #     pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        #     #message_to_feagi.clear()



        # # Send Proximity Sensor data to FEAGI
        # proximity = robot_sensors.get("proximity")
        # for num, distanceSensor in enumerate(proximity):

        #     distanceSensor_data = {str(num): get_sensor_data(distanceSensor)}
        #     #print(distanceSensor_data)

        #     message_to_feagi = sensors.create_data_for_feagi('proximity', capabilities, message_to_feagi, current_data=distanceSensor_data, symmetric=True, measure_enable=True)

        #     pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        #     #message_to_feagi.clear()

        message_to_feagi.clear()


        # cool down everytime
        sleep(feagi_settings['feagi_burst_speed'])
        robot.step(timestep)
