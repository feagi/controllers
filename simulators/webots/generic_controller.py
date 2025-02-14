"""print_devices controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot

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
    if type(sensor).__name == "TouchSensor":
        if sensor.getType() == "WB_TOUCH_SENSOR_BUMPER" or "WB_TOUCH_SENSOR_FORCE":
            print(str(sensor.getValue()))
        else:
            print(str(sensor.getValues()))
    elif type(sensor).__name__ == "DistanceSensor" or "LightSensor" or "PositionSensor":
        print(str(sensor.getValue()))
    elif type(sensor).__name__ == "Accelerometer" or "Compass" or "GPS" or "Gyro":
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
        if sensor.getQueueLength != 0:
            print(str(sensor.getBytes()))
        

#all possible types of actuators
all_actuators = ["Brake", "Connector", "Display", "Emitter", "LinearMotor", "LED", 
                 "Muscle", "Pen", "Propeller", "RotationalMotor", "Speaker", "Track", "Motor"]
      
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
        
    elif type(device).__name__ in all_actuators:
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
