import json
import math

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


def make_capabilities(sensors, actuators, robot):
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
                        "max_value": [0, 0, 0],
                        "min_value": [0, 0, 0]
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
                        "max_value": [0, 0, 0],
                        "min_value": [0, 0, 0]
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

            elif device_type == "servo_position":
                for num, device in enumerate(device_list):
                    data["capabilities"]["input"][device_type][str(num)] = {
                        "custom_name": device.getName(),
                        "disabled": False,
                        "feagi_index": num,
                        "max_value": 0,
                        "min_value": 0
                    }
                    name = device.getName()
                    if "_sensor" in name:
                        name = name.replace("_sensor", "")
                    actuator_device = robot.getDevice(name)
                    max = actuator_device.getMaxPosition()
                    min = actuator_device.getMinPosition()
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
