from time import sleep
import time
import ast
import json
import threading
import serial
from feagi_connector import feagi_interface as feagi
from feagi_connector import sensors
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__

gyro = {"0": []}
acc = {"0": []}

feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator
runtime_data = {}


# Function to handle receiving data
def read_from_port(ser):
    data_received = ser.readline().decode('utf-8').rstrip()
    if data_received:
        # print(data_received) # TODO: Needs to make this somewhat useful and scalable
        # print("type: :", type(data_received))
        if data_received.isdigit():
            data_as_int = int(data_received)
            # print(data_as_int)
            return data_as_int


def action(obtained_data):
    pass


if __name__ == "__main__":
    print("Ready...")
    config = feagi.build_up_from_configuration(serial_in_use=True)
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    ser = serial.Serial(agent_settings['usb_port'], 115200)
    # thread_write.start()

    # thread_read.join()
    # thread_write.join()

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings,
                               capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    time.sleep(5)
    while True:
        message_from_feagi = pns.message_from_feagi

        # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
        if message_from_feagi:
            pns.check_genome_status_no_vision(message_from_feagi)
            feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(
                message_from_feagi, feagi_settings['feagi_burst_speed'])
            obtained_signals = pns.obtain_opu_data(message_from_feagi)
            # action(obtained_signals)

        position = read_from_port(ser)
        if position is not None:
            print("data recieved: ", position)
            new_data = (0, int(position), 0)
            create_id = dict()
            create_id['i___id'] = dict()
            create_id['i___id'][new_data] = 100
            message_to_feagi = sensors.add_generic_input_to_feagi_data(create_id, message_to_feagi)
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()

        sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel,
                             agent_settings, feagi_settings)
        message_to_feagi.clear()