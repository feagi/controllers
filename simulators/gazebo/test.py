import time
import threading
from feagi_connector import retina
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import feagi_interface as feagi
from gz.msgs11.image_pb2 import Image
from gz.msgs.imu_pb2 import IMU
from gz.transport14 import Node
import numpy as np

camera_data = {"vision": {'0': []}}
previous_frame_data = dict()
gyro = {'0': []}
acc = {'0': []}
feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator


# Callback function to process received Image messages
def image_callback(msg):
    global test
    width = int(msg.width)
    height = int(msg.height)
    raw_data = list(msg.data)
    new_rgb = np.array(raw_data, dtype=np.uint8)
    camera_data['vision']['0'] = new_rgb.reshape(width, height, 3)


def infrared_sensor(msg):
    print(msg)


def imu_sensor(msg):
    gyro['0'] = [msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z]
    acc['0'] = [msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z]


if __name__ == '__main__':
    runtime_data = dict()
    config = feagi.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)

    node = Node()

    camera_topic = "/Camera0/image"
    IR0 = "/IR0/image"
    IR1 = "/IR1/image"
    IR2 = "/IR2/image"
    imu_data = "/imu"

    node.subscribe(Image, camera_topic, image_callback)
    # node.subscribe(Image, IR0, infrared_sensor)
    # node.subscribe(Image, IR1, infrared_sensor)
    # node.subscribe(Image, IR2, infrared_sensor)
    node.subscribe(IMU, imu_data, imu_sensor)

    threading.Thread(target=retina.vision_progress, args=(default_capabilities, feagi_settings, camera_data,),
                     daemon=True).start()

    rgb = dict()
    rgb['camera'] = dict()

    while True:
        raw_frame = camera_data['vision']
        # Post image into vision
        previous_frame_data, rgb, default_capabilities = retina.process_visual_stimuli(
            raw_frame,
            default_capabilities,
            previous_frame_data,
            rgb, capabilities)

        # INSERT SENSORS INTO the FEAGI DATA SECTION BEGIN
        message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)

        if gyro:
            message_to_feagi = sensors.create_data_for_feagi('gyro', capabilities, message_to_feagi, gyro,
                                                             symmetric=True)

        # Add accelerator data into feagi data
        if acc:
            message_to_feagi = sensors.create_data_for_feagi('accelerometer', capabilities, message_to_feagi,
                                                             acc, symmetric=True,
                                                             measure_enable=True)

        # Sending data to FEAGI
        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
        message_to_feagi.clear()
        time.sleep(feagi_settings['feagi_burst_speed'])
