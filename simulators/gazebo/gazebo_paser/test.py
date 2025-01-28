import subprocess
import time
import argparse
import json

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run Gazebo simulation and capture JSON output from a topic.")
parser.add_argument("--sdf", type=str, default="shapes.sdf", help="Path to the SDF file")
args = parser.parse_args()

# Commands to run
server_command = f"gz sim -v 4 {args.sdf} -s -r"
gui_command = "gz sim -v 4 -g"

# Start the server command in one process
server_process = subprocess.Popen(server_command, shell=True)

# Start the GUI command in another process
gui_process = subprocess.Popen(gui_command, shell=True)

# Command to capture JSON output from the specified topic
topic_command = ["gz", "topic", "-e", "-t", "/air_pressure", "--json-output"]


def create_entity():
    """
    Function to create a new entity in Gazebo using the gz service command.
    """
    create_command = [
        "gz", "service", "-s", "/world/free_world/create",
        "--reqtype", "gz.msgs.EntityFactory",
        "--reptype", "gz.msgs.Boolean",
        "--timeout", "300",
        "--req",
        "sdf_filename: 'smart_car.sdf' pose: {position: {z: 1}} name: 'new_name' allow_renaming: true"
    ]

    try:
        # Run the command and capture the output
        result = subprocess.run(create_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("Entity creation output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to create entity:")
        print(e.stderr)
    except FileNotFoundError:
        print("The 'gz' command was not found. Make sure it is installed and available in your PATH.")


def initalize_gyro():
    topic_command = ["gz", "topic", "-e", "-t", "/imu", "--json-output"]
    topic_process = subprocess.Popen(topic_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return topic_process


def read_gyro(gyro_instance):
    return json.loads(gyro_instance.stdout.readline())



    # Capture JSON output in a separate process
    topic_process = subprocess.Popen(topic_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Keep the script running for at least 60 minutes (3600 seconds)
    start_time = time.time()
    # Call the create_entity function before shutting down
    print("Creating a new entity in Gazebo...")
    time.sleep(2)
    create_entity()

    gyro = initalize_gyro()
    output = read_gyro(gyro)




    # Terminate all processes after 60 minutes or interruption
    server_process.terminate()
    gui_process.terminate()
    topic_process.terminate()

    # Wait for processes to cleanly exit
    server_process.wait()
    gui_process.wait()
    topic_process.wait()
