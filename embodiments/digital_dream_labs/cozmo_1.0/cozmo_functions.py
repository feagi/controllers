import time
import random
import itertools
import pycozmo
from feagi_connector import PIL_retina as pitina
from feagi_connector import retina as retina



from PIL import Image, ImageDraw
from typing import Optional, Tuple
from pycozmo import protocol_encoder

WIDTH = 128
HEIGHT = 32
MAX_SPEED = 2
NUM_DOTS = 3
DOT_SIZE = 1
LINE_WIDTH = 1

robot = {'accelerator': {'0': []}, "proximity": [], "gyro": {'0': []}, 'servo_head': [], "battery": [],
         'lift_height': []}
camera_data = {"vision": {'0': []}}



def drive_wheels(self, lwheel_speed: float, rwheel_speed: float,
                 lwheel_acc: Optional[float] = 0.0, rwheel_acc: Optional[float] = 0.0,
                 duration: Optional[float] = None) -> None:
    pkt = protocol_encoder.DriveWheels(lwheel_speed_mmps=lwheel_speed,
                                       rwheel_speed_mmps=rwheel_speed,
                                       lwheel_accel_mmps2=0.0, rwheel_accel_mmps2=0.0)
    self.conn.send(pkt)


def stop_motor(self):
    self.stop_all_motors()


class Dot(object):
    def __init__(self, x: int, y: int, vx: int, vy: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy


def display_lines(cli):
    # Generate random dots.
    dots = []
    for i in range(NUM_DOTS):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        vx = random.randint(-MAX_SPEED, MAX_SPEED)
        vy = random.randint(-MAX_SPEED, MAX_SPEED)
        dot = Dot(x, y, vx, vy)
        dots.append(dot)

    timer = pycozmo.util.FPSTimer(pycozmo.robot.FRAME_RATE)
    start = time.time()
    while (time.time() - start) < 20.0:
        # Create a blank image.
        im = Image.new("1", (128, 32), color=0)

        # Draw lines.
        draw = ImageDraw.Draw(im)
        for a, b in itertools.combinations(dots, 2):
            draw.line((a.x, a.y, b.x, b.y), width=LINE_WIDTH, fill=1)

        # Move dots.
        for dot in dots:
            dot.x += dot.vx
            dot.y += dot.vy
            if dot.x <= DOT_SIZE:
                dot.x = DOT_SIZE
                dot.vx = abs(dot.vx)
            elif dot.x >= WIDTH - DOT_SIZE:
                dot.x = WIDTH - DOT_SIZE
                dot.vx = -abs(dot.vx)
            if dot.y <= DOT_SIZE:
                dot.y = DOT_SIZE
                dot.vy = abs(dot.vy)
            elif dot.y >= HEIGHT - DOT_SIZE:
                dot.y = HEIGHT - DOT_SIZE
                dot.vy = -abs(dot.vy)

        cli.display_image(im)

        # Run with 30 FPS.
        timer.sleep()


def on_robot_state(cli, pkt: pycozmo.protocol_encoder.RobotState):
    """
    timestamp: The timestamp associated with the robot state.
    pose_frame_id: The ID of the frame of reference for the robot's pose.
    pose_origin_id: The ID of the origin for the robot's pose.
    pose_x, pose_y, pose_z: The x, y, and z coordinates of the robot's pose.
    pose_angle_rad: The angle of the robot's pose in radians.
    pose_pitch_rad: The pitch angle of the robot's pose in radians.
    lwheel_speed_mmps: Speed of the left wheel in millimeters per second.
    rwheel_speed_mmps: Speed of the right wheel in millimeters per second.
    head_angle_rad: The angle of the robot's head in radians.
    lift_height_mm: The height of the lift in millimeters.
    accel_x, accel_y, accel_z: Acceleration values along the x, y, and z axes.
    gyro_x, gyro_y, gyro_z: Gyroscopic values along the x, y, and z axes.
    battery_voltage: The voltage of the robot's battery.
    status: A status code associated with the robot.
    cliff_data_raw: Raw data related to cliff sensors.
    backpack_touch_sensor_raw: Raw data from the robot's backpack touch sensor.
    curr_path_segment: The ID of the current path segment.
    """
    robot['accelerator']['0'] = [pkt.accel_x, pkt.accel_y, pkt.accel_z]
    robot['proximity'] = pkt.cliff_data_raw
    robot["gyro"]['0'] = [pkt.gyro_x, pkt.gyro_y, pkt.gyro_z]
    robot['servo_head'] = pkt.head_angle_rad
    robot['battery'] = pkt.battery_voltage
    robot['lift_height'] = pkt.lift_height_mm



def on_body_info(cli, pkt: pycozmo.protocol_encoder.BodyInfo):
    print("pkt: ", pkt)


def on_camera_image(cli, image):
    global default_capabilities, previous_frame_data, rgb
    # Obtain the size automatically which will be needed in next line after the next line
    size = pitina.obtain_size(image)
    # Convert into ndarray based on the size it gets
    new_rgb = retina.RGB_list_to_ndarray(image.getdata(), size)
    # update astype to work well with retina and cv2
    raw_frame = retina.update_astype(new_rgb)
    camera_data['vision']['0'] = raw_frame
    time.sleep(0.01)

def vision_initalization(cli):
    cli.add_handler(pycozmo.event.EvtNewRawCameraImage, on_camera_image)


def robot_status(cli):
    cli.add_handler(pycozmo.protocol_encoder.RobotState, on_robot_state)


def move_head(cli, angle, max, min):
    if min <= angle <= max:
        cli.set_head_angle(angle)  # move head
        return True
    else:
        print("reached to limit")
        return False


def lift_arms(cli, angle, max, min, face_selected):
    if min <= angle <= max:
        cli.set_lift_height(angle)  # move head
        return True
    else:
        face_selected.append(4)
        return False