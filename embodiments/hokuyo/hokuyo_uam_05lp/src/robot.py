#!/usr/bin/env python3

# Copyright 2016-2022 The FEAGI Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import sys
import traceback
import math
import geometry_msgs.msg
import rclpy
import std_msgs.msg
import os
import os.path
import subprocess
import requests
import xml.etree.ElementTree as Xml_et
import numpy as np
import pickle
import lz4.frame
from version import __version__
from std_msgs.msg import String
from subprocess import PIPE, Popen
from time import sleep
from rclpy.node import Node
from geometry_msgs.msg import Twist
from feagi_connector import retina
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from feagi_connector import feagi_interface as feagi
from sensor_msgs.msg import LaserScan, Image, BatteryState, Imu
from rclpy.qos import qos_profile_sensor_data
from threading import Thread
from datetime import datetime

feagi.validate_requirements(
    'src/requirements.txt')  # you should get it from the boilerplate generator
lidar_data = []


class ScalableSubscriber(Node):
    def __init__(self, subscription_name, msg_type, topic):
        super().__init__(subscription_name)
        self.subscription = self.create_subscription(
            msg_type,
            topic,
            self.listener_callback,
            qos_profile=qos_profile_sensor_data)
        self.topic = topic
        self.counter = 0

    def listener_callback(self, msg):
        global lidar_data
        lidar_data = msg.ranges


class UltrasonicSubscriber(ScalableSubscriber):
    def __init__(self, subscription_name, msg_type, topic):
        super().__init__(subscription_name, msg_type, topic)


def convert_lidar_to_feagi_data(full_lidar_data, cortical_size):
    result = {'ilidar': {}}
    total_array = []
    counter = 0
    length_based_off_cortical = int(len(full_lidar_data) / cortical_size[0])
    for x in range(len(full_lidar_data)): # grab
        total_array.append(1 / full_lidar_data[x])
        if len(total_array) == length_based_off_cortical:
            name = (counter, 0, 0)
            counter += 1
            try:
                result['ilidar'][name] = sum(total_array) // len(total_array)
                total_array.clear()
            except:
                traceback.print_exc()
    # print(result['ilidar'])
    return result


if __name__ == '__main__':
    rclpy.init(args=None)
    runtime_data = dict()
    executor = rclpy.executors.MultiThreadedExecutor()

    ultrasonic_feed = UltrasonicSubscriber('scan', LaserScan, 'scan')
    executor.add_node(ultrasonic_feed)
    executor_thread = Thread(target=executor.spin, daemon=True)
    executor_thread.start()

    print("Ready...")
    config = feagi.build_up_from_configuration("src/")
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

    # Waiting for lidar to start up
    while True:
        try:
            message_from_feagi = pns.message_from_feagi

            # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
            if message_from_feagi is not None:
                pns.check_genome_status_no_vision(message_from_feagi)
                feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(
                    message_from_feagi, feagi_settings['feagi_burst_speed'])

            ## output: [distance_at_minus135deg, distance_at_minus134.75deg, distance_at_minus134.5deg, ...]
            if lidar_data:
                if pns.full_list_dimension:
                    size = pns.full_list_dimension['ilidar'][
                        'cortical_dimensions_per_device']
                    new_data = convert_lidar_to_feagi_data(lidar_data, size)
                    message_to_feagi = sensors.add_generic_input_to_feagi_data(
                        new_data,
                        message_to_feagi)
            sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel,
                                 agent_settings, feagi_settings)
            message_to_feagi.clear()
        except KeyboardInterrupt:
            print("\nStopping measurements...")
            break
        except Exception as e:
            print("error: ", e)
            traceback.print_exc()

    ultrasonic_feed.destroy_node()
    rclpy.shutdown()
