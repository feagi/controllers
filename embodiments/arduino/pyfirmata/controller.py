"""
Copyright 2016-2022 The FEAGI Authors. All Rights Reserved.

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
import util
from __init__ import *
from time import sleep
import pyfirmata_neuraville
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import feagi_interface as feagi

servo_status = dict()
motor_status = dict()
pin_board = dict()
analog_pin_board = dict()
pin_mode = dict()
rolling_window = {}
output_track = list()
input_track = list()


def list_all_pins(board):
    all_pins = dict()
    for pin in board._layout['digital']:
        if pin not in [0, 1]:  # 0 and 1 are not available for output.
            all_pins[pin] = ""  # initalize empty key
    for pin in all_pins:
        current = pin  # Due to serial communcations port
        pin_board[current] = board.get_pin('d:{0}:s'.format(int(pin)))
        pin_mode[current] = 4


def list_all_analog_pins(board):
    all_pins = dict()
    for pin in board.analog:
        all_pins[pin.pin_number] = ""
    for pin in all_pins:
        analog_pin_board[pin] = board.get_pin('a:{0}:i'.format(int(pin)))
    print(analog_pin_board)


def set_pin_mode(pin, mode, id):
    pin.mode = mode
    pin_mode[id] = mode


def action(obtained_data):
    recieve_servo_data = actuators.get_servo_data(obtained_data, True)
    recieve_gpio_data = actuators.get_gpio_data(obtained_data)
    check_input_request = actuators.check_convert_gpio_to_input(obtained_data)
    if check_input_request:
        for id in check_input_request:
            if id in pin_mode:
                if pin_mode[int(id)] != 0:
                    set_pin_mode(pin_board[int(id)], 0, id)
                    input_track.append(id)
    if recieve_gpio_data:
        for i in recieve_gpio_data:
            if i in pin_mode:
                if pin_mode[int(i)] != 1:
                    set_pin_mode(pin_board[int(i)], 1, i)
                    if int(i) in input_track:
                        input_track.remove(int(i))
                pin_board[int(i)].write(1)
                output_track.append(int(i))  # Tracking whatever used digital
            else:
                print("pin: ", i, " is not configured. Select another pin please.")
    else:
        if output_track:
            for pin in output_track:
                pin_board[pin].write(0)
            output_track.clear()

    if recieve_servo_data:
        # Do some custom work with servo data as well
        for id in recieve_servo_data:
            if id in pin_mode:
                if pin_mode[int(id)] != 4:
                    print("reset your board to use the servo again after you updated pin: ", id)
                    set_pin_mode(pin_board[int(id)], pyfirmata_neuraville.OUTPUT, id)
                servo_power = actuators.servo_generate_power(180, recieve_servo_data[id], id)
                if id in motor_status:
                    del motor_status[id]
                if id not in servo_status:
                    servo_status[id] = actuators.servo_keep_boundaries(servo_power)
                    pin_board[id].write(servo_status[id])
                else:
                    servo_status[id] += servo_power / 100
                    servo_status[id] = actuators.servo_keep_boundaries(servo_status[id])
                    pin_board[id].write(servo_status[id])
            else:
                print("pin: ", id, " is not configured. Select another pin please.")


if __name__ == "__main__":
    runtime_data = dict()
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
    # Specify the serial port where your Arduino is connected (e.g., 'COM3' on Windows or
    # '/dev/ttyUSB0' on Linux)
    feagi_settings['feagi_burst_speed'] = float(runtime_data["feagi_state"]['burst_duration'])
    port = capabilities['arduino']['port']  # Don't change this
    board = Arduino(port)
    it = util.Iterator(board)  # for Analog or Input
    it.start()
    list_all_analog_pins(board) # Temporarily pause analog section
    sleep(2)
    list_all_pins(board)
    print("HERE: ", analog_pin_board)

    while True:
        message_from_feagi = pns.message_from_feagi
        if message_from_feagi:
            # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
            pns.check_genome_status_no_vision(message_from_feagi)
            feagi_settings['feagi_burst_speed'] = \
                pns.check_refresh_rate(message_from_feagi, feagi_settings['feagi_burst_speed'])
            obtained_signals = pns.obtain_opu_data(message_from_feagi)
            action(obtained_signals)
        if input_track:
            create_generic_input_dict = dict()
            create_generic_input_dict['idgpio'] = dict()
            for pin in input_track:
                obtain_data = pin_board[pin].read()
                if obtain_data:
                    location_string = str(pin) + "-0-0"
                    create_generic_input_dict['idgpio'][location_string] = 100
            message_to_feagi = sensors.add_generic_input_to_feagi_data(create_generic_input_dict,
                                                                       message_to_feagi)
        if analog_pin_board:
            create_analog_data_list = dict()
            create_analog_data_list['iagpio'] = dict()
            for i in analog_pin_board:
                position_of_analog = sensors.convert_sensor_to_ipu_data(0, 1, analog_pin_board[
                    i].read(), i)
                create_analog_data_list['iagpio'][position_of_analog] = 100
            message_to_feagi = sensors.add_generic_input_to_feagi_data(create_analog_data_list,
                                                                       message_to_feagi)
        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        sleep(feagi_settings['feagi_burst_speed'])
