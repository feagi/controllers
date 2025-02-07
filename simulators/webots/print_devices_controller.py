from controller import Robot


# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# You should insert a getDevice-like function in order to get the
# instance of a device of the robot. Something like:
#  motor = robot.getDevice('motorname')
#  ds = robot.getDevice('dsname')
#  ds.enable(timestep)

#array to store all distance sensors
sensors = []
actuators = []

print("All Devices:")

#print all device names
for i in range(robot.getNumberOfDevices()):
    device = robot.getDeviceByIndex(i)
    device_name = device.getName()
    print(f"\t {device_name}")
    #type(device).__name__ gets class name
    if "Motor" in type(device).__name__:
        actuators.append(device)
    elif "Sensor" in type(device).__name__:
        sensors.append(device)
    
    
#print all sensors
print(" ")    
print("All Sensors:")
for sensor in sensors:
    sensor.enable(timestep)
    print(f"\t {sensor.getName()}")
   

#print all actuators
print(" ")    
print("All Actuators:")
for actuator in actuators:
    print(f"\t {actuator.getName()}")
    

#print sensor keys
print(" ")    
print("All Sensors and Keys:")
for sensor in sensors:
    print(f"\t {sensor.getName()}:")
    print(f"\t\t Value: {sensor.getValue()}")
    print(f"\t\t SamplingPeriod: {sensor.getSamplingPeriod()}")
    print(f"\t\t Model: {sensor.getModel()}")

while robot.step(timestep) != -1:
    pass