#!/usr/bin/env python
"""
Copyright 2016-2025 Neuraville Inc. All Rights Reserved.

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

import time
import asyncio
import pycozmo
import threading
import traceback
import cozmo_functions
from time import sleep
import facial_expression
from version import __version__
from feagi_connector import retina
from cozmo_ipu import cozmo_ipu
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector import feagi_interface as FEAGI

runtime_data = {
    "current_burst_id": 0,
    "feagi_state": None,
    "cortical_list": (),
    "battery_charge_level": 1,
    "host_network": {},
    'motor_status': {},
    'servo_status': {}
}

previous_frame_data = {}
rgb = {'camera': {}}
FEAGI.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator


def face_starter(cli):
    asyncio.run(facial_expression.expressions(cli))


def action(obtained_data):
    recieve_motor_data = actuators.get_motor_data(obtained_data)
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)


    if recieve_servo_position_data:
        for real_id in recieve_servo_position_data:
            servo_number = real_id  # Feagi sends 0-indexed, mycobot needs 1-indexed
            new_power = recieve_servo_position_data[real_id]
            if servo_number == 0:
                cozmo_functions.move_head(cli, new_power, max, min)
            if servo_number == 1:
                cozmo_functions.lift_arms(cli, new_power, max_lift, min_lift, facial_expression.face_selected)

    if recieve_servo_data:
        for real_id in recieve_servo_data:  # example output: {0: 100, 2: 100}
            servo_number = real_id  # Feagi sends 0-indexed, mycobot needs 1-indexed
            new_power = recieve_servo_data[real_id]
            if servo_number == 0:
                cozmo_functions.move_head(cli, new_power, max, min)
            if servo_number == 1:
                cozmo_functions.lift_arms(cli, new_power, max_lift, min_lift, facial_expression.face_selected)

    if recieve_motor_data:
        rwheel_speed = 0
        lwheel_speed = 0
        for motor_id in recieve_motor_data:
                data_power = recieve_motor_data[motor_id]
                if motor_id == 0:
                    rwheel_speed = data_power
                if motor_id == 1:
                 lwheel_speed = data_power
        cozmo_functions.drive_wheels(cli,
                                     lwheel_speed=lwheel_speed,
                                     rwheel_speed=rwheel_speed,
                                     duration=feagi_settings['feagi_burst_speed'] / 2)
    if "misc" in obtained_data:
        if obtained_data["misc"]:
            print("face: ", facial_expression.face_selected, " misc: ", obtained_data["misc"])
            for i in obtained_data["misc"]:
                facial_expression.face_selected.append(i)
        obtained_data['misc'].clear()

def data_opu(action):
    old_message = {}
    while True:
        message_from_feagi = pns.message_from_feagi
        if old_message != message_from_feagi:
            if message_from_feagi:
                if pns.full_template_information_corticals:
                    obtained_signals = pns.obtain_opu_data(message_from_feagi)
                    action(obtained_signals)
        sleep(0.001)


if __name__ == '__main__':
    config = FEAGI.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        FEAGI.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # # Raise head.
    cli = pycozmo.Client()
    cli.start()
    cli.connect()
    cli.wait_for_robot()
    # print("max in rad: ", pycozmo.robot.MAX_HEAD_ANGLE.radians)  # 0.7766715171374767
    # print("min in rad: ", pycozmo.robot.MIN_HEAD_ANGLE.radians)  # -0.4363323129985824
    max = pycozmo.robot.MAX_HEAD_ANGLE.radians - 0.1
    min = pycozmo.robot.MIN_HEAD_ANGLE.radians + 0.1
    max_lift = pycozmo.MAX_LIFT_HEIGHT.mm - 5
    min_lift = pycozmo.MIN_LIFT_HEIGHT.mm + 5
    angle_of_head = \
        (pycozmo.robot.MAX_HEAD_ANGLE.radians - pycozmo.robot.MIN_HEAD_ANGLE.radians) / 2.0
    angle_of_arms = 50  # TODO: How to obtain the arms encoders in real time
    cli.set_head_angle(angle_of_head)  # move head
    actuators.start_motors(capabilities)  # initialize motors for you.
    actuators.start_servos(capabilities)
    actuators.update_servo_status_by_default(device_id=0, initialized_position=angle_of_head)
    actuators.update_servo_status_by_default(device_id=1, initialized_position=angle_of_arms)
    # # vision capture
    cli.enable_camera(enable=True, color=True)
    threading.Thread(target=face_starter, args=(cli,), daemon=True).start()
    threading.Thread(target=cozmo_functions.robot_status, args=(cli,), daemon=True).start()
    threading.Thread(target=cozmo_functions.vision_initalization, args=(cli,), daemon=True).start()
    threading.Thread(target=retina.vision_progress,
                     args=(default_capabilities,feagi_settings,
                           cozmo_functions.camera_data,), daemon=True).start()
    threading.Thread(target=data_opu, args=(action, ), daemon=True).start()
    time.sleep(2)
    # vision ends

    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            # if message_from_feagi:
                # obtained_signals = pns.obtain_opu_data(message_from_feagi)
                # action(obtained_signals, angle_of_arms, angle_of_head, motor_data)
                # action(obtained_signals)
                # OPU section ENDS
                # if "o_eye1" in message_from_feagi["opu_data"]:
                #     if message_from_feagi["opu_data"]["o_eye1"]:
                #         for i in message_from_feagi["opu_data"]["o_eye1"]:
                #             split_data = i.split("-")
                #             y_array = [70, 40, -60]
                #             if split_data[0] == '2':
                #                 eye_one_location.append([80, y_array[int(split_data[1])]])
                #             if split_data[0] == '1':
                #                 eye_one_location.append([0, y_array[int(split_data[1])]])
                #             if split_data[0] == '0':
                #                 eye_one_location.append([-30, y_array[int(split_data[1])]])
                #         facial_expression.face_selected.append(0)
                # if "o_eye2" in message_from_feagi["opu_data"]:
                #     if message_from_feagi["opu_data"]["o_eye2"]:
                #         for i in message_from_feagi["opu_data"]["o_eye2"]:
                #             split_data = i.split("-")
                #             y_array = [65, 40, -50]
                #             if split_data[0] == '2':
                #                 eye_two_location.append([40, y_array[int(split_data[1])]])
                #             if split_data[0] == '1':
                #                 eye_two_location.append([-10, y_array[int(split_data[1])]])
                #             if split_data[0] == '0':
                #                 eye_two_location.append([-30, y_array[int(split_data[1])]])
                #         if len(facial_expression.face_selected) == 0:
                #             facial_expression.face_selected.append(0)
                # if "o_init" in message_from_feagi["opu_data"]:
                #     if message_from_feagi["opu_data"]["o_init"]:
                #         for i in message_from_feagi["opu_data"]["o_init"]:
                #             split_data = i.split("-")
                #             if split_data[0] == '0':
                #                 cozmo_functions.display_lines(cli)

            # Vision section START
            raw_frame = cozmo_functions.camera_data['vision']
            previous_frame_data, rgb, default_capabilities = retina.process_visual_stimuli(
                raw_frame,
                default_capabilities,
                previous_frame_data,
                rgb, capabilities)
            if rgb:
                message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)
            # Vision section END
            message_to_feagi = cozmo_ipu(cozmo_functions.robot, capabilities, angle_of_head, angle_of_arms, message_to_feagi)
            sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()

            if rgb:
                for i in rgb['camera']:
                    rgb['camera'][i].clear()
        except Exception as e:
            print("ERROR IN COZMO MAIN CODE: ", e)
            traceback.print_exc()
            break
