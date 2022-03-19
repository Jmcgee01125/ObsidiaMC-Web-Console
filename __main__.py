from server.server_manager import ServerManager
from server.server import ServerListener
from dotenv import load_dotenv
import threading
import os


# TODO: web interface (web2py?) with uptime, playercount + names (mctools?), editable config, and of course a console

# TODO: password challenge based on password set in master config, which should have other options (meta-server and UI stuff like colors)


# TODO: iterate over a SERVERS_DIR to get subfolder names of potential servers, then check them to make sure they are servers
load_dotenv()
server_dir = os.getenv("SERVER_DIR")


class DebugPrintListener:
    def __init__(self, server_listener: ServerListener):
        self._server_listener = server_listener

    def start(self):
        threading.Thread(target=self._print_queue).start()

    def _print_queue(self):
        while (manager.server_running()):
            if (self._server_listener.has_next()):
                print(self._server_listener.next())


manager = ServerManager(server_dir)
manager.start_server()

listener = ServerListener(manager.server)
DebugPrintListener(listener).start()

while (manager.server_running()):
    command = input().strip()
    manager.server.write(command)
