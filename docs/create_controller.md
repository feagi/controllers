# How to Create Your Own Controller

Everyone has their own preferences when getting started with controller development. There is no single "right way" to build your own controller.

The repository contains multiple different controllers since there is no standard approach for generic devices or robots. However, many components share similarities. For example, accelerometers consistently return x, y, and z coordinates, while batteries return percentage values.

This guide will demonstrate how to implement and integrate controllers for unfamiliar devices.

## Requirements

To create a functional controller, you need the following components:

1. `capabilities.json` - Available at [NeuroRobotics Studio](https://neurorobotics.studio/capabilities)
2. `networking.json` - Available in the controller template
3. `controller.py` - Available in the controller template
4. `requirements.txt` - Available in the controller template
5. `feagi_connector` - Install using: `pip3 install feagi_connector`

## Achieving Smooth Robot Movement

For optimal performance, your robot should not have embedded or independent code. To ensure FEAGI maintains full control without conflicts:

- The robot should only receive action commands from FEAGI
- The robot should only send raw data streams back to FEAGI
- Avoid running additional code on the robot itself

The controller serves as the communication bridge between your robot and FEAGI.