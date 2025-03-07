# Gazebo

## Information
- Version: gz only
- Programming: sdf, python

# Set up instructions  
There are three different ways to install Gazebo. Fortunately, Gazebo supports all platforms. The Windows OS has a slightly unique setup for installing Gazebo since it uses WSL, which is essentially a Linux environment. So, technically, you are only installing Gazebo on Linux or Mac.

## Windows 11 set up
- wsl --install
- sudo apt-get update
- sudo apt-get install curl lsb-release gnupg
- sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
- echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
- sudo apt-get update
- sudo apt-get install gz-harmonic

## Mac (Apple Silicon)
- ulimit -n unlimited 
- /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)" 
- brew tap osrf/simulation
- brew install gz-ionic

## Linux (24.04)
- sudo apt-get update
- sudo apt-get install lsb-release gnupg
- sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
- echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
- sudo apt-get update
- sudo apt-get install gz-ionic

# Communication
data coming from the gazebo and their topic has a documentation which is here:
https://gazebosim.org/api/msgs/11/install.html

https://gazebosim.org/docs/latest/getstarted/

https://gazebosim.org/api/transport/14/python.html

https://gazebosim.org/api/transport/14/installation.html

This allows you to obtain directly from the python, cpp, or protobuf. As right now, it's not an easy way to set up and build the gazebo without having a cmake to be built.


# How to test your new capabilities using smart car
1) cd to controllers/simulators/gazebo/models/smart_car
2) Run `gz sim -r free_world.sdf` (Mac has a different command, but you need to add '-r')
3) Open a new terminal and navigate to `controllers/simulators/gazebo/models/smart_car`
4) Paste your newly generated capabilities into capabilities.json
5) Run `python3 controller.py --ip YOUR_IP_HERE` (use the IP address where you're running FEAGI)