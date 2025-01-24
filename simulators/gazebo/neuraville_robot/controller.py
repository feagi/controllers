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

previous_frame_data = dict()
camera_data = {"vision": []}
FEAGI.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator


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
        "sdf_filename: 'smart_car.sdf' pose: {position: {z: 1}} name: 'new_name' allow_renaming: true"
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


def initalize_gyro():
    topic_command = ["gz", "topic", "-e", "-t", "/imu", "--json-output"]
    topic_process = subprocess.Popen(topic_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return topic_process


def read_gyro(gyro_instance):
    return json.loads(gyro_instance.stdout.readline())


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

    server_command = f"gz sim -v 4 {world} -s -r"
    gui_command = "gz sim -v 4 -g"
    server_process = subprocess.Popen(server_command, shell=True)
    gui_process = subprocess.Popen(gui_command, shell=True)

    print("Creating a new entity in Gazebo...")
    time.sleep(2)
    create_entity()
    gyro_instance = initalize_gyro()
    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                obtained_signals = pns.obtain_opu_data(message_from_feagi)

            # Add gyro data into feagi data
            data_from_gyro = read_gyro(gyro_instance)
            gyro = {'0': [data_from_gyro['orientation']['x'], data_from_gyro['orientation']['y'], data_from_gyro['orientation']['z']]}
            if gyro:
                message_to_feagi = sensors.create_data_for_feagi('gyro', capabilities, message_to_feagi, gyro,
                                                                 symmetric=True)

            # Sending data to FEAGI
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()
            time.sleep(feagi_settings['feagi_burst_speed'])
        except KeyboardInterrupt as ke:
            print("ERROR: ", ke)
            # Terminate all processes after 60 minutes or interruption
            server_process.terminate()
            gui_process.terminate()

            # Wait for processes to cleanly exit
            server_process.wait()
            gui_process.wait()
            break
