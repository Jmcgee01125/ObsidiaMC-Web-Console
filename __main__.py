from server.server_runner import ServerRunner
from server.rcon import RCONConnection
from dotenv import load_dotenv
import asyncio
import os

from time import sleep

# TODO: all of this is debug should be moved into a per-server manager, to make it easier to expand to multi-server setups

# TODO: web interface with uptime, playercount, fully-editable configs, ability to add/remove mods (file sending), create server by sending jars

# TODO: asyncio to manage everything better than current by switching tasks on awaits

load_dotenv()

# TODO: iterate over a SERVERS_DIR to get subfolder names of potential servers, then check them to make sure they are servers
server_dir = os.getenv("SERVER_DIR")

# TODO: read args from an options file in the server dir (obsidia_ops.conf?)
server_args = ["-server", "-Xms2G", "-Xmx2G"]


class Listener:
    def __init__(self):
        pass

    async def notify(self, message: str):
        print(message)


server = ServerRunner(server_dir, args=server_args)
listener = Listener()

loop = asyncio.get_event_loop()
loop.run_until_complete(server.add_listener(listener))
loop.run_until_complete(server.start())
loop.close()
