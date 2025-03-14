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
all_sensors = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", "Gyro", 
            "InertialUnit", "Lidar", "LightSensor", "PositionSensor", "Radar", "RangeFinder",
            "Receiver", "TouchSensor"]

#arrays to store the robots sensors and actuators
robot_sensors = []
robot_actuators = []

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
    recieve_motor_data = actuators.get_motor_data(obtained_data)
    #recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    if recieve_servo_position_data:
        #actuators.setPosition(obtained_data)
        for outputType in all_FEAGI_outputs:
            if outputType == motors:
                for num,motor in enumerate(motors):
                    positionSensor = motor.getPositionSensor()

                    current_position = get_sensor_data(positionSensor)

                    motor.setPosition(float('inf'))
                    motor.setVelocity(recieve_motor_data[num])

                    if abs(current_position - recieve_servo_position_data[num]) < 0.05:
                         motor.setVelocity(0.0)



        pass # output like {0:0.50, 1:0.20, 2:0.30} # example but the data comes from your capabilities' servo range


#returns the data of given sensor
def get_sensor_data(sensor):
    if type(sensor).__name__ == "TouchSensor":
        if sensor.getType() in ("WB_TOUCH_SENSOR_BUMPER", "WB_TOUCH_SENSOR_FORCE"):
            return sensor.getValue()
        else:
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


def make_capabilities_JSON(all_FEAGI_inputs, all_FEAGI_outputs):
    data = {
        "capabilities": {
            "input": {},
            "output": {}
        }
    }


    for inputType in all_FEAGI_inputs:


        if inputType == cameras:

            # Find lidars and add lidars to cameras
            for secondType in all_FEAGI_inputs:
                if secondType == lidars:
                    inputType += secondType

            # Sort the list again
            inputType = sorted(inputType, key=lambda device: device.getName())

            type = "camera"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "eccentricity_control": {
                        "X offset percentage": 1,
                        "Y offset percentage": 1
                    },
                    "feagi_index": num,
                    "index": "00",
                    "mirror": False,
                    "modulation_control": {
                        
                        "X offset percentage": 99,
                        "Y offset percentage": 99
                    },
                    "threshold_default": 50
                }



    for inputType in all_FEAGI_inputs:
        if inputType == gyros:
            type = "gyro"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": [0, 0, 0],
                    "min_value": [0, 0, 0]
                }


    for inputType in all_FEAGI_inputs:
        if inputType == distanceSensors:
            type = "proximity"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": 0,
                    "min_value": 0
                }


    for inputType in all_FEAGI_inputs:
        if inputType == positionSensors:
            type = "servo_position"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": 0,
                    "min_value": 0
                }


    for outputType in all_FEAGI_outputs:
        if outputType == motors:
            type = "motor"

            data["capabilities"]["output"][type] = {}

            for num, device in enumerate(outputType):
                data["capabilities"]["output"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_power": 0,
                    "rolling_window_len": 0
                }

    # for outputType in all_FEAGI_outputs:
    #     if outputType == brakes:
    #         type = "motor"

    #         data["capabilities"]["output"][type] = {}

    #         for num, device in enumerate(outputType):
    #             data["capabilities"]["output"][type][str(num)] = {
    #                 "custom_name": device.getName(),
    #                 "disabled": False,
    #                 "feagi_index": num,
    #                 "max_power": 0,
    #                 "rolling_window_len": 0
    #             }


    with open("capabilities.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    print("New JSON Created")






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


    #put devices into correct arrays and enable sensors
    for i in range(num_devices):
        device = robot.getDeviceByIndex(i)
        device_name = device.getName()
                
        #append to the correct list
        if type(device).__name__ in all_sensors:
            device.enable(timestep)
            robot_sensors.append(device)
        else:
            robot_actuators.append(device)

















    

    #accelerometers
    accelerometer = []
    for device in robot_sensors:
            if "Accelerometer" == type(device).__name__:
                accelerometer.append(device)

    #Sort list by getName value
    accelerometer = sorted(accelerometer, key=lambda device: device.getName())
    all_FEAGI_inputs.append(accelerometer)



    #Cameras
    cameras = []
    for device in robot_sensors:
            if "Camera" == type(device).__name__:
                cameras.append(device)

    #Sort list by getName value
    cameras = sorted(cameras, key=lambda device: device.getName())
    all_FEAGI_inputs.append(cameras)



    #Gyros
    gyros = []
    for device in robot_sensors:
            if "Gyro" == type(device).__name__:
                gyros.append(device)

    #Sort list by getName value
    gyros = sorted(gyros, key=lambda device: device.getName())
    all_FEAGI_inputs.append(gyros)



    #Pressure Sensors
    pressureSensors = []
    for device in robot_sensors:
            if "TouchSensor" == type(device).__name__:
                pressureSensors.append(device)

    #Sort list by getName value
    pressureSensors = sorted(pressureSensors, key=lambda device: device.getName())
    all_FEAGI_inputs.append(pressureSensors)



    #Distance Sensors
    distanceSensors = []
    for device in robot_sensors:
            if "DistanceSensor" == type(device).__name__:
                distanceSensors.append(device)

    #Sort list by getName value
    distanceSensors = sorted(distanceSensors, key=lambda device: device.getName())
    all_FEAGI_inputs.append(distanceSensors)



    #Position Sensors
    positionSensors = []
    for device in robot_sensors:
            if "PositionSensor" == type(device).__name__:
                positionSensors.append(device)

    #Sort list by getName value
    positionSensors = sorted(positionSensors, key=lambda device: device.getName())
    all_FEAGI_inputs.append(positionSensors)



    #Lidars
    lidars = []
    for device in robot_sensors:
            if "Lidar" == type(device).__name__:
                lidars.append(device)

    #Sort list by getName value
    lidars = sorted(lidars, key=lambda device: device.getName())
    all_FEAGI_inputs.append(lidars)


    #Compass
    Compasses = []
    for device in robot_sensors:
            if "Compass" == type(device).__name__:
                Compasses.append(device)

    #Sort list by getName value
    Compasses = sorted(Compasses, key=lambda device: device.getName())
    all_FEAGI_inputs.append(Compasses)











    #All types of motors now
    motors = []
    for device in robot_actuators:
            if "Motor" == type(device).__name__:
                motors.append(device)

    #Sort list by getName value
    motors = sorted(motors, key=lambda device: device.getName())
    all_FEAGI_outputs.append(motors)



    #All LEDS
    leds = []
    for device in robot_actuators:
            if "LED" == type(device).__name__:
                leds.append(device)

    #Sort list by getName value
    leds = sorted(leds, key=lambda device: device.getName())
    all_FEAGI_outputs.append(leds)


    #Brakes
    brakes = []
    for device in robot_actuators:
            if "Brake" == type(device).__name__:
                brakes.append(device)

    #Sort list by getName value
    brakes = sorted(brakes, key=lambda device: device.getName())
    all_FEAGI_outputs.append(brakes)



    #Connectors
    connectors = []
    for device in robot_actuators:
            if "Connector" == type(device).__name__:
                connectors.append(device)

    #Sort list by getName value
    connectors = sorted(connectors, key=lambda device: device.getName())
    all_FEAGI_outputs.append(connectors)




    #Displays
    displays = []
    for device in robot_actuators:
            if "Display" == type(device).__name__:
                displays.append(device)

    #Sort list by getName value
    displays = sorted(displays, key=lambda device: device.getName())
    all_FEAGI_outputs.append(displays)




    #Emitters
    emitters = []
    for device in robot_actuators:
            if "Emitter" == type(device).__name__:
                emitters.append(device)

    #Sort list by getName value
    emitters = sorted(emitters, key=lambda device: device.getName())
    all_FEAGI_outputs.append(emitters)



    #Pens
    pens = []
    for device in robot_actuators:
            if "Pen" == type(device).__name__:
                pens.append(device)

    #Sort list by getName value
    pens = sorted(pens, key=lambda device: device.getName())
    all_FEAGI_outputs.append(pens)



    #Propeller
    propellers = []
    for device in robot_actuators:
            if "Propeller" == type(device).__name__:
                propellers.append(device)

    #Sort list by getName value
    propellers = sorted(propellers, key=lambda device: device.getName())
    all_FEAGI_outputs.append(propellers)



    #Speakers
    speakers = []
    for device in robot_actuators:
            if "Speaker" == type(device).__name__:
                speakers.append(device)

    #Sort list by getName value
    speakers = sorted(speakers, key=lambda device: device.getName())
    all_FEAGI_outputs.append(speakers)



    #Track
    tracks = []
    for device in robot_actuators:
            if "Track" == type(device).__name__:
                tracks.append(device)

    #Sort list by getName value
    tracks = sorted(tracks, key=lambda device: device.getName())
    all_FEAGI_outputs.append(tracks)




    make_capabilities_JSON(all_FEAGI_inputs, all_FEAGI_outputs)
















    # Main Loop
    while True:
        # The controller will grab the data from FEAGI in real-time
        message_from_feagi = pns.message_from_feagi
        if message_from_feagi: # Verify if the feagi data is not empty
            # Translate from feagi data to human readable data
            obtained_signals = pns.obtain_opu_data(message_from_feagi) # This is getting data from FEAGI
            action(obtained_signals, capabilities) # THis is for actuator#



        # Send Gyro Sensor data to FEAGI
        for num, gyro in enumerate(gyros):

            gyro_data = {str(num): get_sensor_data(gyro)}
            #print(gyro_data)

            message_to_feagi = sensors.create_data_for_feagi('gyro', capabilities, message_to_feagi, current_data=gyro_data, symmetric=True, measure_enable=True)
            
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()



        # Send Motor Position Sensor data to FEAGI
        for num, positionSensor in enumerate(positionSensors):

            positionSensor_data = {str(num): get_sensor_data(positionSensor)}
            #print(positionSensor_data)

            message_to_feagi = sensors.create_data_for_feagi('servo_position', capabilities, message_to_feagi, current_data=positionSensor_data, symmetric=True, measure_enable=True)

            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()



        # Send Proximity Sensor data to FEAGI
        for num, distanceSensor in enumerate(distanceSensors):

            distanceSensor_data = {str(num): get_sensor_data(distanceSensor)}
            #print(distanceSensor_data)

            message_to_feagi = sensors.create_data_for_feagi('proximity', capabilities, message_to_feagi, current_data=distanceSensor_data, symmetric=True, measure_enable=True)

            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()



        # cool down everytime
        sleep(feagi_settings['feagi_burst_speed'])
        robot.step(timestep)
