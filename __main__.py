from server.server_runner import ServerRunner
from server.rcon import RCONConnection
from dotenv import load_dotenv
import os

from time import sleep

# TODO: all of this is debug should be moved into a per-server manager, to make it easier to expand to multi-server setups

# TODO: web interface with uptime, playercount, fully-editable configs, ability to add/remove mods (file sending), create server by sending jars

# TODO: asyncio to manage everything better than current by switching tasks on awaits

load_dotenv()

server_dir = os.getenv("SERVER_DIR")
# TODO: read args from an options file in the server dir (obsidia_ops.txt?)
server_args = ["-server", "-Xms2G", "-Xmx2G"]

server = ServerRunner(server_dir, args=server_args)
server.start()

sleep(40)  # TODO: instead, block until started in server.start()

rcon = RCONConnection("localhost", "adminpassword", 25575)  # NOTE: may not be neccessary since server.write works
rcon.connect()
server.write("say hello")

sleep(5)

rcon.send_command("say cringe")

sleep(5)

rcon.stop()
server.stop()

print(*server.get_full_log())
