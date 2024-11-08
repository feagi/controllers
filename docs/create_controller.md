# How to Create Your Own Controller

Everyone has their own preferences for getting started. There is no single right way to build your own controller.

As you can see, the repository contains multiple different controllers. Unfortunately, there is no standard approach when it comes to generic devices or robots.

Fortunately, many components are similar. For example, an accelerometer returns x, y, and z coordinates, and a battery returns a percentage.

This readme will show you how the integration is often used and implemented on unfamiliar controllers.
# No Controller? No problem! Use the template! 

This is the one that Neuraville usually started the base for a new device. 

```
#!/usr/bin/env python

import time
import asyncio
import traceback
import threading
from time import sleep
from collections import deque
from version import __version__
from feagi_connector import sensors
from feagi_connector import actuators
from feagi_connector import retina as retina
from feagi_connector import pns_gateway as pns
from feagi_connector import feagi_interface as FEAGI

runtime_data = {
    "current_burst_id": 0,
    "feagi_state": None,
    "cortical_list": (),
    "battery_charge_level": 1,
    "host_network": {},
    'motor_status': {},
    'servo_status': {}
}

previous_frame_data = {}
rgb = {'camera': {}}
robot = {'accelerator': {}, "proximity": [], "gyro": [], 'servo_head': [], "battery": [],
         'lift_height': []}
camera_data = {"vision": []}


def action(obtained_data):
    # Example for getting servo and motor from FEAGI
    recieve_motor_data = actuators.get_motor_data(obtained_data)
    recieve_servo_data = actuators.get_servo_data(obtained_data)



if __name__ == '__main__':
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


    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi:
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                action(obtained_signals)

            sleep(feagi_settings['feagi_burst_speed'])
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()

        except Exception as e:
            print("ERROR IN COZMO MAIN CODE: ", e)
            traceback.print_exc()
            break
```
You can safely copy and paste this into your configuration. You will need to use your configuration as well.

# How do I make robot move so smooth? 
The robot should not have its own code embedded or any independent code. To allow FEAGI to fully 
control your robot without confusing FEAGI, ensure that there is no code running on the robot 
itself. The robot should simply receive data from FEAGI to perform actions and pass the raw data stream back to FEAGI.

The controller will allow your robot to communicate with FEAGI.

# I need a help.

Of course, you do! Just create an issue and ask your question. 
