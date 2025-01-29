import threading
import traceback
from time import sleep
from collections import deque
from version import __version__
from feagi_connector import actuators
from feagi_connector import sensors
from pymycobot.mycobot import MyCobot
from feagi_connector import pns_gateway as pns
from feagi_connector import feagi_interface as FEAGI

previous_data_frame = dict()
FEAGI.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator


class Arm:
    @staticmethod
    def connection_initialize(port='/dev/ttyUSB0'):
        """
        :param port: The default would be '/dev/ttyUSB0'. If the port is different, put a different port.
        :return:
        """
        return MyCobot(port, 115200)

    @staticmethod
    def pose_to_default(arm):
        for device_id in capabilities['output']['servo']:
            if not capabilities['output']['servo'][device_id]['disabled']:
                arm.set_encoder(int(device_id) + 1, capabilities['output']['servo'][device_id]['default_value'])
                actuators.update_servo_status_by_default(device_id=int(device_id), initialized_position=capabilities['output']['servo'][device_id]['default_value'])
            else:
                actuators.update_servo_status_by_default(device_id=int(device_id), initialized_position='disabled')


def updating_encoder_position_in_bg():
    global runtime_data, capabilities, feagi_settings
    for i in range(len(capabilities['output']['servo'])):
        runtime_data['actual_encoder_position'][i] = deque([0, 0, 0, 0, 0])
        runtime_data['for_feagi_data'][i] = 0
    while True:
        for i in range(len(capabilities['output']['servo'])):
            new_data = arm.get_encoder(i + 1)
            if new_data != -1:
                if runtime_data['actual_encoder_position'][i]:
                    runtime_data['actual_encoder_position'][i].append(new_data)
                    runtime_data['actual_encoder_position'][i].popleft()
                    runtime_data['for_feagi_data'][i] = new_data
        sleep(0.01)


def action(obtained_data, arm):
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    if recieve_servo_position_data:
        for real_id in recieve_servo_position_data:
            servo_number = real_id + 1  # Feagi sends 0-indexed, mycobot needs 1-indexed
            new_power = recieve_servo_position_data[real_id]
            arm.set_encoder(servo_number, new_power)

    if recieve_servo_data:
        for real_id in recieve_servo_data:  # example output: {0: 100, 2: 100}
            servo_number = real_id + 1  # Feagi sends 0-indexed, mycobot needs 1-indexed
            new_power = recieve_servo_data[real_id]
            arm.set_encoder(servo_number, new_power)



if __name__ == "__main__":
    runtime_data = \
        {
            "current_burst_id": 0,
            "feagi_state": None,
            "cortical_list": (),
            "battery_charge_level": 1,
            "host_network": {},
            'servo_status': {},
            'actual_encoder_position': {},
            'for_feagi_data': {}
        }

    config = FEAGI.build_up_from_configuration(serial_in_use=True)
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

    # MYCOBOT SECTION
    mycobot = Arm()
    arm = mycobot.connection_initialize(agent_settings['usb_port'])
    arm.set_speed(100)
    mycobot.pose_to_default(arm)
    actuators.start_servos(capabilities)
    arm.release_servo(1)
    threading.Thread(target=updating_encoder_position_in_bg, daemon=True).start()

    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                pns.check_genome_status_no_vision(message_from_feagi)
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                action(obtained_signals, arm)

            if pns.full_template_information_corticals:
                message_to_feagi = sensors.create_data_for_feagi('servo_position', capabilities, message_to_feagi, current_data=runtime_data['for_feagi_data'], symmetric=True)


            sleep(feagi_settings['feagi_burst_speed'])
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()
        except KeyboardInterrupt as ke:  # Keyboard error
            arm.release_all_servos()
            break
        except Exception as e:
            arm.release_all_servos()
            print("ERROR! : ", e)
            traceback.print_exc()
            break
