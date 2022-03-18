from server.server_manager import ServerManager
from dotenv import load_dotenv
import os


# TODO: web interface with uptime, playercount, editable config, and of course a console


# TODO: iterate over a SERVERS_DIR to get subfolder names of potential servers, then check them to make sure they are servers
load_dotenv()
server_dir = os.getenv("SERVER_DIR")


class Listener:
    def __init__(self):
        pass

    def notify(self, message: str):
        print(message)


listener = Listener()
manager = ServerManager(server_dir)
manager.start_server()
manager.server.add_listener(listener)

while (True):
    command = input().strip()
    manager.server.write(command)
