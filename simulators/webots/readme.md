# Webots 
A python-based Webots controller that connects Webots to FEAGI. The controller automatically generates cortical areas based on the sensors and actuators that the Webots robot has. The user can then create the desired connections between cortical areas using the FEAGI Playground/Brain Visualizer.

## Setting Up FEAGI
Instructions on setting up FEAGI can be found [here](https://github.com/feagi/feagi/wiki/Deployment)

## Installing Webots
- Download and install [Webots](https://cyberbotics.com/doc/guide/installation-procedure)
- Compatible with Windows, macOS, and Linux
- Recommended: Install latest stable version
- Ensure Python 3.8 or higher is installed on your system

## Running the Controller
### Running the Controller Externally
  1. Ensure that FEAGI is running
  2. In Webots, click the drop down arrow next to the robot node in the scene tree (the panel on the left)
  3. Click on controller, then click on select
  4. In the window that pops up, choose "<extern\>" then hit OK
  5. In a terminal, navigate to bin directory of webots. On Windows, you can get the path by clicking "Open file location" after right clicking the Webots desktop shortcut
  6. Type the following command, depending on your operating system. \
    Windows: `webots-controller.exe [options] path/to/controller/file` \
    macOS: `$WEBOTS_HOME/Contents/MacOS/webots-controller [options] path/to/controller/file` \
    Linux: `$WEBOTS_HOME/webots-controller [options] path/to/controller/file` 

   More information about running an external controller in Webots, such as options can be found [here](https://cyberbotics.com/doc/guide/running-extern-robot-controllers?version=released)


## Webots Device Compatibility

The capabilities are generated by looking at the devices on the robot, and then determining which type of FEAGI devices they are. Currently, Webots has more device types than FEAGI, and therefore not all Webots devices are supported. Below are lists of compatible and incompatible devices.

### Compatible Devices
- Accelerometer
- Camera
- DistanceSensor
- Gyro
- InertialUnit
- Lidar
- PositionSensor
- TouchSensor
- LinearMotor
- RotationalMotor

### Incompatible Devices
- Compass
- GPS
- LightSensor
- Radar
- RangeFinder
- Receiver
- Brake
- Connector
- Display
- Emitter
- LED
- Muscle
- Pen
- Propeller
- Speaker
- Track
