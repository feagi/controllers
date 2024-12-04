import time, random
import copy
import mujoco, mujoco.viewer
import numpy as np
import math
import glfw

#region CONSTANTS
RUNTIME = 6000 # (seconds)
SPEED   = 120 # simulation step speed

#endregion CONSTANTS

#region data.qpos name references
'''
POS INDICIES

abdomen_z   = 7
abdomen_y   = 8
abdomen_x   = 9
hip_x_right   = 10
hip_z_right   = 11
hip_y_right   = 12
knee_right    = 13
ankle_y_right = 14
ankle_x_right = 15
hip_x_left    = 16
hip_z_left    = 17
hip_y_left    = 18
knee_left     = 19
ankle_y_left  = 20
ankle_x_left  = 21
shoulder1_right = 22
shoulder2_right = 23
elbow_right     = 24
shoulder1_left  = 25
shoulder2_left  = 26
elbow_left      = 27

'''

joints = [
  "abdomen_z",
  "abdomen_y",
  "abdomen_x",
  "hip_x_right",
  "hip_z_right",
  "hip_y_right",
  "knee_right",
  "ankle_y_right",
  "ankle_x_right",
  "hip_x_left",
  "hip_z_left",
  "hip_y_left",
  "knee_left",
  "ankle_y_left",
  "ankle_x_left",
  "shoulder1_right",
  "shoulder2_right",
  "elbow_right",
  "shoulder1_left",
  "shoulder2_left", 
  "elbow_left"
]
#endregion data.qpos name references


model = mujoco.MjModel.from_xml_path('./humanoid.xml')
data  = mujoco.MjData(model)

def get_frame(model, data, opt, scene, context, camera_name, loc_x, loc_y, width=640, height=480):
    # Bottom Placement
    # bottom left: loc_x = 0, loc_y = 0
    # bottom middle: loc_x = 0.5*(viewport_width - width), loc_y = 0
    # bottom right: loc_x = viewport_width - width, loc_y = 0
    # Middle Placement
    # middle left: loc_x = 0, loc_y = 0.5*(viewport_width - width)
    # middle: loc_x = 0.5*(viewport_width - width), loc_y = 0.5*(viewport_width - width)
    # middle right: loc_x = viewport_width - width, loc_y = 0.5*(viewport_width - width)
    # Top Placement
    # top left: loc_x = 0, loc_y = viewport_height - height
    # top middle: loc_x = 0.5*(viewport_width - width), loc_y = viewport_height - height
    # top right: loc_x = viewport_width - width, loc_y = viewport_height - height
    
    height = int(height)
    width = int(width)
    # Adding an inset window from a different perspective
    # https://github.com/google-deepmind/mujoco/issues/744#issuecomment-1442221178
    # 1. Create a rectangular viewport in the upper right corner for example.
    offscreen_viewport = mujoco.MjrRect(int(loc_x), int(loc_y), width, height)
    
    # 2. Specify a different camera view by updating the scene with mjv_updateScene.
    # Set the camera to the specified view
    camera_id = mujoco.mj_name2id(model, mj.mjtObj.mjOBJ_CAMERA, camera_name)
    offscreen_cam = mujoco.MjvCamera()
    offscreen_cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
    offscreen_cam.fixedcamid = camera_id

    # Update scene for the off-screen camera
    mujoco.mjv_updateScene(model, data, opt, None, offscreen_cam, mj.mjtCatBit.mjCAT_ALL.value, scene)
    
    # 3.Render the scene in the offscreen buffer with mjr_render.
    frame = np.zeros((height*width*3, 1), dtype=np.uint8)  # Placeholder for pixel data
    mujoco.mjr_render(offscreen_viewport, scene, context)
    
    # 4. Read the pixels with mjr_readPixels.
    mujoco.mjr_readPixels(frame, None, offscreen_viewport, context)
    
    # 5. Call mjr_drawPixels using the rectangular viewport you created in step 1.
    # glClear(GL_DEPTH_BUFFER_BIT)  # allows rendering over geometries
    # mj.mjr_drawPixels(frame, None, offscreen_viewport, context)
    
    return frame, offscreen_viewport

def check_keypos(data, model):
    #check if current data.qpos matches a model.keypos
    # Loop over each keyframe
    for i in range(model.nkey):
        # Compare with current data.qpos using np.allclose
        if np.allclose(data.qpos, model.key_qpos[i], atol=1e-6):
            #print(f"Current qpos matches keyframe {i}")
            return i
    else:
        return -1

#Position number can be 1-5
def start_keypos(data, model, position_number):
    data.qpos = model.key_qpos[position_number] 
    #mujoco.mj_step(model, data) # single step to make sure data renders
    return model.key_qpos[position_number]

#Better balance attempt using actual physics 
def balance_attempt_advanced(data, desired_qpos, desired_qvel):
    # Control gains
    Kp = np.array([100] * len(desired_qpos))  # Proportional gains
    Kd = np.array([10] * len(desired_qpos))   # Derivative gains
    # Current joint positions and velocities
    current_qpos = data.qpos[7:]
    current_qvel = data.qvel[6:]  # Exclude global velocities
    # Compute errors
    qpos_error = desired_qpos - current_qpos
    qvel_error = desired_qvel - current_qvel
    # PD control law
    control_torques = Kp * qpos_error + Kd * qvel_error
    # Apply control torques within actuator limits
    data.ctrl[:] = np.clip(control_torques, model.actuator_ctrlrange[:, 0], model.actuator_ctrlrange[:, 1])

#This does not work lol it stresses him out
def balance_attempt_basic(data, start_pos): 
    current_pos = data.qpos[7:]
    start_pos = start_pos[7:]
    for i, pos in enumerate(current_pos):
            if (pos < start_pos[i]):
                data.ctrl[i] += .01
            elif (pos > start_pos[i]):
                data.ctrl[i] -= .01

#Pauses the model until control is applied somewhere.
def pause_until_move(data, start_pos):
    for i, ctrl in enumerate(data.ctrl):
        if (ctrl != 0): #if we change the ctrl we "free" the limb
            return False # we are no longer paused
    
    data.qpos[:] = start_pos[:]
    return True

# Since we're ignoring the physics behind everything, moving multiple joints will create overflow in data.qacc 
# which briefly resets the model. Tried to fix this but solution is not simple. I notice the qpos positions go outside their bounds 
# when it happens so maybe hard bounds along with resetting the respective data.qvel and data.qacc values could fix it (just an idea) 
def pause_standing_unstable(data, start_pos, free_joints):
    for i, ctrl in enumerate(data.ctrl):
        if (data.ctrl[i] == 0):
            free_joints[i]=0
        if (ctrl != 0): #if we change the ctrl we "free" the limb
            free_joints[i] = -1 #find the limb to free and mark it
    for i, pos in enumerate(data.qpos[:7]):
            data.qpos[i] = start_pos[i]
            pass
    for i, pos in enumerate(data.qpos[7:]):
        if (free_joints[i] != -1):
            data.qpos[i+7] = start_pos[i+7]
    return free_joints      

def main():
  
  
  mujoco.mj_resetDataKeyframe(model, data, 4)

  """ # Initialize GLFW
  if not glfw.init():
    raise Exception("Failed to initialize GLFW")
  # Create a hidden GLFW window
  glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
  window = glfw.create_window(100, 100, "Hidden Window", None, None)
  if not window:
    glfw.terminate()
    raise Exception("Failed to create GLFW window") """
  
  with mujoco.viewer.launch_passive(model, data) as viewer:
     start_time = time.time()
     free_joints = [0] * 21 #keep track of which joints to lock and free (for unstable pause method)
     start_pos = copy.copy(data.qpos)
     paused = True

     camera_name = "egocentric"
     camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
     camera = mujoco.MjvCamera()
     camera.fixedcamid = camera_id
     camera.type = mujoco.mjtCamera.mjCAMERA_FIXED
     mujoco.mjv_defaultFreeCamera(model, camera)
     
     while viewer.is_running() and time.time() - start_time < RUNTIME:
        step_start = time.time()
        """ for i, cam_pos in enumerate(data.cam_xpos):
            print(f"Cam position {i}: {cam_pos}")
        for i, cam_mat in enumerate(data.cam_xmat):
            print(f"Cam orientation {i}: {cam_mat}") """
        #context = mujoco.MjrContext()
        #context = mujoco.MjrContext(model, 50)
        #scene = mujoco.MjvScene(model, maxgeom=10000)
        #viewport = mujoco.MjrRect(0, 0, 100, 100)
        """ context = mujoco.MjrContext(model, mujoco.mjtFontScale.mjFONTSCALE_100)
        scene = mujoco.MjvScene(model, maxgeom=10000)
        viewport = mujoco.MjrRect(0, 0, 100, 100)
        #mujoco.mjr_render(viewport, scene, context)
        upside_down_image = np.empty((100, 100, 3), dtype=np.uint8)
        upside_down_depth = np.empty((100, 100, 1))
        #mujoco.mjr_readPixels(rgb=upside_down_image, depth=upside_down_depth, viewport=viewport, con=context)
 """
         # Iterate over contacts
        for i in range(data.ncon):
            contact = data.contact[i]  # Access the contact object
            # Extract contact details
            dist = contact.dist  # Penetration distance
            geom1 = contact.geom1  # ID of the first geometry
            geom2 = contact.geom2  # ID of the second geometry
            pos = contact.pos  # Contact position, size 3 array. x,y,z
            frame = contact.frame  # ID of the first geometry
            #print(contact)
            # Print contact information
            #print(f"Contact {i}: pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}), dist={dist}")
            #print(f"Contact {i}: pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}), frame={frame}")
            #print(contact)
        ### APPLY FORCE TO MODEL HERE ###
       

        # Loop through all active contacts
        for i in range(data.ncon):
            contact = data.contact[i]  # Access each contact
            force = np.zeros(6)  # Allocate array to hold the contact force data

            # Retrieve the contact force for this contact
            mujoco.mj_contactForce(model, data, i, force)

            # Print contact force data
            print(f"Contact between geom {contact.geom1} and geom {contact.geom2}")
            print(f"Normal force: {force[:3]}")
            #print(i)
            #print(f"Tangent forces: {force[3:]}")

        """ if (np.array_equal(data.qpos, zero_pos)): #means we're not in the starting position (hit delete to reset sim)
            start_standing(data) """
    
        #check if key pos was manually changed
        if check_keypos(data, model) >= 0:
            #print("hello, ", check_keypos(data, model))
            #start_pos = start_keypos(data, model, check_keypos(data, model)) #if it was, update the start_pos
            pass

        ### PAUSING/BALANCE ### Only try one at a time.
        #balance_attempt_advanced(data, start_pos[7:], np.zeros_like(start_pos[7:])) #better attempt at balancing
        #if paused:
        #paused = pause_until_move(data, start_pos) #pauses the simulation until control is applied. Will lock positions if d.ctrl[:]==0 
        #free_joints = pause_standing_unstable(data, start_pos, free_joints) #Unstable. Mainly for testing. lock the model but move joints freely. Helpful for seeing what controls actually do
        #balance_attempt_basic(data, start_pos) #Bad. tries to use ctrl to balance instead of hardcoding qpos.
        ###############

        #print("proximity data:" , data.sensordata) #test to print proximity data

        # steps the simulation forward 'tick' -- Only step if we aren't paused because it breaks the physics
        #if not paused:
        mujoco.mj_step(model, data)

        # Pick up changes to the physics state, apply perturbations, update options from GUI.
        viewer.sync()

        # Tick Speed # 
        time_until_next_step = (1/SPEED) - (time.time() - step_start)
        if time_until_next_step > 0:
            time.sleep(time_until_next_step)


if __name__ == "__main__":
  main()
