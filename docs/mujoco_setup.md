# Installation
```pip install mujoco```

# Running MuJoCo with Humanoid.xml
```python -m mujoco.viewer --mjcf=.\mujoco\model\humanoid\humanoid.xml```

Make sure you run this command while in the project root directory.

# Example Code
```python
import time

import mujoco
import mujoco.viewer

m = mujoco.MjModel.from_xml_path('/path/to/mjcf.xml')
d = mujoco.MjData(m)

with mujoco.viewer.launch_passive(m, d) as viewer:
  # Close the viewer automatically after 30 wall-seconds.
  start = time.time()
  while viewer.is_running() and time.time() - start < 30:
    step_start = time.time()

    # mj_step can be replaced with code that also evaluates
    # a policy and applies a control signal before stepping the physics.
    mujoco.mj_step(m, d)

    # Example modification of a viewer option: toggle contact points every two seconds.
    with viewer.lock():
      viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = int(d.time % 2)

    # Pick up changes to the physics state, apply perturbations, update options from GUI.
    viewer.sync()

    # Rudimentary time keeping, will drift relative to wall clock.
    time_until_next_step = m.opt.timestep - (time.time() - step_start)
    if time_until_next_step > 0:
      time.sleep(time_until_next_step)
```

# MuJoCo Documentation link:
https://mujoco.readthedocs.io/en/stable/APIreference/APItypes.html#mjmodel

# Troubleshooting
Issue: Black Screen or Glitches in MuJoCo on Windows 11 with AMD GPU

Problem: If the MuJoCo simulation screen appears black, contains graphical glitches, or the interface becomes unresponsive, the issue is likely related to outdated drivers.

Solution:

1. Ensure that your AMD GPU drivers are up to date. You can download the latest drivers directly from the AMD website.
2. Follow the prompts to install the new drivers and restart your computer.
3. Relaunch MuJoCo to verify that the issue has been resolved.

If the problem persists after updating drivers, consider verifying your system’s compatibility with MuJoCo or seeking additional support from the MuJoCo community.

