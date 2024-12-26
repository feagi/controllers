# FEAGI MuJoCo Connector

A Python connector for interfacing FEAGI with MuJoCo physics simulation.

## See the requirement below:
1) Git: [https://gitforwindows.org/]  
2) Python 3.9 or higher: [https://www.python.org/downloads/]  
3) Docker (if you want to use FEAGI on Docker): [https://docs.docker.com/get-started/introduction/get-docker-desktop/]  


## Installation

```
# For Windows
pip install feagi_connector_mujoco

# For Mac/Linux
pip3 install feagi_connector_mujoco
```

## Usage
To run the connector:

```
# For Windows
python -m feagi_connector_mujoco

# For Mac/Linux
python3 -m feagi_connector_mujoco
```

## Docker Usage
When running with Docker, append the port flag:

```
python -m feagi_connector_mujoco --port 30000
```

## Custom MuJoCo Files

To use your own MuJoCo files, see the [Extra Flags](#extra-flags) section below.

## Load Docker:

	1.	git clone git@github.com:feagi/feagi.git
	2.	cd ~/feagi/docker
	3.	docker compose -f playground.yml pull
	4.	Wait until it’s done.
	5.	docker compose -f playground.yml up

## Open Playground Website:

	1.	Go to http://127.0.0.1:4000/
	2.	Click the “GENOME” button on the top right, next to “API.”
	3.	Click “Essential.”


# Extra flags
Example command: `python controller.py --help`
```
optional arguments:
  -h, --help            Show this help message and exit.
  
  -magic_link MAGIC_LINK, --magic_link MAGIC_LINK
                        Use a magic link. You can find your magic link from NRS studio.
                        
  -magic-link MAGIC_LINK, --magic-link MAGIC_LINK
                        Use a magic link. You can find your magic link from NRS studio.
                        
  -magic MAGIC, --magic MAGIC
                        Use a magic link. You can find your magic link from NRS studio.
                        
  -ip IP, --ip IP       Specify the FEAGI IP address.
  
  -port PORT, --port PORT
                        Change the ZMQ port. Use 30000 for Docker and 3000 for localhost.

  --model_xml_path, --MODEL_XML_PATH
                        Path to the XML file (default: './humanoid.xml')
```
