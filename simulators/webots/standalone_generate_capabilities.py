import json
import math
from controller import Robot

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# all possible types of sensors
webots_sensor_types = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", "Gyro",
                       "InertialUnit", "Lidar", "LightSensor", "PositionSensor", "Radar", "RangeFinder",
                       "Receiver", "TouchSensor"]

# All data inputs read from the webot robot
robot_sensors = {"gyro": [], "pressure": [], "servo_position": [], "proximity": [], "accelerometer": [], "camera": [],
                 "lidar": [], "compass": []}

# All outputs read from webot robot
robot_actuators = {"motor": [], "servo": [], "LED": []}

# Total number of devices on webot robot
num_devices = robot.getNumberOfDevices()


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

                    # put into velocity mode
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


def make_capabilities(sensors, actuators):

    with open("capabilities.json", "w") as json_file:
        json.dump({}, json_file, indent=4)

    data = {
        "capabilities": {
            "input": {},
            "output": {}
        }
    }

    for device_type, device_list in sensors.items():
        if len(device_list) > 0:
            data["capabilities"]["input"][device_type] = {}

            if device_type == "accelerometer":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": [150, 150, 150], #technically inf
                        "min_value": [-150, -150, -150]
                    }
            elif device_type == "compass":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": [1, 1, 1],
                        "min_value": [-1, -1, -1]
                    }
            elif device_type == "gyro":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": [6, 6, 6], #technically inf
                        "min_value": [-6, -6, -6]
                    }
            elif device_type == "pressure":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": [0, 0, 0],
                        "min_value": [0, 0, 0]
                    }

            elif device_type == "position_sensor":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": 0,
                        "min_value": 0
                    }
                    parent_motor = device.getMotor()
                    max = parent_motor.getMaxPosition()
                    min = parent_motor.getMinPosition()
                    if max != 0.0 and min != 0.0:
                        data["capabilities"]["input"][device_type][str(num)].update({
                            "max_power": calculate_increment(min,max),
                            "max_value": max,
                            "min_value": min,
                        })

            elif device_type == "proximity":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": 0,
                        "min_value": 0
                    }
            elif device_type == "lidar":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": 0,
                        "max_value": 0,
                        "min_value": 0
                    }

            elif device_type == "camera":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
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



    for device_type, device_list in actuators.items():
        if len(device_list) > 0:
            data["capabilities"]["output"][device_type] = {}

            if device_type == "led":
                for num, device in enumerate(device_list):
                    data["capabilities"]["output"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                    }

            elif device_type == "motor":
                for num, device in enumerate(device_list):
                    data["capabilities"]["output"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_power": device.getMaxVelocity(),
                        "rolling_window_len": 2
                    }

            elif device_type == "servo":
                for num, device in enumerate(device_list):
                    data["capabilities"]["output"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "default_value": 0,
                        "disabled": False,
                        "feagi_index": num,
                    }

                    max = device.getMaxPosition()
                    min = device.getMinPosition()

                    data["capabilities"]["output"][device_type][str(num)].update({
                        "max_power": calculate_increment(min,max),
                        "max_value": max,
                        "min_value": min,
                    })

    with open("capabilities.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    print("New JSON Created")


if __name__ == "__main__":
    # Sorts all Webots devices
    sort_devices()

    # Gives time for sensors to get a value
    robot.step(timestep)

    # Make capabilities.json file
    make_capabilities(robot_sensors, robot_actuators)