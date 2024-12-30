from time import sleep
import time
import threading
import serial
from datetime import datetime
from feagi_connector import feagi_interface as feagi
from feagi_connector import sensors
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import actuators
import struct

servo_for_feagi = [40, 40, 40, 40, 40]
previous_feagi_servo_list = servo_for_feagi.copy()

feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator
runtime_data = {}


# Function to handle receiving data
def read_from_port(ser):
    while True:
        try:
            obtained_data = ser.readline()
            print("recieved_data: ", obtained_data)
        except Exception as Error_case:
            print("error: ", Error_case)


def action(obtained_data):
    global servo_for_feagi, previous_feagi_servo_list
    servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    if recieve_servo_position_data:
        for device_id in recieve_servo_position_data:
            servo_for_feagi[int(device_id)] = int(recieve_servo_position_data[device_id])

    if servo_data:
        for device_id in servo_data:
            servo_for_feagi[int(device_id)] = int(recieve_servo_position_data[device_id])

    if servo_for_feagi != previous_feagi_servo_list:
        formatted_data = ','.join(map(str, servo_for_feagi)) + '\n'
        ser.write(formatted_data.encode('utf-8'))
        previous_feagi_servo_list = servo_for_feagi.copy()

if __name__ == "__main__":
    ser = serial.Serial('COM7', 115200)
    # thread_read = threading.Thread(target=read_from_port, args=(ser,)) # We need this for sensor soon
    # thread_write = threading.Thread(target=write_to_port, args=(ser,))

    # thread_read.start() # Needs to uncomment this for sensor
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

    # To give ardiuno some time to open port. It's required
    actuators.start_servos(capabilities)
    time.sleep(5)
    print("serial is ready")

    while True:
        message_from_feagi = pns.message_from_feagi

        # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
        if message_from_feagi is not None:
            pns.check_genome_status_no_vision(message_from_feagi)
            feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(
                message_from_feagi, feagi_settings['feagi_burst_speed'])
            obtained_signals = pns.obtain_opu_data(message_from_feagi)
            action(obtained_signals)

        sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel,
                             agent_settings, feagi_settings)
        message_to_feagi.clear()
