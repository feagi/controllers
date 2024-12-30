## Installation

In CMD/Terminal, run:

1. `git clone https://github.com/feagi/controllers.git`
2. `cd controllers/embodiments/neuraville/feagi_trainer`
3. `python3 -m venv venv` (for Windows, `python -m venv venv`)
4. `source venv/bin/activate`
5. Once the venv is activated, run:
   - Linux / Mac:
     1. `pip3 install -r requirements.txt`
     2. `python3 controller.py --magic_link "<insert link here>" (replace <insert link here> without removing the quotes in the command).`
   - Windows:
     1. `pip install -r requirements.txt`
     2. `python controller.py --magic_link "<insert link here>" (replace <insert link here> without removing the quotes in the command).`

At this point, the websocket should be successfully connected. You should see a log of the websocket URL (`wss:// . . .`), with no errors following.

## Requirements:

1. Python version 3.8+
2. Pip version 21+ (?)
3. Magic link (get from /brain-visualizer on NRS under main nav Embodiment -> Magic Link)
4. Command Prompt (CMD) or PowerShell (Windows) / Terminal (Mac or Linux)
5. Git (https://git-scm.com/downloads for Windows. Mac and Linux should have it by default)

### Image Identification

A trainer has been built to send FEAGI images and display the image in the browser with FEAGI's guess of what that image is.

- To use it, after doing the installation steps above, open a separate terminal and run the Flask server with `python utils/flask_server.py`. This will open a separate browser window displaying the current image.
- Any images in feagi_trainer/ will be sent. They should be named x-y-z to match FEAGI's language (such as 0-1-0.jpg).
- To confirm everything is set up, you can manually test FEAGI's ID recognition output:
  1. In the brain visualizer GUI, click the + beside Cortical Areas, click Output, and select ID recognition from the dropdown.
  2. Shift + click anywhere in the ID recognition cortical area and hit space to activate. You should see "FEAGI Guess" update above the image in the separate browser window. It will change depending on the selected voxel.
  3. In the GUI, again click the + beside Cortical Areas, click Output, and select Recognition Location from the dropdown.
  4. Shift-click any two locations in Vision_MR and hit space. You should see a bounding box appear in the current image.



# I don't see any change in behavior.
Do you have the image inside the folder? If not, you will need to grab an image and place it in the folder where the controller is located, or follow the path specified in your configuration.json's `image_path`.

# How do I add more pictures?
Your image's name should be formatted like this: `#-#-#`. For example, `0-0-1`, `1-0-0`, `0-2-3`. They all need to be in an image format such as PNG, JPEG, JPG, or any other static format. You can add them without restarting your trainer, as it is designed to work with dynamic file changes.

# I want the image to stay on for a certain period. How do I do that?
Go to `image_display_duration` in your configuration.json. Update it to the number of seconds you want the image to stay on display.

# I want to pause for a certain period. How do I do that?
Go to `image_gap_duration` in your configuration.json and update it to the number of seconds you want the image to stay off.

# Extra flags
Example command: `python controller.py --help`
```commandline
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

```

# KNOWN ISSUE WITH SSL ERROR ON MAC!

If you see an error like this:
```commandline
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
```

This issue occurs due to Mac's security, which is perfectly acceptable and understandable.

To fix this, follow these steps:

1. Open Finder.
2. Go to Applications (on the left side).
3. Click on Python 3.x.
4. Double-click on `Install Certificates....ommand` file.
5. Wait for it to be done then close the terminal it popped.
6. Re-run your Python script.



# How to Use
TODO: Add text describing the folowing image in detail
<img width="1100" alt="image" src="https://github.com/user-attachments/assets/51ba52cd-ee9c-4560-84da-b979c96206a3">
