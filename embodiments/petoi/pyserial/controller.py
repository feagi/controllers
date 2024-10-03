import traceback
from time import sleep
import time
import threading
import serial
import numpy as np
from datetime import datetime
from feagi_connector import feagi_interface as feagi
from feagi_connector import sensors
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import actuators

servo_status = []
gyro = {}


def simulation_from_fpga():
    return [np.random.choice([0, 1]) for _ in range(16)]

# Function to handle receiving data
def read_from_port(ser=''):
    global received_data, gyro
    full_data = ''
    while True:
        # total_time = (datetime.now() - start_time).total_seconds()
        # if total_time > 1:
        #     start_time = datetime.now()
        #     print("data recieved: ", counter, " after 1 second", total_time)
        #     counter = 0
        reading = simulation_from_fpga()
        # reading = ser.readline().decode('utf-8').rstrip()
        received_data = reading
        try:
            if '#' in received_data:
                cleaned_data = received_data.replace('#', '')
                new_data = full_data + cleaned_data
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
            else:
                full_data = received_data # just an array
                action(full_data)
        except Exception as Error_case:
            pass
            print(Error_case)
            traceback.print_exc()
        # counter += 1

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
    # fpga here section:
    servo_for_feagi = 'i '
    print("full raw data: ", obtained_data)
    for servo_id in range(0, len(obtained_data), 2):
        mapped_id = feagi_to_petoi_id(servo_id // 2)
        value1, value2 = obtained_data[servo_id], obtained_data[servo_id + 1]
        if value1 == 1:
            servo_status[servo_id // 2] += 1
        if value2 == 1:
            servo_status[servo_id // 2] -= 1
        servo_status[servo_id // 2] = actuators.servo_keep_boundaries(servo_status[servo_id // 2], 90, -90) # block from exceeded 90
        # Append the mapped ID and the adjusted status to the result string
        servo_for_feagi += str(mapped_id) + " " + str(servo_status[servo_id // 2]) + " "
    print("final: ", servo_for_feagi)
    # ser.write(servo_for_feagi.encode())

    # fpga ends here:
    # servo_data = actuators.get_servo_data(obtained_data, True)
    # if 'servo_position' in obtained_data:
    #     servo_for_feagi = 'i '
    #     if obtained_data['servo_position'] is not {}:
    #         for data_point in obtained_data['servo_position']:
    #             device_id = feagi_to_petoi_id(data_point)
    #             encoder_position = (((180) / 20) * obtained_data['servo_position'][data_point]) - 90
    #             servo_for_feagi += str(device_id) + " " + str(encoder_position) + " "
    #         print(servo_for_feagi)
    #         ser.write(servo_for_feagi.encode())
    # if servo_data:
    #     servo_for_feagi = 'i '
    #     for device_id in servo_data:
    #         servo_power = actuators.servo_generate_power(90, servo_data[device_id], device_id)
    #         if device_id not in servo_status:
    #             servo_status[device_id] = actuators.servo_keep_boundaries(servo_power)
    #             # pin_board[device_id].write(servo_status[device_id])
    #         else:
    #             servo_status[device_id] += servo_power / 10
    #             servo_status[device_id] = actuators.servo_keep_boundaries(servo_status[device_id])
    #             # pin_board[device_id].write(servo_status[device_id])
    #             token = feagi_to_petoi_id(device_id)
    #             task = servo_status[device_id] - 90  # white space
    #             servo_for_feagi += str(token) + " " + str(task) + " "
    #     print(servo_for_feagi)
    #     ser.write(servo_for_feagi.encode())



if __name__ == "__main__":
    # ser = serial.Serial('/dev/ttyACM0', 115200)
    # thread_read = threading.Thread(target=read_from_port, args=(ser,))
    # thread_write = threading.Thread(target=write_to_port, args=(ser,))

    # thread_read.start()
    # thread_write.start()

    # thread_read.join()
    # thread_write.join()
    # print("Ready...")
    # config = FEAGI.build_up_from_configuration()
    # feagi_settings = config['feagi_settings'].copy()
    # agent_settings = config['agent_settings'].copy()
    # default_capabilities = config['default_capabilities'].copy()
    # message_to_feagi = config['message_to_feagi'].copy()
    # capabilities = config['capabilities'].copy()

    # # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # # - - - - - - - - - - - - - - - - - - #
    # feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
    #     FEAGI.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
    #                            __version__)
    # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # To give ardiuno some time to open port. It's required
    # ser = serial.Serial('/dev/ttyACM0', 115200)
    # time.sleep(5)
    print("Starting now!")
    for x in range(8):
        servo_status.append(90)
    read_from_port()
    # while True:
    #     print(simulation_from_fpga())
    #     sleep((0.1))
        # message_from_feagi = pns.message_from_feagi
        #
        # # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
        # if message_from_feagi is not None:
        #     pns.check_genome_status_no_vision(message_from_feagi)
        #     feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(message_from_feagi, feagi_settings['feagi_burst_speed'])
        #     obtained_signals = pns.obtain_opu_data(message_from_feagi)
        #     # action(obtained_signals)
        # # if gyro:
        # #     message_to_feagi = sensors.add_gyro_to_feagi_data(gyro['gyro'], message_to_feagi)
        # sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
        # pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        # message_to_feagi.clear()
