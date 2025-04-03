import copy
import time
import threading
import sys
import subprocess
import argparse
import json
from version import __version__
from feagi_connector import retina
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector import feagi_interface as FEAGI
import base64
import numpy as np
import cv2

camera_data = {"vision": {'0': []}}
previous_frame_data = dict()
rgb = dict()
rgb['camera'] = dict()
raw_data_msg = {}
FEAGI.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator
gazebo_actuator = {'servo': {}, 'motor': {}}


def check_the_flag():
    parser = argparse.ArgumentParser(description="Run Gazebo simulation and capture JSON output from a topic.")
    parser.add_argument("--sdf", type=str, default="shapes.sdf", help="Path to the SDF file")

    args, remaining_args = parser.parse_known_args()
    path = args.sdf  # e.g., './humanoid.xml' or 'C:/path/to/humanoid.xml'
    available_list_from_feagi_connector = FEAGI.get_flag_list()
    cleaned_args = []
    skip_next = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if arg in available_list_from_feagi_connector:
            cleaned_args.append(arg)
            if i + 1 < len(sys.argv[1:]) and not sys.argv[1:][i + 1].startswith("-"):
                cleaned_args.append(sys.argv[1:][i + 1])
                skip_next = True
    sys.argv = [sys.argv[0]] + cleaned_args
    return path


def create_entity():
    """
    Function to create a new entity in Gazebo using the gz service command.
    """
    create_command = [
        "gz", "service", "-s", "/world/free_world/create",
        "--reqtype", "gz.msgs.EntityFactory",
        "--reptype", "gz.msgs.Boolean",
        "--timeout", "300",
        "--req",
        "sdf_filename: 'smart_car.sdf' pose: {position: {z: 1}} name: 'new_name' allow_renaming: false"
    ]

    try:
        # Run the command and capture the output
        result = subprocess.run(create_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("Entity creation output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to create entity:")
        print(e.stderr)
    except FileNotFoundError:
        print("The 'gz' command was not found. Make sure it is installed and available in your PATH.")


def initalize_sensor(sensor_name):
    topic_command = ["gz", "topic", "-e", "-t", "/" + str(sensor_name), "--json-output"]
    topic_process = subprocess.Popen(topic_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return topic_process


def send(topic, message_type, data):
    command = f'gz topic -t {topic} -m {message_type} -p "data: {data}" &'
    subprocess.run(command, shell=True)


def get_data_json(instance, sensor_name, initalize_data):
    raw_data_msg[sensor_name] = initalize_data
    while True:
        raw_data_msg[sensor_name] = json.loads(instance.stdout.readline())
        time.sleep(0.0001)


def read_camera(raw_data_msg):
    raw_data = copy.deepcopy(raw_data_msg)
    msg = raw_data
    if len(msg) > 0:
        data = msg['data']
        height = int(msg['width'])
        width = int(msg['height'])
        decoded_data = list(base64.b64decode(data))
        new_rgb = np.array(decoded_data, dtype=np.uint8)
        if width * height * 4 == len(new_rgb):
            bgr = new_rgb.reshape(width, height, 4)
            return cv2.cvtColor(bgr, cv2.COLOR_RGBA2RGB)
        bgr = new_rgb.reshape(width, height, 3)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    else:
        return []


def monitor_motor_in_background(gazebo_actuator, feagi_settings):
    previous_state = {
        'servo': {},
        'motor': {}
    }

    while True:
        changes_to_send = {
            'servo': [],
            'motor': []
        }
        # Check each actuator type (servo and motor)
        for actuator_type in ['servo', 'motor']:
            current_values = gazebo_actuator[actuator_type]
            prev_values = previous_state[actuator_type]

            for channel, value in current_values.items():
                if channel not in prev_values or value != prev_values[channel]:
                    changes_to_send[actuator_type].append(channel)

        if changes_to_send['servo'] or changes_to_send['motor']:
            for channel in changes_to_send['servo']:
                topic = f'/S{channel}'
                send(topic, 'gz.msgs.Double', gazebo_actuator['servo'][channel])

            for channel in changes_to_send['motor']:
                topic = f'/M{channel}'
                send(topic, 'gz.msgs.Double', gazebo_actuator['motor'][channel])

        previous_state = {
            'servo': gazebo_actuator['servo'].copy(),
            'motor': gazebo_actuator['motor'].copy()
        }
        time.sleep(feagi_settings['feagi_burst_speed'])


def data_opu(action, gazebo_actuator):
    old_message = {}
    while True:
        message_from_feagi = pns.message_from_feagi
        if old_message != message_from_feagi:
            if message_from_feagi:
                if pns.full_template_information_corticals:
                    obtained_signals = pns.obtain_opu_data(message_from_feagi)
                    gazebo_actuator = action(obtained_signals, gazebo_actuator)
                    old_message = copy.deepcopy(message_from_feagi)
        time.sleep(0.001)


def action(obtained_data, gazebo_actuator):
    recieve_motor_data = actuators.get_motor_data(obtained_data)
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    if recieve_servo_position_data:
        for servo_id in recieve_servo_position_data:
            if servo_id not in gazebo_actuator['servo']:
                gazebo_actuator['servo'][servo_id] = recieve_servo_position_data[servo_id]
            gazebo_actuator['servo'][servo_id] = recieve_servo_position_data[servo_id]

    if recieve_servo_data:
        for servo_id in recieve_servo_data:
            if servo_id not in gazebo_actuator['servo']:
                gazebo_actuator['servo'][servo_id] = recieve_servo_data[servo_id]
            gazebo_actuator['servo'][servo_id] = recieve_servo_data[servo_id]

    if recieve_motor_data:
        for motor_id in recieve_motor_data:
            if motor_id not in gazebo_actuator['motor']:
                gazebo_actuator['motor'][motor_id] = recieve_motor_data[motor_id]
            gazebo_actuator['motor'][motor_id] += recieve_motor_data[motor_id]
    return gazebo_actuator


if __name__ == '__main__':
    world = check_the_flag()
    runtime_data = dict()
    config = FEAGI.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    actuators.start_generic_opu(capabilities)

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        FEAGI.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # overwrite manual
    threading.Thread(target=retina.vision_progress, args=(default_capabilities, feagi_settings, camera_data,),
                     daemon=True).start()

    # # camera
    # camera_instance = initalize_camera()
    # threading.Thread(target=get_camera_json, args=(camera_instance,), daemon=True).start()
    # # gyro
    # gyro_instance = initalize_gyro()
    # threading.Thread(target=get_gyro_json, args=(gyro_instance,), daemon=True).start()
    # # ultrasonic
    # ultrasonic_instance = initalize_ultrasonic()
    for instance in capabilities['input']:
        for index in capabilities['input'][instance]:
            print(capabilities['input'][instance][index]['custom_name'])
            if instance == "camera":
                sensor_instance = initalize_sensor(capabilities['input'][instance][index]['custom_name'] + "/image")
                threading.Thread(target=get_data_json, args=(sensor_instance, "/" + capabilities['input'][instance][index]['custom_name'] + "/image", [],), daemon=True).start()
                sensor_instance = initalize_sensor(capabilities['input'][instance][index]['custom_name'])
                threading.Thread(target=get_data_json, args=(sensor_instance, "/" + capabilities['input'][instance][index]['custom_name'], [],), daemon=True).start()
                print("sensor_instance: ", sensor_instance)
            else:
                sensor_instance = initalize_sensor(capabilities['input'][instance][index]['custom_name'])
                threading.Thread(target=get_data_json, args=(sensor_instance, capabilities['input'][instance][index]['custom_name'], [],), daemon=True).start()
        # print("instance: ", instance, " and custom name: ", capabilities['input'][instance])
        # threading.Thread(target=get_ultrasonic_json, args=(ultrasonic_instance,), daemon=True).start()
    threading.Thread(target=data_opu, args=(action, gazebo_actuator), daemon=True).start()
    threading.Thread(target=monitor_motor_in_background, args=(gazebo_actuator, feagi_settings), daemon=True).start()
    # server_command = f"gz sim -v 4 {world} -s -r"
    # gui_command = "gz sim -v 4 -g"
    # server_process = subprocess.Popen(server_command, shell=True)
    # gui_process = subprocess.Popen(gui_command, shell=True)

    print("Creating a new entity in Gazebo...")
    time.sleep(2)
    # create_entity()
    while True:
        try:
            # TEMPORARILY COMMENTED OUT
            camera_index = 0
            for sensor_data in raw_data_msg:
                if 'pixelFormatType' in raw_data_msg[sensor_data]:
                    camera_data['vision'][str(camera_index)] = read_camera(raw_data_msg[sensor_data])
                    camera_index += 1
            for data in camera_data['vision']:
                if camera_data['vision']:
                    raw_frame = copy.deepcopy(camera_data['vision'])
                    # Post image into vision
                    previous_frame_data, rgb, default_capabilities = retina.process_visual_stimuli(
                        raw_frame,
                        default_capabilities,
                        previous_frame_data,
                        rgb, capabilities)
            # INSERT SENSORS INTO the FEAGI DATA SECTION BEGIN
            message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)

            # # Add gyro data into feagi data
            data_from_gyro = raw_data_msg['gyro']
            if data_from_gyro:
                gyro = {'0': [data_from_gyro['orientation']['x'],
                              data_from_gyro['orientation']['y'],
                              data_from_gyro['orientation']['z']]}
                if gyro:
                    message_to_feagi = sensors.create_data_for_feagi('gyro', capabilities, message_to_feagi, gyro,
                                                                     symmetric=True, measure_enable=True)
            # data_from_ultrasonic = raw_data_msg['ultrasonic']
            # if data_from_ultrasonic:
            #     if data_from_ultrasonic['ranges'][0] == '-Infinity':  # temp workaround
            #         data_from_ultrasonic['ranges'][0] = default_capabilities['input']['proximity']['0']['min_value']
            #     if data_from_ultrasonic['ranges'][0] == 'Infinity':  # temp workaround
            #         data_from_ultrasonic['ranges'][0] = default_capabilities['input']['proximity']['0']['max_value']
            #     message_to_feagi = sensors.create_data_for_feagi('proximity', capabilities, message_to_feagi,
            #                                                      data_from_ultrasonic['ranges'][0], symmetric=True)

            # Sending data to FEAGI
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()
            time.sleep(feagi_settings['feagi_burst_speed'])

        # Uncommented this out
        except KeyboardInterrupt as ke:
            print("ERROR: ", ke)
            # Terminate all processes after 60 minutes or interruption
            # server_process.terminate()
            # gui_process.terminate()

            # Wait for processes to cleanly exit
            # server_process.wait()
            # gui_process.wait()
            break
