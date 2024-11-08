# Set up Cozmo with FEAGI
**Important information:** This method works on Windows and Linux only. It's currently not supported 
by Mac due to security reasons. Mac can only work with local FEAGI, use different OS or playground at the moment.

## For Windows users:
1) Get a WiFi dongle and connect it with Cozmo.
2) Download the Cozmo cognitive connector: [here](https://storage.googleapis.com/nrs-artifacts/em-iqgkoadn/controller.zip).
3) Unzip and click the executable file, `controller.exe`
4) You should see a white dialog screen pop up.
5) Click the "Magic Link" button, then paste it into the textbox under the Magic Link.

![image](https://storage.googleapis.com/nrs-artifacts/em-iqgkoadn/pasteyourmagictohere.png)

Note: If you don't want to download anything but prefer to run it from Python, go to the next section below.

## Windows or Linux
Buy a WiFi dongle and connect it to Cozmo. It will connect to the controller once you run it. Be sure to specify the IP address in the controller's configuration to connect to FEAGI (Playground, NRS, or local). Follow the full steps from scratch below:

1) `git clone https://github.com/feagi/controllers.git`
2) `cd controllers/embodiments/digital_dream_labs/cozmo_1.0`
3) `python3 -m venv venv` (venv/Scripts/activate for windows)
4) `source venv/bin/activate`
5) Connect your wifi with Cozmo.
6) Run python using below:
   1. linux users:
      1. `pip3 install -r requirements.txt`
      2. `python3 controller.py --magic_link "<insert link here>" (replace <insert link here> without removing the quotes in the command).`
   2. windows users:
      1. `pip install -r requirements.txt`
      2. `python controller.py --magic_link "<insert link here>" (replace <insert link here> without removing the quotes in the command).`
7) You're all set. Next time you want to run the robot, you can simply execute 
`python3 controller.py` or `python controller.py` without following the steps above again.

# Requirements:
1) python 3.8+
2) Magic link (you can find this from NRS)
3) CMD (WINDOWS) or Terminal (MAC OR LINUX)
4) Wifi Dongle
5) Git (https://git-scm.com/downloads for windows. Mac and Linux should have it by default)

# Tested on cozmo version:
Cozmo 1.0
