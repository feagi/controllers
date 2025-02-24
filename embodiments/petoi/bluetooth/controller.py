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

import asyncio
import threading
from collections import deque
from datetime import datetime
from time import sleep
import traceback
import websockets
from configuration import *
from version import __version__
from feagi_connector import pns_gateway as pns
from feagi_connector import sensors as sensors
from feagi_connector import actuators
from feagi_connector import feagi_interface as feagi

ws = deque()
ws_operation = deque()
previous_data = ""
servo_status = {}
gyro = {}


async def bridge_to_godot():
    while True:
        if ws:
            try:
                if ws_operation:
                    if len(ws) > 0:
                        if len(ws) > 2:
                            stored_value = ws.pop()
                            ws.clear()
                            ws.append(stored_value)
                    await ws_operation[0].send(str(ws[0]))
                    ws.pop()
                if "stimulation_period" in runtime_data:
                    sleep(runtime_data["stimulation_period"])
            except Exception as error:
                print("error: ", error)
                sleep(0.001)
        else:
            sleep(0.001)


def bridge_operation():
    asyncio.run(bridge_to_godot())


async def echo(websocket):
    """
    The function echoes the data it receives from other connected websockets
    and sends the data from FEAGI to the connected websockets.
    """
    # ws.append("G")
    full_data = ''
    start_time = datetime.now()
    counter = 0
    async for message in websocket:
        if (datetime.now() - start_time).total_seconds() > 1:
            start_time = datetime.now()
            print("data recieved: ", counter, " after 1 second")
            counter = 0
        if not ws_operation:
            ws_operation.append(websocket)
        else:
            ws_operation[0] = websocket
        # output_array = message.strip('#').split(',')
        # print(output_array)
        try:
            if '#' in message:
                cleaned_data = message.replace('\r', '')
                cleaned_data = cleaned_data.replace('\n', '')
                test = cleaned_data.split('#')
                new_data = full_data + test[0]
                new_data = new_data.split(",")
                processed_data = []
                for i in new_data:
                    full_number = str()
                    for x in i:
                        if x in [".", "-"] or x.isdigit():
                            full_number += x
                    if full_number:
                        processed_data.append(float(full_number))
                # Add gyro data into feagi data
                gyro['gyro'] = {'0': processed_data[0], '1': processed_data[1],
                                '2': processed_data[2]}
                full_data = test[1]
            else:
                full_data = message
        except Exception as Error_case:
            pass
            # print("error: ", Error_case)
            # traceback.print_exc()
            # print("raw: ", message)
        counter += 1
        # print((datetime.now() - start_time).total_seconds())


async def main():
    """
    The main function handles the websocket and spins the asyncio to run the echo function
    infinitely until it exits. Once it exits, the function will resume to the next new websocket.
    """
    async with websockets.serve(echo, agent_settings["godot_websocket_ip"],
                                agent_settings['godot_websocket_port']):
        await asyncio.Future()  # run forever


def websocket_operation():
    """
    WebSocket initialized to call the echo function using asyncio.
    """
    asyncio.run(main())


def feagi_to_petoi_id(device_id):
    mapping = {
        0: 0,
        1: 8,
        2: 12,
        3: 9,
        4: 13,
        5: 11,
        6: 15,
        7: 10,
        8: 14
    }
    return mapping.get(device_id, None)


def action(obtained_data):
    servo_data = actuators.get_servo_data(obtained_data, True)
    WS_STRING = ""
    if 'servo_position' in obtained_data:
        servo_for_feagi = 'i '
        if obtained_data['servo_position'] is not {}:
            for data_point in obtained_data['servo_position']:
                device_id = feagi_to_petoi_id(data_point)
                encoder_position = (((180) / 20) * obtained_data['servo_position'][data_point]) - 90
                servo_for_feagi += str(device_id) + " " + str(encoder_position) + " "
            WS_STRING += servo_for_feagi
    if servo_data:
        WS_STRING = "i"
        for device_id in servo_data:
            servo_power = actuators.servo_generate_power(180, servo_data[device_id], device_id)
            if device_id not in servo_status:
                servo_status[device_id] = actuators.servo_keep_boundaries(90)
            else:
                servo_status[device_id] += servo_power / 10
                servo_status[device_id] = actuators.servo_keep_boundaries(servo_status[device_id])
            actual_id = feagi_to_petoi_id(device_id)
            # print("device id: ", actual_id, ' and power: ', servo_data[device_id], " servo power: ", servo_power)
            WS_STRING += " " + str(actual_id) + " " + str(int(actuators.servo_keep_boundaries(servo_status[device_id])) - 90)
    if WS_STRING != "":
        # WS_STRING = WS_STRING + "#"
        print("sending to main: ", WS_STRING)
        ws.append(WS_STRING)


if __name__ == "__main__":
    CHECKPOINT_TOTAL = 5
    FLAG_COUNTER = 0
    microbit_data = {'ir': [], 'ultrasonic': {}, 'accelerator': {}, 'sound_level': {}}
    threading.Thread(target=websocket_operation, daemon=True).start()
    # threading.Thread(target=bridge_to_godot, daemon=True).start()
    threading.Thread(target=bridge_operation, daemon=True).start()
    feagi_flag = False
    print("Waiting on FEAGI...")
    while not feagi_flag:
        feagi_flag = feagi.is_FEAGI_reachable(
            os.environ.get('FEAGI_HOST_INTERNAL', "127.0.0.1"),
            int(os.environ.get('FEAGI_OPU_PORT', "3000"))
        )
        sleep(2)
    previous_data_frame = {}
    runtime_data = {"cortical_data": {}, "current_burst_id": None,
                    "stimulation_period": 0.01, "feagi_state": None,
                    "feagi_network": None}

    feagi_auth_url = feagi_settings.pop('feagi_auth_url', None)
    print("FEAGI AUTH URL ------- ", feagi_auth_url)

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    threading.Thread(target=pns.feagi_listener, args=(feagi_opu_channel,), daemon=True).start()
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    msg_counter = runtime_data["feagi_state"]['burst_counter']
    runtime_data['accelerator'] = {}
    flag = True

    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            # OPU section STARTS
            if message_from_feagi:
                pns.check_genome_status_no_vision(message_from_feagi)
                feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(message_from_feagi,
                                                                             feagi_settings[
                                                                                 'feagi_burst_speed'])
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                action(obtained_signals)
            # OPU section ENDS

            if gyro:
                message_to_feagi = sensors.add_gyro_to_feagi_data(gyro['gyro'], message_to_feagi)
                if flag:
                    ws.append('g')
                    flag = False

            message_to_feagi['timestamp'] = datetime.now()
            message_to_feagi['counter'] = msg_counter
            sleep(feagi_settings['feagi_burst_speed'])
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()
        except Exception as e:
            print("ERROR: ", e)
            traceback.print_exc()
            break
