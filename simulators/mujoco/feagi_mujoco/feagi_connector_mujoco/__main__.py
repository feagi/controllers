#!/usr/bin/env python3

"""
Copyright 2016-present Neuraville Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================
"""

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

