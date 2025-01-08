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
    while True:
        try:
            obtained_data = ser.readline().decode('utf-8').rstrip()
            parsed_data = json.loads(obtained_data)
            acc['0'] = parsed_data[0]
            gyro['0'] = parsed_data[1]
        except Exception as Error_case:
            pass
            # print("error: ", Error_case)
            # print("raw data: ", obtained_data)


def action(obtained_data):
    pass


if __name__ == "__main__":
    ser = serial.Serial('COM7', 115200)
    thread_read = threading.Thread(target=read_from_port, args=(ser,))
    thread_read.start()
    # thread_write.start()

    # thread_read.join()
    # thread_write.join()
    print("Ready...")
    config = feagi.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

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
        if message_from_feagi is not None:
            pns.check_genome_status_no_vision(message_from_feagi)
            feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(
                message_from_feagi, feagi_settings['feagi_burst_speed'])
            obtained_signals = pns.obtain_opu_data(message_from_feagi)
            # action(obtained_signals)
        if gyro['0']:
            message_to_feagi = sensors.create_data_for_feagi('gyro',
                                                             capabilities,
                                                             message_to_feagi,
                                                             current_data=gyro,
                                                             symmetric=True)
        if acc['0']:
            message_to_feagi = sensors.create_data_for_feagi('accelerometer',
                                                             capabilities,
                                                             message_to_feagi,
                                                             current_data=acc,
                                                             symmetric=True)

        sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel,
                             agent_settings, feagi_settings)
        message_to_feagi.clear()
