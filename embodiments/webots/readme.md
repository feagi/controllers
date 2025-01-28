# Webots 
## Information
Technical Stack:
- Programming Language: Python.
- APIs and Protocols: Webots API, FEAGI SDK, websockets, ZMQ

## Setup Instructions
1. Install Webots
   - Download and install Webots from: https://cyberbotics.com/doc/guide/installation-procedure
   - Compatible with Windows, macOS, and Linux
   - Recommended: Install latest stable version
   - Ensure Python 3.8 or higher is installed on your system
2. Learn Webots Fundamentals
   - Begin with the Webots GUI guide: https://cyberbotics.com/doc/guide/getting-started-with-webots
   - Key areas to understand:
      World and scene structure
      Robot node hierarchy
      Simulation controls
      Basic world editing
3. Study the Python API
- Documentation: https://cyberbotics.com/doc/guide/cpp-java-python#python-example
   - Focus on these essential components:
      Camera sensor implementation
      Robot positioning and movement
      Environmental sensing and interaction
      Basic control mechanisms
      Sensor data acquisition
      Actuator control and feedback
      Robot controller structure
4. Implement FEAGI Controller
   - Reference: https://github.com/feagi/controllers/blob/main/README.md
   - Development requirements:
      Create sensor data pipeline from Webots
      Implement FEAGI data processing
      Develop control command interface
      Establish bidirectional communication

## Controller
Boilerplates are provided. A controller requires capabilities, networking, requirements.txt, and version specifications.

## Libraries
Feagi-connector is the library that enables communication with the brain (FEAGI). We need to create a controller for Blender.

## Troubleshooting
- Join our [Discord community](https://discord.gg/GxHXvY79) to chat with other users and ask questions
- If you encounter issues building the controller, please create an issue in the repository

# Project Objective
1) This is very similar to Mujoco and Gazebo, but the difference is that this uses Webots. It should work with FEAGI and enable FEAGI to control any models. See the example below:


