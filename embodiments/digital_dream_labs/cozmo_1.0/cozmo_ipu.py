from feagi_connector import pns_gateway as pns
from feagi_connector import sensors
import traceback


def cozmo_ipu(robot, capabilities, angle_of_head, angle_of_arms, message_to_feagi):
    if robot['battery']:
        message_to_feagi = sensors.create_data_for_feagi('battery', capabilities, message_to_feagi, robot['battery'],symmetric=False)
    
    if robot['gyro']:
        message_to_feagi = sensors.create_data_for_feagi('gyro', capabilities, message_to_feagi, robot['gyro'],symmetric=True)
    
    # # Add accelerator section
    if robot['accelerator']:
        message_to_feagi = sensors.create_data_for_feagi('accelerometer', capabilities, message_to_feagi, robot['accelerator'], symmetric=True)
    
    if robot['proximity']:
        message_to_feagi = sensors.create_data_for_feagi('proximity', capabilities, message_to_feagi, robot['proximity'][0], symmetric=True, measure_enable=True)
    return message_to_feagi