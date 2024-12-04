import time
import mujoco, mujoco.viewer

SPEED   = 120 # simulation step speed

model = mujoco.MjModel.from_xml_path('./humanoid.xml')
data  = mujoco.MjData(model)

def main():
  mujoco.mj_resetDataKeyframe(model, data, 4)
  
  with mujoco.viewer.launch_passive(model, data) as viewer:

     while viewer.is_running():
        step_start = time.time()
 
        print("rangefinder data:" , data.sensordata[7:]) #prints all sensor data, ignore the first 3 because that's proximity

        mujoco.mj_step(model, data)

        # Pick up changes to the physics state, apply perturbations, update options from GUI.
        viewer.sync()

        # Tick Speed # 
        time_until_next_step = (1/SPEED) - (time.time() - step_start)
        if time_until_next_step > 0:
            time.sleep(time_until_next_step)


if __name__ == "__main__":
  main()
