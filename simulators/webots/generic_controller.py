"""print_devices controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot
import inspect

#prints the robot's actuators
def print_actuators():
    print("Actuators: \n")
    for actuator in robot_actuators:
        print("\t Name: " + actuator.getName() + 
            "\n\t\tType: " + type(actuator).__name__ + "\n")

#prints the robot's sensors
def print_sensors():
    print("Sensors:\n")
    for sensor in robot_sensors:
        print("\tName: " + sensor.getName() + 
            "\n\t\tType: " + type(sensor).__name__)

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

def print_all_ds():
    for ds in robot_sensors:
        if "ds" in ds.getName():
            print(f"{ds.getName()} - {ds.getValue()}")

#move the motors to make the robot spin
def pioneer2_wheel_movements():
    #gets the motors
    left_wheel = robot.getDevice("left wheel motor")
    right_wheel = robot.getDevice("right wheel motor")

    print_all_ds()
            
    #sets velocities opposite eachother, moves and then stops
    left_wheel.setVelocity(-3)
    right_wheel.setVelocity(3)
    robot.step(10 * timestep)
    left_wheel.setVelocity(0)
    right_wheel.setVelocity(0)

    print_all_ds()



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

# Main loop:
while robot.step(timestep) != -1:
    # Read the sensors:

    # Process sensor data here.
    
    # Enter here functions to send actuator commands:

    pass

# Enter here exit cleanup code.
