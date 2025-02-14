"""Controller that Moves Wheels and Checks DS Values"""

import inspect
from controller import Robot



#move left wheel to desired radian amount
def move_left_wheel(amount):
    for actuator in robot_actuators:
        if "left wheel motor" in actuator.getName():
            print("moving left wheel")
            actuator.setPosition(amount)



#move right wheel to desired radian amount
def move_right_wheel(amount):
    for actuator in robot_actuators:
        if "right wheel motor" in actuator.getName():
            print("moving right wheel")
            actuator.setPosition(amount)


#print all distance sensor data
def print_ds_data():
    for sensor in robot_sensors:
        if "ds" in sensor.getName():
            print(f"{sensor.getName()}: \t {sensor.getValue()}")



# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

#all possible types of actuators
all_actuators = ["Brake", "Connector", "Display", "Emitter", "LinearMotor", 
                 "LED", "Muscle", "Pen", "Propeller", "RotationalMotor", 
                 "Speaker", "Track", "Motor"]
      
#all possible types of sensors
all_sensors = ["Accelerometer", "Camera", "Compass", "DistanceSensor", "GPS", 
               "Gyro", "InertialUnit", "Lidar", "LightSensor", 
               "PositionSensor", "Radar", "RangeFinder","Receiver", 
               "TouchSensor"]

num_devices = robot.getNumberOfDevices()

#arrays to store the robots sensors and actuators
robot_sensors = []
robot_actuators = []

#print device names
for i in range(num_devices):
    device = robot.getDeviceByIndex(i)
    device_name = device.getName()
    print(device_name)

    #append to the correct list
    if type(device).__name__ in all_sensors:
        robot_sensors.append(device)

    elif type(device).__name__ in all_actuators:
        robot_actuators.append(device)

#print the robot's actuator names
print("Actuators: \n")
for actuator in robot_actuators:
    print("\t Name: " + actuator.getName() + 
          "\n\t\tType: " + type(actuator).__name__ + "\n")

#print the robot's sensor names
print("Sensors:\n")
for sensor in robot_sensors:
    sensor.enable(timestep)
    print("\tName: " + sensor.getName() + 
          "\n\t\tType: " + type(sensor).__name__ + "\n")



# Main loop:
while robot.step(timestep) != -1:
    #print distance sensors value pre move
    print("pre move:")
    print_ds_data()

    #move the motors to make the robot spin
    move_right_wheel(1)
    move_left_wheel(-1)

    #print distance sensors value post move
    print("post move:")
    print_ds_data()

    print("\n")

    robot.step(1000)
    pass
