"""PR2 Webots Python Controller"""

from controller import Robot, Motor, Camera

# Initialize robot
robot = Robot()

# Get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# Get PR2 motors for the right arm
right_arm_motors = {
    "shoulder_pan": robot.getDevice("r_shoulder_pan_joint"),
    "shoulder_lift": robot.getDevice("r_shoulder_lift_joint"),
    "upper_arm_roll": robot.getDevice("r_upper_arm_roll_joint"),
    "elbow_lift": robot.getDevice("r_elbow_flex_joint"),
    "wrist_roll": robot.getDevice("r_wrist_roll_joint")
}

# Get PR2 motors for the left arm
left_arm_motors = {
    "shoulder_pan": robot.getDevice("l_shoulder_pan_joint"),
    "shoulder_lift": robot.getDevice("l_shoulder_lift_joint"),
    "upper_arm_roll": robot.getDevice("l_upper_arm_roll_joint"),
    "elbow_lift": robot.getDevice("l_elbow_flex_joint"),
    "wrist_roll": robot.getDevice("l_wrist_roll_joint")
}

# Enable the PR2 camera
camera = robot.getDevice("high_def_sensor")
camera.enable(timestep)

def move_arm(arm, positions):
    """
    Move the PR2 arm to a specified position.
    :param arm: "left" or "right"
    :param positions: Dict with joint angles {joint_name: angle}
    """
    if arm == "right":
        motors = right_arm_motors
    elif arm == "left":
        motors = left_arm_motors
    else:
        print("Invalid arm name. Use 'left' or 'right'.")
        return
    for joint, angle in positions.items():
        if joint in motors:
            motors[joint].setPosition(angle)
        else:
            print(f"Invalid joint name: {joint}")

def print_camera_data():
    """Retrieve and print RGB camera data."""
    image = camera.getImageArray()
    width = camera.getWidth()
    height = camera.getHeight()

    if image:
        for y in range(height):
            row_pixels = []
            for x in range(width):
                red = image[x][y][0]
                green = image[x][y][1]
                blue = image[x][y][2]
                row_pixels.append(f"({x},{y}): R={red} G={green} B={blue}")
            print("".join(row_pixels))

# Move right arm a bit
move_arm("right", {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.5,
        "upper_arm_roll": 0.0,
        "elbow_lift": -0.5,
        "wrist_roll": 0.0
    })
# Main loop
while robot.step(timestep) != -1:
    print_camera_data() # Keep outputing the camera data