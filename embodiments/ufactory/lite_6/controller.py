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
FEAGI.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator



def pose_to_default(arm, capabilities):
    actuators.start_servos(capabilities)
    arm.reset(wait=True)


def calculate_the_servo_speed(rolling_window, seconds):
    last_index = len(rolling_window) - 1
    rolling_delta = rolling_window[last_index] - rolling_window[0]
    burst_duration_total = 3 * seconds
    return rolling_delta / burst_duration_total


def updating_encoder_position_in_bg(arm):
    global runtime_data, capabilities, feagi_settings

    rolling_window = {}
    rolling_window_len = 3
    for servo_id in range(6 * 2):
        rolling_window[servo_id] = deque([0] * rolling_window_len)

    for i in range(len(capabilities['input']['servo_position'])):
        runtime_data['actual_encoder_position'][i] = deque([0, 0, 0, 0, 0])
        runtime_data['for_feagi_data'][i] = 0
    while True:
        new_degree_list_of_servo = arm.get_servo_angle()
        for device_id in range(len(capabilities['output']['servo'])):
            if runtime_data['actual_encoder_position'][device_id]:
                runtime_data['actual_encoder_position'][device_id].append(new_degree_list_of_servo[1][int(device_id)])
                runtime_data['actual_encoder_position'][device_id].popleft()
                runtime_data['for_feagi_data'][device_id] = new_degree_list_of_servo[1][int(device_id)]
        new_dict = dict()
        for current_servo_number in range(0, len(capabilities['input']['servo_position']) * 2, 2):
            number_of_servo = current_servo_number  # A number incrementing from range(12)
            rolling_window[number_of_servo].append(new_degree_list_of_servo[1][number_of_servo // 2])
            # new degree list has 6 servos, so using floor divsion to keep it 6
            rolling_window[number_of_servo].popleft()
            # pop the old index from rolling_window
            get_speed = calculate_the_servo_speed(runtime_data['actual_encoder_position'][number_of_servo/2],
                                                  feagi_settings['feagi_burst_speed'])
            # Get a speed from old index - new index / time
            # print(get_speed)
            position_for_i_smot = pns.fetch_servo_motion_sensor_size_and_return_percentage(
                int(get_speed),
                number_of_servo,
                25)
            if position_for_i_smot is not None:
                if not any(key[:4] == position_for_i_smot[:4] for key in runtime_data['i_smot']):
                    new_dict[position_for_i_smot] = 100
                    key_name = str(number_of_servo) + '-0'
                    if not key_name in position_for_i_smot:
                        key_name = key_name + '-0'
                    else:
                        key_name = str(number_of_servo + 1) + '-0-0'
                    new_dict[key_name] = 100
        runtime_data['i_smot'] = new_dict.copy()
        sleep(0.01)


def action(obtained_data, arm, speed):
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)
    if recieve_servo_position_data:
        angle_list = []
        for i in actuators.servo_status:
            angle_list.append(actuators.servo_status[i])
        angle_list.append(0)  # last one doesn't do anything so just add 0

        for real_id in recieve_servo_position_data:
            servo_number = real_id
            new_power = recieve_servo_position_data[real_id]
            angle_list[servo_number] = new_power
        if not arm.get_is_moving():
            arm.set_servo_angle(angle=angle_list, speed=speed)

    if recieve_servo_data:
        angle_list = []
        for i in actuators.servo_status:
            angle_list.append(actuators.servo_status[i])
        angle_list.append(0)  # last one doesn't do anything so just add 0
        for real_id in recieve_servo_data:
            servo_number = real_id
            new_power = recieve_servo_data[real_id]
            angle_list[servo_number] = new_power
        if not arm.get_is_moving():
            arm.set_servo_angle(angle=angle_list, speed=speed)

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
            'actual_encoder_position': {},
            'for_feagi_data': {},
            'speed_motion': {},
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
    ip = "192.168.1.156" # We gotta keep it super simple. Just look at the back of the robot IP. That's it.
    arm = XArmAPI(ip)
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(state=0)
    speed = 100
    arm.set_pause_time(0)
    # UFACTORY ENDS
    pose_to_default(arm, capabilities)

    threading.Thread(target=updating_encoder_position_in_bg, args=(arm,), daemon=True).start()
    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                pns.check_genome_status_no_vision(message_from_feagi)
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                speed = action(obtained_signals, arm, speed)

            message_to_feagi = sensors.create_data_for_feagi('servo_position', capabilities, message_to_feagi,
                                                             current_data=runtime_data['for_feagi_data'],
                                                             symmetric=True)
            if runtime_data['i_smot']:
                speed_motion = dict()
                speed_motion['i_smot'] = runtime_data['i_smot']
                message_to_feagi = sensors.add_generic_input_to_feagi_data(speed_motion, message_to_feagi)




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
