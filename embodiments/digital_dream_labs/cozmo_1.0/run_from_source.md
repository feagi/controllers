# FEAGI Cozmo Connector
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://github.com/Neuraville/controllers/blob/14f4f8d6f010f134a48fa40d1e3b25a85a364fe1/LICENSE.txt)

A Python-based connector that enables seamless integration between FEAGI (The Framework for Evolutionary Artificial General Intelligence) and the Cozmo. This connector facilitates neural network-driven control of Cozmo.


## 💻 Usage Options
### 1. Neurorobotics Studio (Recommended)

The Neurorobotics Studio provides a user-friendly web interface for quick setup and experimentation.

### Prerequisites

- Python 3.9 or higher ([Download Python](https://www.python.org/downloads/))
- Dongle Wi-Fi


#### Getting Started with Neurorobotics Studio


1. Visit [Neurorobotics Studio](https://neurorobotics.studio/lab)

2. Create a New Experiment:
   - Click "Create"
   - Select "Cozmo"
   - Choose any genome. "Barebones genome" is highly recommended.
   - Name your experiment
   - Click "Create"

3. Connect via Magic Link:
   - Navigate to "Embodiment" in the top menu
   - Click "Magic Link"
   - Run the provided command:

#### Windows
1) Get a WiFi dongle and connect it with Cozmo.
2) Download the Cozmo cognitive connector: [here](https://storage.googleapis.com/nrs-artifacts/em-iqgkoadn/controller.zip).
3) Unzip and click the executable file, `controller.exe`
4) You should see a white dialog screen pop up.
5) Click the "Magic Link" button, then paste it into the textbox under the Magic Link.

![image](https://storage.googleapis.com/nrs-artifacts/em-iqgkoadn/pasteyourmagictohere.png)

Note: If you don't want to download anything but prefer to run it from Python or if you are on Mac/Linux, go to the next section "Run without installer (For NRS or Docker)".

### 2. Docker Deployment
### Prerequisites

- Python 3.9 or higher ([Download Python](https://www.python.org/downloads/))
- For Docker deployment:
  - Git ([Windows only Download](https://gitforwindows.org/))
  - Docker Desktop ([Installation Guide](https://docs.docker.com/get-started/introduction/get-docker-desktop/))


#### Setup Instructions

1. Clone the repository after you launch CMD or Terminal:
```
git clone git@github.com:feagi/feagi.git
```

2. Navigate to the Docker directory:
```
cd feagi/docker
```

3. Pull and start the Docker containers:
```
docker compose -f playground.yml pull
docker compose -f playground.yml up
```

1. Access the Playground:
   - Open `http://127.0.0.1:4000/`
   - Click "GENOME" (top right, next to "API")
   - Select "Essential"

2. Continue to the section, "Run without installer (For NRS or Docker)"

### 3. Run without installer (For NRS or Docker)
### Prerequisites
1) python 3.8+
2) CMD (WINDOWS) or Terminal (MAC OR LINUX)
3) Wifi Dongle (To connect Cozmo while your computer stays connected to the internet)
4) Git (https://git-scm.com/downloads for windows. Mac and Linux should have it by default)

### Run the controller
1) `git clone https://github.com/feagi/controllers.git`
2) `cd controllers/embodiments/digital_dream_labs/cozmo_1.0`
3) `python3 -m venv venv` (venv/Scripts/activate for windows)
4) `source venv/bin/activate`
5) Connect your Wi-Fi with Cozmo.
6) Run python using below:
   1. linux/Mac users:
      1. `pip3 install -r requirements.txt`
      2. `python3 controller.py --magic_link "<insert link here>" (replace <insert link here> without removing the quotes in the command).`
   2. Windows users:
      1. `pip install -r requirements.txt`
      2. `python controller.py --magic_link "<insert link here>" (replace <insert link here> without removing the quotes in the command).`
7) You're all set. Next time you want to run the robot, you can simply execute 
`python3 controller.py` or `python controller.py` without following the steps above again.

## 🛠️ Configuration Options

### Command-Line Arguments

```
python controller.py --help
```

| Argument | Description | Default |
|----------|-------------|---------|
| `-h, --help` | Display help message | - |
| `-magic_link, --magic_link` | NRS Studio magic link | - |
| `-ip, --ip` | FEAGI IP address | localhost |
| `-port, --port` | ZMQ port (30000 for Docker, 3000 for localhost) | 3000 |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/feagi/feagi/blob/staging/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](https://github.com/feagi/feagi/blob/staging/LICENSE.txt) file for details.

## 🔗 Links
- [FEAGI Website](https://feagi.org)
- [Documentation](https://docs.feagi.org)
- [GitHub Repository](https://github.com/feagi/feagi)
- [Issue Tracker](https://github.com/feagi/feagi/issues)