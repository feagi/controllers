"""print_devices controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot
import inspect
import json

#prints the robot's actuators
def print_actuators():
    print("Actuators: \n")
    for num, actuator in enumerate(robot_actuators):
        print(f"\t Name: {actuator.getName()}   num:{num}")
        print(f"\t\tType: {type(actuator).__name__} \n")

#prints the robot's sensors
def print_sensors():
    print("Sensors:\n")
    for num, sensor in enumerate(robot_sensors):
        print(f"\t Name: {sensor.getName()}   num:{num}")
        print(f"\t\tType: {type(sensor).__name__} \n")

#prints the given sensors data, assumes that the sensor is enabled     
def print_sensor_data(sensor):
    if type(sensor).__name__ == "TouchSensor":
        if sensor.getType() in ("WB_TOUCH_SENSOR_BUMPER", "WB_TOUCH_SENSOR_FORCE"):
            print(str(sensor.getValue()))
        else:
            print(str(sensor.getValues()))
    elif type(sensor).__name__ in ("DistanceSensor", "LightSensor", "PositionSensor"):
        print(str(sensor.getValue()))
    elif type(sensor).__name__ in ("Accelerometer", "Compass", "GPS", "Gyro"):
        print(str(sensor.getValues()))
    elif type(sensor).__name__ == "Camera":
        print(str(sensor.getImageArray()))
    elif type(sensor).__name__ == "InertialUnit":
        print(str(sensor.getRollPitchYaw()))
    elif type(sensor).__name__ == "Lidar":
        print(str(sensor.getRangeImageArray()))
    elif type(sensor).__name__ == "Radar":
        print(str(sensor.getTargets()))
    elif type(sensor).__name__ == "RangeFinder":
        print(str(sensor.getRangeImageArray()))
    elif type(sensor).__name__ == "Receiver":
        if sensor.getQueueLength() != 0:
            print(str(sensor.getBytes()))

#print all object methods
def print_methods():
    print("Sensors:\n")
    for i in range(num_devices):
        device = robot.getDeviceByIndex(i)
        print("\tName: " + device.getName() + "\n\t\tType: " + type(device).__name__ + "\n")
        keys = [method for method, _ in inspect.getmembers(device, predicate=inspect.ismethod)]
        print(keys)

#prints all distance sensors
def print_all_ds():
    for ds in robot_sensors:
        if "ds" in ds.getName():
            print(f"{ds.getName()} - {ds.getValue()}")

#move the motors to make the robot spin
def pioneer2_wheel_movements():
    #gets the motors
    left_wheel = robot.getDevice("left wheel motor")
    right_wheel = robot.getDevice("right wheel motor")

    print("Pre-move sensors")
    print_all_ds()
    print()
            
    #sets velocities opposite eachother, moves and then stops
    left_wheel.setVelocity(-3)
    right_wheel.setVelocity(3)
    robot.step(10 * timestep)
    left_wheel.setVelocity(0)
    right_wheel.setVelocity(0)

    print("Post-move sensors")
    print_all_ds()
    print("\n")
    
    #3 seconds
    robot.step(3000)

def pr2_move_arm(arm, positions):
    """
    Move the PR2 arm to a specified position.
    :param arm: "left" or "right"
    :param positions: Dict with joint angles {joint_name: angle}
    """
    """
    Here is an example of how to call this function:
    move_arm("right", {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.5,
        "upper_arm_roll": 0.0,
        "elbow_lift": -0.5,
        "wrist_roll": 0.0
    })
    """
    # Get PR2 motors for the right arm
    right_arm_motors = {
        "shoulder_pan": robot.getDevice("r_shoulder_pan_joint"),
        "shoulder_lift": robot.getDevice("r_shoulder_lift_joint"),
        "upper_arm_roll": robot.getDevice("r_upper_arm_roll_joint"),
        "elbow_lift": robot.getDevice("r_elbow_flex_joint"),
        "wrist_roll": robot.getDevice("r_wrist_roll_joint")
    }
    # Get PR2 motors for the left arm
    left_arm_motors = {
        "shoulder_pan": robot.getDevice("l_shoulder_pan_joint"),
        "shoulder_lift": robot.getDevice("l_shoulder_lift_joint"),
        "upper_arm_roll": robot.getDevice("l_upper_arm_roll_joint"),
        "elbow_lift": robot.getDevice("l_elbow_flex_joint"),
        "wrist_roll": robot.getDevice("l_wrist_roll_joint")
    }
    if arm == "right":
        motors = right_arm_motors
    elif arm == "left":
        motors = left_arm_motors
    else:
        print("Invalid arm name. Use 'left' or 'right'.")
        return
    for joint, angle in positions.items():
        if joint in motors:
            motors[joint].setPosition(angle)
        else:
            print(f"Invalid joint name: {joint}")
        
              
#all possible types of sensors           
all_sensors = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", "Gyro", 
               "InertialUnit", "Lidar", "LightSensor", "PositionSensor", "Radar", "RangeFinder",
               "Receiver", "TouchSensor"]

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

#arrays to store the robots sensors and actuators
robot_sensors = []
robot_actuators = []

num_devices = robot.getNumberOfDevices()

#put devices into correct arrays and enable sensors
for i in range(num_devices):
    device = robot.getDeviceByIndex(i)
    device_name = device.getName()
            
    #append to the correct list
    if type(device).__name__ in all_sensors:
        device.enable(timestep)
        robot_sensors.append(device)  
    else:
        robot_actuators.append(device)

print_actuators()
print_sensors()























def make_capabilities_JSON(all_FEAGI_inputs, all_FEAGI_outputs):
    data = {
        "capabilities": {
            "input": {},
            "output": {}
        }
    }


    for inputType in all_FEAGI_inputs:


        if inputType == cameras:

            # Find lidars and add lidars to cameras
            for secondType in all_FEAGI_inputs:
                if secondType == lidars:
                    inputType += secondType

            # Sort the list again
            inputType = sorted(inputType, key=lambda device: device.getName())

            type = "camera"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "eccentricity_control": {
                        "X offset percentage": 1,
                        "Y offset percentage": 1
                    },
                    "feagi_index": 0,
                    "index": "00",
                    "mirror": False,
                    "modulation_control": {
                        
                        "X offset percentage": 99,
                        "Y offset percentage": 99
                    },
                    "threshold_default": 50
                }



    for inputType in all_FEAGI_inputs:
        if inputType == gyros:
            type = "gyro"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": 0,
                    "max_value": [0, 0, 0],
                    "min_value": [0, 0, 0]
                }


    for inputType in all_FEAGI_inputs:
        if inputType == distanceSensors:
            type = "proximity"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": 0,
                    "max_value": 0,
                    "min_value": 0
                }


    for inputType in all_FEAGI_inputs:
        if inputType == positionSensors:
            type = "servo_position"

            data["capabilities"]["input"][type] = {}

            for num, device in enumerate(inputType):
                data["capabilities"]["input"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": 0,
                    "max_value": 0,
                    "min_value": 0
                }


    for outputType in all_FEAGI_outputs:
        if outputType == motors:
            type = "motor"

            data["capabilities"]["output"][type] = {}

            for num, device in enumerate(outputType):
                data["capabilities"]["output"][type][str(num)] = {
                    "custom_name": device.getName(),
                    "disabled": False,
                    "feagi_index": 0,
                    "max_power": 0,
                    "rolling_window_len": 0
                }


    with open("test.json", "w") as json_file:
        json.dump(data, json_file, indent=4)












all_FEAGI_inputs = []

#add types of devices to each category
#Gyros
gyros = []
for device in robot_sensors:
        if "Gyro" == type(device).__name__:
            gyros.append(device)

#Sort list by getName value
gyros = sorted(gyros, key=lambda device: device.getName())
all_FEAGI_inputs.append(gyros)

#Position Sensors
positionSensors = []
for device in robot_sensors:
        if "PositionSensor" == type(device).__name__:
            positionSensors.append(device)

#Sort list by getName value
positionSensors = sorted(positionSensors, key=lambda device: device.getName())
all_FEAGI_inputs.append(positionSensors)


#Distance Sensors
distanceSensors = []
for device in robot_sensors:
        if "DistanceSensor" == type(device).__name__:
            distanceSensors.append(device)

#Sort list by getName value
distanceSensors = sorted(distanceSensors, key=lambda device: device.getName())
all_FEAGI_inputs.append(distanceSensors)


#Cameras
cameras = []
for device in robot_sensors:
        if "Camera" == type(device).__name__:
            cameras.append(device)

#Sort list by getName value
cameras = sorted(cameras, key=lambda device: device.getName())
all_FEAGI_inputs.append(cameras)


#Lidars
lidars = []
for device in robot_sensors:
        if "Lidar" == type(device).__name__:
            lidars.append(device)

#Sort list by getName value
lidars = sorted(lidars, key=lambda device: device.getName())
all_FEAGI_inputs.append(lidars)



# Get outputs that FEAGI can use in capabilities.json
all_FEAGI_outputs = []

motors = []
for device in robot_actuators:
        if "Motor" == type(device).__name__:
            motors.append(device)

#Sort list by getName value
motors = sorted(motors, key=lambda device: device.getName())
all_FEAGI_outputs.append(motors)



make_capabilities_JSON(all_FEAGI_inputs, all_FEAGI_outputs)



















# Main loop:
while robot.step(timestep) != -1:
    for gyro in robot_sensors:
        if "Gyro" == type(gyro).__name__:
            print(f"\t Name: {gyro.getName()}")
            print(f"\t\tType: {type(gyro).__name__} \n")

            print(f"\t\tValue: {print_sensor_data(gyro)}")

    pass

# Enter here exit cleanup code.
