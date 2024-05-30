import threading
import traceback
from time import sleep
from collections import deque
from version import __version__
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector import feagi_interface as FEAGI

from xArm.xarm.wrapper import XArmAPI


def pose_to_default(arm, count):
    for number_id in range(count):
        runtime_data['servo_status'][number_id] = 0
    arm.reset(wait=True)


def calculate_the_servo_speed(rolling_window, seconds):
    last_index = len(rolling_window) - 1
    rolling_delta = rolling_window[last_index] - rolling_window[0]
    burst_duration_total = 3 * seconds
    return rolling_delta / burst_duration_total


def updating_encoder_position_in_bg(arm):
    global runtime_data, capabilities, feagi_settings
    rolling_window = {}
    rolling_window_len = capabilities['servo']['rolling_window_len']
    for servo_id in range(capabilities['servo']['count'] * 2):
        rolling_window[servo_id] = deque([0] * rolling_window_len)
    while True:
        new_degree_list_of_servo = arm.get_servo_angle()
        for number_of_servo in range(capabilities['servo']['count']):
            position_for_i_spos = pns.fetch_servo_position_size_and_return_percentage(capabilities,
                                                                                      new_degree_list_of_servo[1][number_of_servo],
                                                                                      number_of_servo,
                                                                                      flip=True)
            if position_for_i_spos is not None:
                runtime_data['i_spos'][position_for_i_spos] = 100
        for current_servo_number in range(0, capabilities['servo']['count'] * 2, 2):
            number_of_servo = current_servo_number # A number incrementing from range(12)
            rolling_window[number_of_servo].append(new_degree_list_of_servo[1][number_of_servo//2])
            # new degree list has 6 servos, so using floor divsion to keep it 6
            rolling_window[number_of_servo].popleft()
            # pop the old index from rolling_window

            get_speed = calculate_the_servo_speed(rolling_window[number_of_servo],
                                                  feagi_settings['feagi_burst_speed'])
            # Get a speed from old index - new index / time
            position_for_i_smot = pns.fetch_servo_motion_sensor_size_and_return_percentage(
                get_speed,
                number_of_servo,
                capabilities['servo']['max_speed'])
            if position_for_i_smot is not None:
                if not any(key[:4] == position_for_i_smot[:4] for key in runtime_data['i_smot']):
                    runtime_data['i_smot'][position_for_i_smot] = 100
                    key_name = str(number_of_servo) + '-0'
                    if not key_name in position_for_i_smot:
                        key_name = key_name + '-0'
                    else:
                        key_name = str(number_of_servo+1) + '-0-0'
                    runtime_data['i_smot'][key_name] = 100
        sleep(0.01)


def move(encoder_id, power):
    max_range = capabilities['servo']['servo_range'][str(encoder_id)][1]
    min_range = capabilities['servo']['servo_range'][str(encoder_id)][0]
    pre_power = runtime_data['servo_status'][encoder_id] + power
    if max_range >= pre_power >= min_range:
        runtime_data['servo_status'][encoder_id] = pre_power


def move_encoder(encoder_id, degree):
    max_range = capabilities['servo']['servo_range'][str(encoder_id)][1]
    min_range = capabilities['servo']['servo_range'][str(encoder_id)][0]
    if max_range >= degree >= min_range:
        runtime_data['servo_status'][encoder_id] = degree


def action(obtained_data, arm, speed):
    if "misc" in obtained_data:
        if obtained_data["misc"]:
            for i in obtained_data["misc"]:
                if i == 0:
                    arm.set_vacuum_gripper(on=True)
                if i == 1:
                    arm.set_vacuum_gripper(on=False)
                if i == 2:
                    arm.open_lite6_gripper()
                if i == 3:
                    arm.close_lite6_gripper()
    if 'servo_position' in obtained_data:
        try:
            if obtained_data['servo_position']:
                for data_point in obtained_data['servo_position']:
                    device_id = data_point
                    encoder_position = actuators.get_position_data(
                        obtained_data['servo_position'][data_point], capabilities, device_id)
                    move_encoder(device_id, encoder_position)
                angle_list = []
                for i in runtime_data['servo_status']:
                    angle_list.append(runtime_data['servo_status'][i])
                angle_list.append(0)  # last one doesn't do anything so just add 0
                arm.set_servo_angle(angle=angle_list, speed=speed)
        except Exception as e:
            print("ERROR: ", e)
            traceback.print_exc()

    if 'servo' in obtained_data:
        try:
            if obtained_data['servo']:
                for data_point in obtained_data['servo']:
                    new_position = obtained_data['servo'][data_point]
                    if data_point % 2 != 0:
                        new_position *= -1
                    device_id = (data_point // 2)
                    power = new_position / 10
                    move(device_id, power)
                angle_list = []
                for i in runtime_data['servo_status']:
                    angle_list.append(runtime_data['servo_status'][i])
                angle_list.append(0)  # last one doesn't do anything so just add 0
                arm.set_servo_angle(angle=angle_list, speed=speed)
        except Exception as e:
            print("ERROR: ", e)
            traceback.print_exc()
    # servo_id_used = []
    # for servo_id in runtime_data['servo_status']:
    #     if servo_id not in servo_id_used:
    #         runtime_data['servo_status'][servo_id].append(runtime_data['servo_status'][servo_id][2])
    #         runtime_data['servo_status'][servo_id].popleft()
    # runtime_data['i_smot'].clear()
    # for servo_id in runtime_data['servo_status']:
    #     get_speed = calculate_the_servo_speed(runtime_data['servo_status'][servo_id],
    #                                           feagi_settings['feagi_burst_speed'])
    #     new_name = pns.fetch_servo_motion_sensor_size_and_return_percentage(get_speed, servo_id)
    #     runtime_data['i_smot'][new_name] = 100
    return speed


if __name__ == "__main__":
    runtime_data = \
        {
            "current_burst_id": 0,
            "feagi_state": None,
            "cortical_list": (),
            "battery_charge_level": 1,
            "host_network": {},
            'servo_status': {},
            'i_spos': {},
            'i_smot': {}
        }

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

    # UFACTORY SETTING
    ip = "192.168.1.156"
    arm = XArmAPI(ip)  # we don't need that complicated above.
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(state=0)
    speed = 200
    arm.set_pause_time(0)
    # UFACTORY ENDS
    pose_to_default(arm, capabilities['servo']['count'])

    threading.Thread(target=updating_encoder_position_in_bg, args=(arm,), daemon=True).start()
    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                pns.check_genome_status_no_vision(message_from_feagi)
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                speed = action(obtained_signals, arm, speed)

            try:
                message_to_feagi = sensors.add_generic_input_to_feagi_data(runtime_data,
                                                                           message_to_feagi)
                runtime_data['i_spos'].clear()
                runtime_data['i_smot'].clear()
            except Exception as e:
                print("error: ", e)
            sleep(feagi_settings['feagi_burst_speed'])
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings,
                                 feagi_settings)
            message_to_feagi.clear()
        except KeyboardInterrupt as ke:  # Keyboard error
            arm.disconnect()
            break
        except Exception as e:
            arm.disconnect()
            print("ERROR! : ", e)
            traceback.print_exc()
            break
