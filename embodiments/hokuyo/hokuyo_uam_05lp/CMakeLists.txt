cmake_minimum_required(VERSION 3.5)
project(hokuyo_uam_05lp)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# Install Python modules
ament_python_install_package(src/)

# Install Python executables
install(PROGRAMS
  src/robot.py
  src/configuration.py
  src/networking.json
  src/capabilities.json
  src/requirements.txt
  src/version.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()