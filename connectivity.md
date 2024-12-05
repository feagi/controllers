# How to connect FEAGI with any embodiment
## Load Docker:
1. `git clone git@github.com:feagi/feagi.git`
2. `cd ~/feagi/docker`
3. `docker compose -f playground.yml pull`
4. Wait until it's done.
5. `docker compose -f playground.yml up`

## Open Playground Website:
5. Go to [http://127.0.0.1:4000/](http://127.0.0.1:4000/)
6. Click the "GENOME" button on the top right, next to "API."
7. Click "Essential."


# Extra flags
Example command: `python controller.py --help`
```commandline
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