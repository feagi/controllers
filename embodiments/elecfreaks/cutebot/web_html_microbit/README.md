# How to Use FEAGI on Microbit

## Requirements for Microbit
* A micro-USB cable
* Micro:bit device
* Computer

## Instructions

1. Connect your micro-USB cable to the micro:bit and your computer.
   ![Connected Microbit](_static/microbit_and_usb.jpg)

2. Visit this [link](https://github.com/feagi/feagi-connector/blob/staging/embodiments/elecfreaks/cutebot/web_html_microbit/microbit-bluetooth-allsensors.hex) and download 
   the HEX file. It should look like this and see the red circle. 

   ![Download HEX](_static/download_hex.png)
3. Drag and drop the file from your Downloads folder to the Micro:bit.
   ![Drag and Drop](_static/arrow_drag_hex.png)

4. You will see the screen go black on the Microbit while the orange or yellow LED on the back of 
   the micro:bit blinks rapidly. Once you see the LCD display showing `1`, you can safely unplug 
   the USB cable.

5. Open the playground and click the `Microbit` blue button. A pop-up window full of device options will appear. Select the one labeled `uBit`. Each micro:bit has its own unique name. For example, mine is `uBit[zovep]`. Yours will have its own name too.
   ![Microbit Connected](_static/microbit_selected.png)
6. **MAC only**: You will see this menu pop up. Due to Apple's security measures, it is required to ask for user permission, so you can simply press 'connect'. See here for an example:
   ![bluetooth_confirm](_static/mac_bluetooth_confirm.png)

7. You should now see the number `2` displayed on the micro:bit's LCD. This indicates a successful connection.


