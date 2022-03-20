from server.server_manager import ServerManager
from server.server import ServerListener
from dotenv import load_dotenv
import threading
import asyncio
import os


# TODO: web interface (web2py?) with uptime, playercount + names (mctools?), editable config, and of course a console
# TODO: password challenge based on password set in master config, which should have other options (meta-server and UI stuff like colors)

# TODO: create a guide for each option, such as using 0 to disable maximum backups or how SMTWRFD works

# TODO: iterate over a SERVERS_DIR to get subfolder names of potential servers, then check them to make sure they are servers
load_dotenv()
server_dir = os.getenv("SERVER_DIR")


class DebugPrintListener:
    def __init__(self, server_listener: ServerListener):
        self._server_listener = server_listener

    def start(self):
        threading.Thread(target=self._print_queue).start()

    def _print_queue(self):
        while (manager.server_should_be_running()):
            if (self._server_listener.has_next()):
                print(self._server_listener.next())
        print("DebugPrintListener closing")


async def start_server():
    global manager
    manager = ServerManager(server_dir)
    await manager.start_server()


async def watch_user_input():
    while (manager.server_should_be_running()):
        command = input()
        manager.write(command.strip())


async def debug_listen_to_server():
    listener = ServerListener(manager.server)
    DebugPrintListener(listener).start()


async def queue_initial_actions():
    await start_server()
    await debug_listen_to_server()
    await watch_user_input()


if __name__ == "__main__":
    asyncio.run(queue_initial_actions())
