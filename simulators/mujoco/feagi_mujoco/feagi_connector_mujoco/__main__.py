#!/usr/bin/env python3


import traceback
from time import sleep
import feagi_connector_mujoco import controller as feagi_controller_mujoco
from feagi_connector import feagi_interface as feagi


if __name__ == '__main__':
    current_path = feagi_connector_mujoco.__path__
    feagi.validate_requirements(str(current_path[0]) + '/requirements.txt')  # you should get it from the boilerplate generator

    while True:
        try:
            feagi_controller_mujoco.start()
            sleep(5)
        except Exception as e:
            print(f"Controller run failed", e)
            traceback.print_exc()
            sleep(2)

