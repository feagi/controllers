"""Controller that Prints all Sensor Data"""

from controller import Robot

robot = Robot()

#get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

#get the number of all devices
num_devices = robot.getNumberOfDevices()

#arrays to store type of devices
sensors = []
actuators = []


#print all device names
print("Robot Devices:")
for i in range(num_devices):
    device = robot.getDeviceByIndex(i)
    device_name = device.getName()
    print(device_name)

    #type(device).__name__ gets class name
    if "Motor" in type(device).__name__:
        actuators.append(device)

    if "Sensor" in type(device).__name__:
        sensors.append(device)


#print all sensors
print(" ")
print("All Sensors:")
for sensor in sensors:
    sensor.enable(timestep)
    print(sensor.getName())


#print all actuators
print(" ")
print("All Actuators:")
for actuator in actuators:
    print(actuator.getName())


#print sensor keys
print(" ")
print("All Sensor Keys:")
for sensor in sensors:
    print(f"\t {sensor.getName()}:")
    print(f"\t\t Value: {sensor.getValue()}")
    print(f"\t\t SamplingPeriod: {sensor.getSamplingPeriod()}")
    print(f"\t\t Model: {sensor.getModel()}")


# Main loop:
while robot.step(timestep) != -1:
    for sensor in sensors:
        print(f"{sensor.getName()} Value: {sensor.getValue()}")

    pass
