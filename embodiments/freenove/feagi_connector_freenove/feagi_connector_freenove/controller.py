import sys
import cv2
import time
import asyncio
import argparse
import traceback
import threading
import subprocess
from time import sleep
import RPi.GPIO as GPIO
from collections import deque
from feagi_connector_freenove.ADC import *
from feagi_connector_freenove.Led import *
from feagi_connector import retina as retina
from feagi_connector import sensors as sensors
from feagi_connector import pns_gateway as pns
from feagi_connector import actuators as actuators
from feagi_connector_freenove.PCA9685 import PCA9685
from feagi_connector import feagi_interface as FEAGI
from feagi_connector_freenove.version import __version__

ir_data = deque()
ultrasonic_data = deque()
feagi_dict = deque()
feagi_settings = dict()
raw_frame_internal = {'0': []}


class LED:
    def __init__(self):
        self.led = Led()

    def LED_on(self, led_ID, Red_Intensity, Blue_Intensity, Green_intensity):
        """
        Parameters
        ----------
        led_ID: This is the ID of leds. It can be from 1 to 8
        Red_Intensity: 1 to 255, from dimmest to brightest
        Blue_Intensity: 1 to 255, from dimmest to brightest
        Green_intensity: 1 to 255, from dimmest to brightest
        -------
        """
        try:
            self.led.ledIndex(led_ID, Red_Intensity, Blue_Intensity, Green_intensity)
        except KeyboardInterrupt:
            self.led.colorWipe(led.strip, Color(0, 0, 0))  ##This is to turn all leds off/

    def test_led(self):
        """
        This is to test all leds and do several different leds.
        """
        try:
            self.led.ledIndex(0x01, 255, 0, 0)  # Red
            self.led.ledIndex(0x02, 255, 125, 0)  # orange
            self.led.ledIndex(0x04, 255, 255, 0)  # yellow
            self.led.ledIndex(0x08, 0, 255, 0)  # green
            self.led.ledIndex(0x10, 0, 255, 255)  # cyan-blue
            self.led.ledIndex(0x20, 0, 0, 255)  # blue
            self.led.ledIndex(0x40, 128, 0, 128)  # purple
            self.led.ledIndex(0x80, 255, 255, 255)  # white'''
            print("The LED has been lit, the color is red orange yellow green cyan-blue blue white")
            # time.sleep(3)  # wait 3s
            self.led.colorWipe("", Color(0, 0, 0))  # turn off the light
            print("\nEnd of program")
        except KeyboardInterrupt:
            self.led.colorWipe("", Color(0, 0, 0))  # turn off the light
            print("\nEnd of program")

    def leds_off(self):
        self.led.colorWipe("", Color(0, 0, 0))  # This is to turn all leds off/


class Servo:
    """
    Functions: head_UP_DOWN and head_RIGHT_LEFT only. Other functions are just a support and defined system for Servo
    class to work with functions.
    """

    def __init__(self):
        self.PwmServo = PCA9685(0x40, debug=True)
        self.PwmServo.setPWMFreq(50)
        self.device_position = float()
        self.servo_ranges = {i: [10, 170] for i in range(13)}
        self.servo_ranges[1] = [76, 140]

    def setServoPwm(self, channel, angle, error=10):
        angle = float(angle)
        if channel == '0':
            self.PwmServo.setServoPulse(8, 2500 - float((angle + error) / 0.09))
        elif channel == '1':
            self.PwmServo.setServoPulse(9, 500 + float((angle + error) / 0.09))
        elif channel == '2':
            self.PwmServo.setServoPulse(10, 500 + float((angle + error) / 0.09))
        elif channel == '3':
            self.PwmServo.setServoPulse(11, 500 + float((angle + error) / 0.09))
        elif channel == '4':
            self.PwmServo.setServoPulse(12, 500 + float((angle + error) / 0.09))
        elif channel == '5':
            self.PwmServo.setServoPulse(13, 500 + float((angle + error) / 0.09))
        elif channel == '6':
            self.PwmServo.setServoPulse(14, 500 + float((angle + error) / 0.09))
        elif channel == '7':
            self.PwmServo.setServoPulse(15, 500 + float((angle + error) / 0.09))

    def set_default_position(self, capabilities):
        try:
            # Setting the initial position for the servo
            for servo_id in capabilities['output']['servo']:
                if not capabilities['output']['servo'][servo_id]['disabled']:
                    position = actuators.servo_keep_boundaries(capabilities['output']['servo'][servo_id]['default_value'],
                                                               capabilities['output']['servo'][servo_id]['max_value'],
                                                               capabilities['output']['servo'][servo_id]['min_value'])

                    self.setServoPwm(servo_id, position)
            # servo_0_initial_position = 90
            # runtime_data['servo_status'][0] = servo_0_initial_position
            # self.setServoPwm(str(0), runtime_data['servo_status'][0])
            # print("Servo 0 was moved to its initial position")
            #
            # servo_1_initial_position = 90
            # runtime_data['servo_status'][1] = servo_1_initial_position
            # self.setServoPwm(str(1), runtime_data['servo_status'][0])
        except Exception as e:
            print("Error while setting initial position for the servo:", e)

    def move(self, device_index, power):
        try:
            # if feagi_device_id > 2 * capabilities['servo']['count']:
            #     print("Warning! Number of servo channels from FEAGI exceed available Motor count!")
            # # Translate feagi_motor_id to motor backward and forward motion to individual motors
            # device_index = feagi_device_id // 2
            # if feagi_device_id % 2 == 1:
            #     power *= 1
            # else:
            #     power *= -1
            # if device_index not in runtime_data['servo_status']:
            #     runtime_data['servo_status'][device_index] = device_index
            #
            # device_current_position = runtime_data['servo_status'][device_index]
            # self.device_position = float((power * feagi_settings['feagi_burst_speed'] /
            #                               capabilities["servo"][
            #                                   "power_amount"]) + device_current_position)
            #
            # self.device_position = self.keep_boundaries(device_id=device_index,
            #                                             current_position=self.device_position)

            # runtime_data['servo_status'][device_index] = self.device_position
            # print("device index, position, power = ", device_index, self.device_position, power)
            # self.servo_node[device_index].publish(self.device_position)
            self.setServoPwm(str(device_index), power)
        except Exception:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)

    def keep_boundaries(self, device_id, current_position):
        """
        Prevent Servo position to go beyond range
        """
        if current_position > self.servo_ranges[device_id][1]:
            adjusted_position = float(self.servo_ranges[device_id][1])
        elif current_position < self.servo_ranges[device_id][0]:
            adjusted_position = float(self.servo_ranges[device_id][0])
        else:
            adjusted_position = float(current_position)
        return adjusted_position

    @staticmethod
    def servo_id_converter(servo_id):
        """
        This will convert from godot to motor's id. Let's say, you have 4x10 (width x depth from static_genome).
        So, you click 2 (actually 4 but 2 for one servo on backward/forward) to go forward. It will be like this:
        o_sper': {'1-0-9': 1, '3-0-9': 1}
        which is 1,3. So this code will convert from 1,3 to 0,1 on motor id.

        Since 0-1 is servo 0, 2-3 is servo 1 and so on. In this case, 0 and 2 is for forward and 1 and 3 is for backward
        """
        if servo_id <= 1:
            return 0
        elif servo_id <= 3:
            return 1
        else:
            print("Input has been refused. Please put motor ID.")

    @staticmethod
    def power_convert(motor_id, power):
        if motor_id % 2 == 0:
            return -1 * power
        else:
            return abs(power)

    @staticmethod
    def motor_converter(motor_id):
        """
        This will convert from godot to motor's id. Let's say, you have 8x10 (width x depth from
        static_genome). So, you click 4 to go forward. It will be like this: o_mper': {'1-0-9':
        1, '5-0-9': 1, '3-0-9': 1, '7-0-9': 1} which is 1,3,5,7. So this code will convert from
        1,3,5,7 to 0,1,2,3 on motor id.

        Since 0-1 is motor 1, 2-3 is motor 2 and so on. In this case, 0 is for forward and 1 is
        for backward.
        """
        # motor_total = capabilities['motor']['count'] #be sure to update your motor total in
        # configuration.json increment = 0 for motor in range(motor_total): if motor_id <= motor +
        # 1: print("motor_id: ", motor_id) increment += 1 return increment
        if motor_id <= 1:
            return 0
        elif motor_id <= 3:
            return 3
        elif motor_id <= 5:
            return 1
        elif motor_id <= 7:
            return 2
        else:
            print("Input has been refused. Please put motor ID.")


class Motor:
    def __init__(self):
        self.pwm = PCA9685(0x40, debug=True)
        self.pwm.setPWMFreq(50)
        self.motor_channels = [[0, 1], [3, 2], [4, 5], [6, 7]]

    @staticmethod
    def duty_range(duty1, duty2, duty3, duty4):
        if duty1 > 4095:
            duty1 = 4095
        elif duty1 < -4095:
            duty1 = -4095

        if duty2 > 4095:
            duty2 = 4095
        elif duty2 < -4095:
            duty2 = -4095

        if duty3 > 4095:
            duty3 = 4095
        elif duty3 < -4095:
            duty3 = -4095

        if duty4 > 4095:
            duty4 = 4095
        elif duty4 < -4095:
            duty4 = -4095
        return duty1, duty2, duty3, duty4

    def left_Upper_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(0, 0)
            self.pwm.setMotorPwm(1, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(1, 0)
            self.pwm.setMotorPwm(0, abs(duty))
        else:
            self.pwm.setMotorPwm(0, 4095)
            self.pwm.setMotorPwm(1, 4095)

    def left_Lower_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(3, 0)
            self.pwm.setMotorPwm(2, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(2, 0)
            self.pwm.setMotorPwm(3, abs(duty))
        else:
            self.pwm.setMotorPwm(2, 4095)
            self.pwm.setMotorPwm(3, 4095)

    def right_Upper_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(6, 0)
            self.pwm.setMotorPwm(7, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(7, 0)
            self.pwm.setMotorPwm(6, abs(duty))
        else:
            self.pwm.setMotorPwm(6, 4095)
            self.pwm.setMotorPwm(7, 4095)

    def right_Lower_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(4, 0)
            self.pwm.setMotorPwm(5, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(5, 0)
            self.pwm.setMotorPwm(4, abs(duty))
        else:
            self.pwm.setMotorPwm(4, 4095)
            self.pwm.setMotorPwm(5, 4095)

    def move(self, motor_index, speed):
        if speed > 0:
            # print("from move(): ", motor_index)
            self.pwm.setMotorPwm(self.motor_channels[motor_index][0], 0)
            self.pwm.setMotorPwm(self.motor_channels[motor_index][1], speed)
        elif speed < 0:
            self.pwm.setMotorPwm(self.motor_channels[motor_index][1], 0)
            self.pwm.setMotorPwm(self.motor_channels[motor_index][0], abs(speed))
        elif speed == 0:
            self.pwm.setMotorPwm(self.motor_channels[motor_index][0], 0)
            self.pwm.setMotorPwm(self.motor_channels[motor_index][1], 0)

    def setMotorModel(self, duty1, duty2, duty3, duty4):
        duty1, duty2, duty3, duty4 = self.duty_range(duty1, duty2, duty3, duty4)
        self.left_Upper_Wheel(duty1)
        self.left_Lower_Wheel(duty2)
        self.right_Upper_Wheel(duty3)
        self.right_Lower_Wheel(duty4)

    def stop(self):
        self.setMotorModel(0, 0, 0, 0)

    @staticmethod
    def motor_converter(motor_id):
        """
        This will convert from godot to motor's id. Let's say, you have 8x10 (width x depth from static_genome).
        So, you click 4 to go forward. It will be like this:
        o_mper': {'1-0-9': 1, '5-0-9': 1, '3-0-9': 1, '7-0-9': 1}
        which is 1,3,5,7. So this code will convert from 1,3,5,7 to 0,1,2,3 on motor id.

        Since 0-1 is motor 1, 2-3 is motor 2 and so on. In this case, 0 is for forward and 1 is for backward.
        """
        # motor_total = capabilities['motor']['count'] #be sure to update your motor total in
        # configuration.json increment = 0 for motor in range(motor_total): if motor_id <= motor +
        # 1: print("motor_id: ", motor_id) increment += 1 return increment
        if motor_id == 0:
            return 0
        elif motor_id == 1:
            return 3
        elif motor_id == 2:
            return 1
        elif motor_id == 3:
            return 2
        else:
            print("Input has been refused. Please put motor ID.")

    @staticmethod
    def power_convert(motor_id, power):
        if motor_id % 2 == 0:
            return -1 * power
        else:
            return abs(power)


class IR:
    def __init__(self):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

    def read(self):
        gpio_state = []
        ir_sensors = [self.IR01, self.IR02, self.IR03]
        for idx, sensor in enumerate(ir_sensors):
            if GPIO.input(sensor):
                gpio_state.append(idx)
        return gpio_state


class Ultrasonic:
    def __init__(self):
        GPIO.setwarnings(False)
        self.trigger_pin = 27
        self.echo_pin = 22
        self.MAX_DISTANCE = 300  # define the maximum measuring distance, unit: cm
        self.timeOut = self.MAX_DISTANCE * 60  # calculate timeout according to the maximum measuring distance
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def pulseIn(self, pin, level, timeOut):  # obtain pulse time of a pin under timeOut
        t0 = time.time()
        while (GPIO.input(pin) != level):
            if ((time.time() - t0) > timeOut * 0.000001):
                return 0;
        t0 = time.time()
        while (GPIO.input(pin) == level):
            if ((time.time() - t0) > timeOut * 0.000001):
                return 0;
        pulseTime = (time.time() - t0) * 1000000
        return pulseTime

    def get_distance(self):  # get the measurement results of ultrasonic module,with unit: cm
        distance_cm = [0, 0, 0, 0, 0]
        for i in range(5):
            GPIO.output(self.trigger_pin, GPIO.HIGH)  # make trigger_pin output 10us HIGH level
            time.sleep(0.00001)  # 10us
            GPIO.output(self.trigger_pin, GPIO.LOW)  # make trigger_pin output LOW level
            pingTime = self.pulseIn(self.echo_pin, GPIO.HIGH, self.timeOut)  # read plus time of echo_pin
            distance_cm[i] = pingTime * 340.0 / 2.0 / 10000.0  # calculate distance with sound speed 340m/s
        distance_cm = sorted(distance_cm)
        return int(distance_cm[2])/100


class Battery:
    def battery_total(self):
        adc = Adc()
        Power = adc.recvADC(2) * 3
        return Power


def process_video(default_capabilities, cam):
    while True:
        if default_capabilities['input']['camera']['0']['disabled'] is not True:
            ret, raw_frame = cam.read()
            raw_frame_internal['0'] = raw_frame
        sleep(0.001)


def vision_calculation(default_capabilities, previous_frame_data, rgb, capabilities):
    while True:
        if raw_frame_internal['0'] != []:
            raw_frame = raw_frame_internal['0']
            if len(default_capabilities['input']['camera']['0']['blink']) > 0:
                raw_frame = default_capabilities['input']['camera']['0']['blink']
            # Post image into vision
            previous_frame_data, rgb, default_capabilities = \
                retina.process_visual_stimuli(raw_frame, default_capabilities,
                                              previous_frame_data,
                                              rgb, capabilities)
            default_capabilities['input']['camera']['0']['blink'] = []
            # Wrapping camera data into a frame for FEAGI
        sleep(0.001)


def action(obtained_data, led_tracking_list, led,capabilities, motor, servo):
    recieve_motor_data = actuators.get_motor_data(obtained_data)
    recieve_servo_data = actuators.get_servo_data(obtained_data)
    recieve_servo_position_data = actuators.get_servo_position_data(obtained_data)

    if recieve_servo_position_data:
        for real_id in recieve_servo_position_data:
            servo_number = real_id
            new_power = recieve_servo_position_data[real_id]
            servo.move(servo_number, new_power)

    if recieve_servo_data:
        for real_id in recieve_servo_data:  # example output: {0: 100, 2: 100}
            servo_number = real_id
            new_power = recieve_servo_data[real_id]
            servo.move(servo_number, new_power)



    if recieve_motor_data:
        for motor_id in recieve_motor_data:
            motor.move(motor_id, -1 * recieve_motor_data[motor_id]) # add negative 1 to convert forward into positive


    recieved_led_data = actuators.get_led_data(obtained_data)
    if recieved_led_data:
        for data_point in recieved_led_data:
            led.LED_on(data_point, int((recieved_led_data[data_point] / 100) * 255), 0, 0)
            led_tracking_list[data_point] = True
    else:
        if led_tracking_list:
            for x in led_tracking_list:
                led.LED_on(x, 0, 0, 0)
            led_tracking_list.clear()


async def read_background(feagi_settings):
    ir = IR()
    while True:
        if len(ir_data) > 2:
            ir_data.popleft()
        ir_data.append(ir.read())
        sleep(feagi_settings['feagi_burst_speed'])


def start_IR(feagi_settings):
    asyncio.run(read_background(feagi_settings))


async def read_ultrasonic(feagi_settings):
    ultrasonic = Ultrasonic()
    while True:
        if len(ultrasonic_data) > 2:
            ultrasonic_data.popleft()
        ultrasonic_data.append(ultrasonic.get_distance())
        sleep(feagi_settings['feagi_burst_speed'])



def start_ultrasonic(feagi_settings):
    asyncio.run(read_ultrasonic(feagi_settings))


def check_the_flag(current_path):
    parser = argparse.ArgumentParser(description="Load freenove")
    parser.add_argument('-setup', '--setup', help='first time setup only', required=False)
    args, remaining_args = parser.parse_known_args()

    if args.setup:
        if args.setup.lower() == 'true':
            new_path = current_path[0] + "/setup.sh " + current_path[0]
            subprocess.run([new_path, "arguments"], shell=True)

    available_list_from_feagi_connector = FEAGI.get_flag_list()
    cleaned_args = []
    skip_next = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if arg in available_list_from_feagi_connector:
            cleaned_args.append(arg)
            if i + 1 < len(sys.argv[1:]) and not sys.argv[1:][i + 1].startswith("-"):
                cleaned_args.append(sys.argv[1:][i + 1])
                skip_next = True

    sys.argv = [sys.argv[0]] + cleaned_args


def main(current_path):
    GPIO.cleanup()
    check_the_flag(current_path)
    config = FEAGI.build_up_from_configuration(str(current_path[0]) + '/')
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    capabilities = config['capabilities'].copy()


    # # FEAGI REACHABLE CHECKER # #
    print("retrying...")
    print("Waiting on FEAGI...")
    # while not feagi_flag:
    #     print("ip: ", os.environ.get('FEAGI_HOST_INTERNAL', feagi_settings["feagi_host"]))
    #     print("here: ", int(os.environ.get('FEAGI_OPU_PORT', "30000")))
    #     feagi_flag = FEAGI.is_FEAGI_reachable(
    #         os.environ.get('FEAGI_HOST_INTERNAL', feagi_settings["feagi_host"]),
    #         int(os.environ.get('FEAGI_OPU_PORT', "30000")))
    #     sleep(2)

    runtime_data = {
        "current_burst_id": 0,
        "feagi_state": None,
        "cortical_list": (),
        "battery_charge_level": 1,
        "host_network": {},
        'motor_status': {},
        'servo_status': {}
    }
    # # FEAGI REACHABLE CHECKER COMPLETED # #

    # # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # - - - - - - - - - - - - - - - - - - #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        FEAGI.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # --- Initializer section ---
    motor = Motor()
    actuators.start_motors(capabilities)  # initialize motors for you.
    servo = Servo()
    actuators.start_servos(capabilities)
    led = LED()
    battery = Battery()  # Commented out, not currently in use

    # --- Variables ---
    rgb = dict()
    rgb['camera'] = dict()

    # --- Data Containers ---
    # Status for data points
    led_tracking_list = {}
    previous_frame_data = {}
    message_to_feagi = {}

    threading.Thread(target=start_IR, args=(feagi_settings,), daemon=True).start()
    threading.Thread(target=start_ultrasonic, args=(feagi_settings,), daemon=True).start()
    # ultrasonic = Ultrasonic()
    motor.stop()
    cam = cv2.VideoCapture(0)  # you need to do sudo rpi-update to be able to use this
    servo.set_default_position(capabilities)

    default_capabilities = {}  # It will be generated in process_visual_stimuli. See the
    # overwrite manual
    camera_data = {"vision": {}}
    default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)
    threading.Thread(target=process_video, args=(default_capabilities, cam), daemon=True).start()
    # threading.Thread(target=vision_calculation, args=(default_capabilities, previous_frame_data,
    #                                                   rgb, capabilities), daemon=True).start()

    # router.websocket_client_initalize('192.168.50.218', '9053')
    threading.Thread(target=retina.vision_progress,
                     args=(default_capabilities, feagi_settings, camera_data,), daemon=True).start()
    # threading.Thread(target=router.websocket_recieve, daemon=True).start()
    while True:
        try:
            message_from_feagi = pns.message_from_feagi
            if message_from_feagi and message_from_feagi != None:
                # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
                obtained_signals = pns.obtain_opu_data(message_from_feagi)
                action(obtained_signals, led_tracking_list, led,capabilities, motor, servo)

            if raw_frame_internal['0'] is not []:
                raw_frame = raw_frame_internal['0']
                if len(default_capabilities['input']['camera']['0']['blink']) > 0:
                    raw_frame = default_capabilities['input']['camera']['0']['blink']
                # Post image into vision
                previous_frame_data, rgb, default_capabilities = \
                    retina.process_visual_stimuli(raw_frame, default_capabilities,
                                                  previous_frame_data,
                                                  rgb, capabilities)
                default_capabilities['input']['camera']['0']['blink'] = []
                # Wrapping camera data into a frame for FEAGI
                if rgb:
                    message_to_feagi = pns.generate_feagi_data(rgb, message_to_feagi)


            # add IR data into feagi data
            ir_list = ir_data[0] if ir_data else []
            message_to_feagi = sensors.convert_ir_to_ipu_data(ir_list, len(capabilities['input']['infrared']), message_to_feagi)
            # add ultrasonic data into feagi data
            if ultrasonic_data:
                ultrasonic_list = ultrasonic_data[0]
            else:
                ultrasonic_list = 0
            message_to_feagi = sensors.create_data_for_feagi(sensor='proximity', capabilities=capabilities,
                                                             message_to_feagi=message_to_feagi,
                                                             current_data=ultrasonic_list,
                                                             measure_enable=True)
            # add battery data into feagi data
            current_battery = battery.battery_total()
            message_to_feagi = sensors.create_data_for_feagi(sensor='battery', capabilities=capabilities,
                                                             message_to_feagi=message_to_feagi,
                                                             current_data=current_battery)


            sleep(feagi_settings['feagi_burst_speed'])  # bottleneck
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()

            if rgb:
                for i in rgb['camera']:
                    rgb['camera'][i].clear()
        except KeyboardInterrupt as ke:  # Keyboard error
            motor.stop()
            cam.release()
            print("ke: ", ke)
            led.leds_off()
            break
        except Exception as e:
            print("ERROR: ", e)
            traceback.print_exc()
            motor.stop()
            led.leds_off()
            break