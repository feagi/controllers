#!/usr/bin/env python3


import traceback
from time import sleep
import feagi_connector_mujoco
from feagi_connector import feagi_interface as feagi
from feagi_connector_mujoco import controller as feagi_controller_mujoco


if __name__ == '__main__':
    current_path = feagi_connector_mujoco.__path__
    feagi.validate_requirements(str(current_path[0]) + '/requirements.txt')
    try:
        feagi_controller_mujoco.start(current_path[0] + '/')
        sleep(5)
    except Exception as e:
        print(f"Controller run failed", e)
        traceback.print_exc()

