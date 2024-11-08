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
from time import sleep
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import retina as retina
from feagi_connector import feagi_interface as feagi
from mistyPy import Robot
import threading
from datetime import datetime
from collections import deque
from websockets.sync.client import connect
import json

camera_data = {"vision": []}
servo_status = {}
feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator



# def getting_websocket_data():
#     print("websocket connected")
#     with connect("ws://192.168.50.237/pubsub") as websocket:
#         subscribe_msg = {
#             "Operation": "subscribe",
#             "Type": "IMU",
#             "DebounceMs": 1,
#             "EventName": "IMU",
#             "Message": "",
#             "ReturnProperty": "",
#             "EventConditions": []
#         }
#         websocket.send(json.dumps(subscribe_msg))
#         while True:
#             message = json.loads(websocket.recv())
#             print(f"Received: {message}")

def process_video(capabilities, misty):
    while True:
        try:
            data = misty.camera_rgb()
            camera_data["vision"] = data
        except KeyboardInterrupt:
            break
        sleep(0.01)


def action(obtained_data):
    recieve_motor_data = actuators.get_motor_data(obtained_data,
                                                  capabilities['motor']['power_amount'],
                                                  capabilities['motor']['count'], rolling_window,
                                                  id_converter=False)
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    if recieve_motor_data:
        wheel_speeds = {"ff": 0, "fb": 0, "lf": 0, "lb": 0}
        for id in recieve_motor_data:
            if id in [0, 1]:
                wheel_speeds["f" + ["f", "b"][id]] = float(recieve_motor_data[id])
            if id in [2, 3]:
                wheel_speeds["l" + ["f", "b"][id - 2]] = float(recieve_motor_data[id])
        forward_backward = wheel_speeds["ff"] - wheel_speeds["fb"]
        left_right = wheel_speeds["lf"] - wheel_speeds["lb"]
        misty.drive(forward_backward, left_right)
    else:
        misty.stop()

    if recieve_servo_data:
        for id in recieve_servo_data:  # example output: {0: 100, 2: 100}
            current_id = id // 2
            if current_id not in servo_status:
                servo_status[current_id] = 0
            if id in [0, 1]:
                servo_power = actuators.servo_generate_power(34.9, recieve_servo_data[id], id)
                servo_status[current_id] += servo_power / 100
                power = servo_status[current_id]
                servo_status[current_id] = actuators.servo_keep_boundaries(power, 34.9, -9)
                if (servo_status[current_id] != 34.9) and (servo_status[current_id] != -9):
                    misty.moveHeadDegrees(0, servo_status[current_id], 0, 100)
            if id in [2, 3]:
                servo_power = actuators.servo_generate_power(43, recieve_servo_data[id], id)
                servo_status[current_id] += servo_power / 100
                power = servo_status[current_id]
                servo_status[current_id] = actuators.servo_keep_boundaries(power, 43, -43)
                if (servo_status[current_id] != 43) and (servo_status[current_id] != -43):
                    misty.moveHeadDegrees(servo_status[current_id], servo_status[0], 0,
                                          100)  # hardcoded, whatever. misty is so API based zzz
                    # needs websocket to make it super smooth. Hopefully, misty can be updated to
                    # websocket only instead of https to move head/arms/drive
    if 'servo_position' in obtained_data:
        print(obtained_data)
        try:
            head_flag = False
            arms_flag = False
            if obtained_data['servo_position']:
                for data_point in obtained_data['servo_position']:
                    device_id = data_point // 2
                    if not all(key in servo_status for key in range(5)):
                        for i in range(5):
                            servo_status[i] = 0
                    if data_point == 0:
                        encoder_position = ((obtained_data['servo_position'][data_point] - 0) / (
                                20 - 0)) * (capabilities['servo']['servo_range'][str(0)][1] -
                                            capabilities['servo']['servo_range'][str(0)][0]) \
                                           + capabilities['servo']['servo_range'][str(0)][0]
                        servo_status[0] = encoder_position
                        head_flag = True
                    if data_point == 1:
                        encoder_position = ((obtained_data['servo_position'][data_point] - 0) / (
                                20 - 0)) * (capabilities['servo']['servo_range'][str(1)][1] -
                                            capabilities['servo']['servo_range'][str(1)][0]) \
                                           + capabilities['servo']['servo_range'][str(1)][0]
                        servo_status[1] = encoder_position
                        head_flag = True
                    if data_point == 2:
                        encoder_position = ((obtained_data['servo_position'][data_point] - 0) / (
                                20 - 0)) * (capabilities['servo']['servo_range'][str(2)][1] -
                                            capabilities['servo']['servo_range'][str(2)][0]) \
                                           + capabilities['servo']['servo_range'][str(2)][0]
                        servo_status[2] = encoder_position
                        head_flag = True
                    if data_point == 3:
                        min_input = 0
                        max_input = 20
                        min_output = capabilities['servo']['servo_range'][str(3)][0]
                        max_output = capabilities['servo']['servo_range'][str(3)][1]
                        current_value = obtained_data['servo_position'][data_point]
                        encoder_position = ((current_value - min_input) / (
                                max_input - min_input)) * (max_output - min_output) + min_output
                        servo_status[3] = encoder_position
                        arms_flag = True
                    if data_point == 4:
                        min_input = 0
                        max_input = 20
                        min_output = capabilities['servo']['servo_range'][str(4)][0]
                        max_output = capabilities['servo']['servo_range'][str(4)][1]
                        current_value = obtained_data['servo_position'][data_point]
                        encoder_position = ((current_value - min_input) / (
                                max_input - min_input)) * (max_output - min_output) + min_output
                        servo_status[4] = encoder_position
                        arms_flag = True
                if head_flag:
                    misty.moveHeadDegrees(servo_status[1], servo_status[0], servo_status[2], 100)
                if arms_flag:
                    print("arms: ", servo_status[3], " and ", servo_status[4])
                    misty.moveArmsDegrees(servo_status[3], servo_status[4])


        except Exception as e:
            print("ERROR: ", e)

    # print(obtained_data)


if __name__ == "__main__":
    runtime_data = {
        "current_burst_id": 0,
        "feagi_state": None,
        "cortical_list": (),
        "battery_charge_level": 1,
        "host_network": {},
        'motor_status': {},
        'servo_status': {}
    }
    config = feagi.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    feagi_settings['feagi_burst_speed'] = float(runtime_data["feagi_state"]['burst_duration'])

    msg_counter = runtime_data["feagi_state"]['burst_counter']
    rgb = dict()
    rgb['camera'] = dict()
    previous_frame_data = {}
    raw_frame = []
    default_capabilities = {}  # It will be generated in process_visual_stimuli. See the
    # overwrite manual
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)
    # threading.Thread(target=retina.vision_progress,
    #                  args=(default_capabilities, feagi_opu_channel, api_address, feagi_settings,
    #                        camera_data['vision'],), daemon=True).start()

    # motor setting
    rolling_window_len = capabilities['motor']['rolling_window_len']
    motor_count = capabilities['motor']['count']
    # Rolling windows for each motor
    rolling_window = {}
    # Initialize rolling window for each motor
    for motor_id in range(motor_count):
        rolling_window[motor_id] = deque([0] * rolling_window_len)

    misty = Robot(capabilities['misty']['ip'])
    misty.changeLED(0, 0, 255)
    # threading.Thread(target=process_video, args=(capabilities, misty), daemon=True).start()
    # threading.Thread(target=getting_websocket_data, daemon=True).start()

    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                pns.check_genome_status_no_vision(message_from_feagi)
                feagi_settings['feagi_burst_speed'] = \
                    pns.check_refresh_rate(message_from_feagi, feagi_settings['feagi_burst_speed'])
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                action(obtained_signals)

            # VISION SECTION
            if len(camera_data['vision']) > 0:
                raw_frame = camera_data['vision']
                previous_frame_data, rgb, default_capabilities = retina.process_visual_stimuli(
                    raw_frame,
                    default_capabilities,
                    previous_frame_data,
                    rgb, capabilities)
                default_capabilities['camera']['blink'] = []
            if 'camera' in default_capabilities:
                if default_capabilities['camera']['blink'] != []:
                    raw_frame = default_capabilities['camera']['blink']
            if rgb:
                message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)
            # VISION ENDS

            sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings,
                                 feagi_settings)
            message_to_feagi.clear()
            if 'camera' in rgb:
                for i in rgb['camera']:
                    rgb['camera'][i].clear()
        except KeyboardInterrupt:
            print("keyboard interrupted. Exiting the program now")
            misty.stop()
            break
