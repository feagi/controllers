# How to connect FEAGI with Mujoco

## Start Mujoco project:
1.	Open a new terminal/cmd and run: `git clone https://github.com/feagi/controllers.git`
2. `cd controllers/simulators/mujoco\humanoid`
3. `python3 -m venv venv` (Windows: `python -m venv venv`)
4. `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
5. `pip3 install -r requirements.txt` (Windows: `pip install -r requirements.txt`)
6. `python3 controller.py` (Windows: `python controller.py`) (If you are using FEAGI in the docker, run this command: `python3 controller.py --port 30000`

## Load Docker:

	1.	git clone git@github.com:feagi/feagi.git
	2.	cd feagi/docker
	3.	docker compose -f playground.yml pull
	4.	Wait until it’s done.
	5.	docker compose -f playground.yml up

## Open Playground Website:

	1.	Go to http://127.0.0.1:4000/
	2.	Click the “GENOME” button on the top right, next to “API.”
	3.	Click “Essential.”


# Extra flags
Example command: `python controller.py --help`
```
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
