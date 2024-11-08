#!/usr/bin/env python
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
===============================================================================
"""
import os
import json
import socket
import traceback
import lz4.frame
import threading
from time import sleep
from version import __version__
from feagi_connector import sensors
from feagi_connector import pns_gateway as pns
from feagi_connector import feagi_interface as feagi

connected_agents = dict() # Initalize
connected_agents['0'] = False  # By default, it is not connected by client's websocket
feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator


if __name__ == "__main__":
    # NEW JSON UPDATE
    f = open('configuration.json')
    configuration = json.load(f)
    feagi_settings =  configuration["feagi_settings"]
    agent_settings = configuration['agent_settings']
    capabilities = configuration['capabilities']
    feagi_settings['feagi_host'] = os.environ.get('FEAGI_HOST_INTERNAL', "127.0.0.1")
    feagi_settings['feagi_api_port'] = os.environ.get('FEAGI_API_PORT', "8000")
    # agent_settings['godot_websocket_ip'] = os.environ.get('WS_MICROBIT_PORT', "9052")
    f.close()
    message_to_feagi = {"data": {}}
    # END JSON UPDATE

    # Update UDP IP
    UDP_IP = agent_settings['udp_ip'] # To your IP instead of localhost in the configuration. its set due to security reason
    UDP_PORT = agent_settings['udp_port']
    print("UDP IP:", UDP_IP, " and UDP port:", UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)

    # Microbit Ultrasonic values
    accelometer_max_value = []
    accelometer_min_value = []

    phone_gyro_max_value = []
    phone_gyro_min_value = []

    while True:
        feagi_flag = False
        print("Waiting on FEAGI...")
        while not feagi_flag:
            feagi_flag = feagi.is_FEAGI_reachable(os.environ.get('FEAGI_HOST_INTERNAL',
                                                                 "127.0.0.1"),
                                                  int(os.environ.get('FEAGI_OPU_PORT', "3000")))
            sleep(2)
        print("DONE")
        previous_data_frame = {}
        runtime_data = {"cortical_data": {}, "current_burst_id": None,
                        "stimulation_period": 0.01, "feagi_state": None,
                        "feagi_network": None}

        # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
            feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                                   __version__)

        threading.Thread(target=pns.feagi_listener, args=(feagi_opu_channel,), daemon=True).start()
        while True:
            try:
                try:
                    new_data = {}
                    data, addr = sock.recvfrom(1024)
                    new_data = json.loads(data)
                    message_from_feagi = pns.message_from_feagi
                    # print(new_data)
                    if message_from_feagi:
                        pns.check_genome_status_no_vision(message_from_feagi)
                        feagi_settings['feagi_burst_speed'] = message_from_feagi['burst_frequency']

                    if new_data['accelerometer']:
                        # Section of acceleration

                        create_gyro_data_list_phone = dict()
                        create_gyro_data_list_phone['i__gyr'] = dict()


                        for device_id in range(3):
                            letter = str(device_id)
                            accelometer_max_value, accelometer_min_value = (
                                sensors.measuring_max_and_min_range(new_data['accelerometer'][letter],
                                                                    device_id,
                                                                    accelometer_max_value,
                                                                    accelometer_min_value))
                            try:
                                position_of_analog = sensors.convert_sensor_to_ipu_data(
                                    accelometer_min_value[device_id],
                                    accelometer_max_value[device_id],
                                    new_data['accelerometer'][letter],
                                    device_id,
                                    cortical_id='i__gyr',
                                    symmetric=True)
                                create_gyro_data_list_phone['i__gyr'][position_of_analog] = 100
                            except Exception as error:
                                pass
                        message_to_feagi = sensors.add_generic_input_to_feagi_data(
                            create_gyro_data_list_phone,
                            message_to_feagi)

                    # Add gyro section
                    if new_data['gyro']:
                        # Section of acceleration
                        create_acceleration_data_list_microbit = dict()
                        create_acceleration_data_list_microbit['i__acc'] = dict()
                        try:
                            for device_id in range(len(new_data['gyro'])):
                                phone_gyro_max_value, phone_gyro_min_value = (
                                    sensors.measuring_max_and_min_range(new_data['gyro'][str(device_id)],
                                                                        device_id,
                                                                        phone_gyro_max_value,
                                                                        phone_gyro_min_value))
                                position_of_analog = sensors.convert_sensor_to_ipu_data(phone_gyro_min_value[device_id],
                                                                                        phone_gyro_max_value[device_id],
                                                                                        new_data['gyro'][
                                                                                            str(device_id)],
                                                                                        device_id,
                                                                                        cortical_id='i__acc',
                                                                                        symmetric=True)
                                create_acceleration_data_list_microbit['i__acc'][position_of_analog] = 100
                            message_to_feagi = sensors.add_generic_input_to_feagi_data(
                                create_acceleration_data_list_microbit,
                                message_to_feagi)
                        except:
                            pass
                    # End gyro section
                except Exception as error:
                    pass
                sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
                pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
                message_to_feagi.clear()
            except Exception as e:
                # pass
                print("ERROR! : ", e)
                traceback.print_exc()
                break