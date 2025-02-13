"""print_devices controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot

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

#prints the given sensors data     
def print_sensor_data(sensor):
    print()


print_actuators()
print_sensors()

# Main loop:
while robot.step(timestep) != -1:
    # Read the sensors:

    # Process sensor data here.
    
    #print sensor data
    # for sensor in robot_sensors:
    #     if type(sensor).__name__ == "PositionSensor":
    #          print("Sensor: " + sensor.getName() + 
    #                "\n\tValue: " + str(sensor.getValue()))
                    
    #     elif type(sensor).__name__ == "Camera":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tImage: " + str(sensor.getImageArray()))
                                  
    #     elif type(sensor).__name__ == "RangeFinder":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tRange: " + str(sensor.getRangeImageArray()))
                
    #     elif type(sensor).__name__ == "Lidar":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tRange: " + str(sensor.getRangeImageArray()))
            
    #     elif type(sensor).__name__ == "Accelerometer":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tValues: " + str(sensor.getValues()))
            
    #     elif type(sensor).__name__ == "InertialUnit":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tValue: " + str(sensor.getRollPitchYaw()))
            
    #     elif type(sensor).__name__ == "Gyro":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tAngular Velocities: " + str(sensor.getValues()))
            
    #     elif type(sensor).__name__ == "TouchSensor":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tForce: " + str(sensor.getValue()))
            
    #     elif type(sensor).__name__ == "DistanceSensor":
    #         print("Sensor: " + sensor.getName() + 
    #               "\n\tDistance: " + str(sensor.getValue()))            

    # Enter here functions to send actuator commands:

    pass

# Enter here exit cleanup code.
