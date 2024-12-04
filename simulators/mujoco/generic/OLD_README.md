

Link to humanoid.xml https://github.com/google-deepmind/mujoco/blob/main/model/humanoid/humanoid.xml

# How to Run

## FEAGI (Docker)
1. Clone the repository
2. Change directory to `/feagi/docker/`
3. Ensure you have the latest update: `docker-compose -f playground.yml pull`
4. Run FEAGI with: `docker-compose -f playground.yml up`

## FEAGI Playground & Brain Visualizer
1. With FEAGI running, visit this link: http://localhost:4000/
This should open up the Playground and Brain Visualizer

2. It should say "Loading..." BUT
On the top right select 'GENOMES' > 'ESSENTIAL'
From there you should see the brain visualizer.

3. Spin up the MuJoCo controller
`python3 controller.py --port 30000`

