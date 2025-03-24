import json


def make_capabilities(all_FEAGI_inputs, all_FEAGI_outputs):
    data = {
        "capabilities": {
            "input": {},
            "output": {}
        }
    }


#data["capabilities"]["input"][type] = {}
#adding this line creates an empty feild in capabilities even if there is no device in list



    for inputType in all_FEAGI_inputs:
        if inputType[0] == "accelerometer":
            type = "accelerometer"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": [0, 0, 0],
                    "min_value": [0, 0, 0]
                }


    for inputType in all_FEAGI_inputs:
        if inputType[0] == "analog_input":
            type = "analog_input"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": 1,
                    "min_value": 0
                }

    for inputType in all_FEAGI_inputs:
        if inputType[0] == "battery":
            type = "battery"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": 100,
                    "min_value": 0
                }







    for inputType in all_FEAGI_inputs:
        if inputType[0] == "cameras":
            type = "camera"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
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
        if inputType[0] == "digital_input":
            type = "digital_input"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num
                }


    for inputType in all_FEAGI_inputs:
        if inputType[0] == "gyro":
            type = "gyro"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": [0, 0, 0],
                    "min_value": [0, 0, 0]
                }



    for inputType in all_FEAGI_inputs:
        if inputType[0] == "id_trainer":
            type = "id_trainer"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num
                }

    for inputType in all_FEAGI_inputs:
        if inputType[0] == "infrared":
            type = "infrared"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num
                }


    for inputType in all_FEAGI_inputs:
        if inputType[0] == "pressure":
            type = "pressure"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": [0, 0, 0],
                    "min_value": [0, 0, 0]
                }



    for inputType in all_FEAGI_inputs:
        if inputType[0] == "proximity":
            type = "proximity"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": 0,
                    "min_value": 0
                }


    for inputType in all_FEAGI_inputs:
        if inputType[0] == "servo_position":
            type = "servo_position"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType[1]):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_value": 0,
                    "min_value": 0
                }

#########################################################

    for outputType in all_FEAGI_outputs:
        if outputType[0] == "motors":
            type = "motor"

            data["capabilities"]["output"][type] = {}

            for num, device in enumerate(outputType[1]):
                data["capabilities"]["output"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": num,
                    "max_power": 0,
                    "rolling_window_len": 0
                }


    for outputType in all_FEAGI_outputs:
        if outputType[0] == "servos":
            type = "servo"

            data["capabilities"]["output"][type] = {}

            for num, device in enumerate(outputType[1]):
                data["capabilities"]["output"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "default_value": 0,
                    "disabled": False,
                    "feagi_index": num,
                    "max_power": 0,
                    "max_value": 0,
                    "min_value": 0
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