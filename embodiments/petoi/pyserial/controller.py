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

servo_status = dict()
gyro = {"0":[]}
acc = {"0":[]}
feagi.validate_requirements(
    'requirements.txt')  # you should get it from the boilerplate generator
runtime_data = {}
petoi_data = {'servo_status': {}}


# Function to handle receiving data
def read_from_port(ser):
    global received_data, gyro
    full_data = ''
    # start_time = datetime.now()
    # counter = 0
    while True:
        # total_time = (datetime.now() - start_time).total_seconds()
        # if total_time > 1:
        #     start_time = datetime.now()
        #     print("data recieved: ", counter, " after 1 second", total_time)
        #     counter = 0
        try:
            obtained_data = ser.readline().decode('utf-8').rstrip()
            split_data = obtained_data.split()
            received_data = {}
            if len(split_data) == 9:
                for servo_id in range(len(split_data)):
                    received_data[str(servo_id)] = int(float(split_data[servo_id]))
                petoi_data['servo_status'] = received_data
            if len(split_data) == 6:
                gyro['0'] = [float(split_data[0]), float(split_data[1]), float(split_data[2])]
                acc['0'] = [int(split_data[3]), int(split_data[4]), int(split_data[5])]
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
                gyro['gyro'] = {'0': [processed_data[0], processed_data[1], processed_data[2]]}
            else:
                full_data = received_data
        except Exception as Error_case:
            pass
            print("error: ", Error_case)
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
    servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)
    recieved_misc_data = actuators.get_generic_opu_data_from_feagi(obtained_data, 'misc')


    if recieved_misc_data:
        for data_point in recieved_misc_data:
            if data_point == 0:
                ser.write('gPb'.encode())
            if data_point == 1:
                ser.write('f'.encode())

    if recieve_servo_position_data:
        petoi_data['servo_status'].clear()
        servo_for_feagi = 'i '
        for device_id in recieve_servo_position_data:
            new_power = recieve_servo_position_data[device_id]
            servo_for_feagi += str(feagi_to_petoi_id(device_id)) + " " + str(new_power) + " "
            ser.write(servo_for_feagi.encode())

    if servo_data:
        petoi_data['servo_status'].clear()
        servo_for_feagi = 'i '
        for device_id in servo_data:
            power = servo_data[device_id]
            servo_for_feagi += str(feagi_to_petoi_id(device_id)) + " " + str(power) + " "
        print(servo_for_feagi)
        ser.write(servo_for_feagi.encode())



if __name__ == "__main__":
    ser = serial.Serial('COM4', 115200)
    thread_read = threading.Thread(target=read_from_port, args=(ser,))
    # thread_write = threading.Thread(target=write_to_port, args=(ser,))

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

    # To give ardiuno some time to open port. It's required
    actuators.start_servos(capabilities)
    time.sleep(5)
    feagi_servo_data_to_send = 'i '
    for position in capabilities['output']['servo']:
        feagi_servo_data_to_send += str(feagi_to_petoi_id(int(position))) + " " + str(
            capabilities['output']['servo'][position]['default_value']) + " "
    actuators.start_servos(capabilities)
    # ser.write('gPb'.encode())
    print("here: ", feagi_servo_data_to_send)
    ser.write(feagi_servo_data_to_send.encode())
    print("done")
    while True:
        message_from_feagi = pns.message_from_feagi

        # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
        if message_from_feagi is not None:
            pns.check_genome_status_no_vision(message_from_feagi)
            feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(
                message_from_feagi, feagi_settings['feagi_burst_speed'])
            obtained_signals = pns.obtain_opu_data(message_from_feagi)
            action(obtained_signals)
        # if gyro:
        #     message_to_feagi = sensors.add_gyro_to_feagi_data(gyro['gyro'], message_to_feagi)
        if petoi_data['servo_status']:
            message_to_feagi = sensors.create_data_for_feagi('servo_position',
                                                             capabilities,
                                                             message_to_feagi,
                                                             current_data=petoi_data['servo_status'],
                                                             symmetric=True)
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