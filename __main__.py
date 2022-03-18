from server.server_manager import ServerManager
from dotenv import load_dotenv
from queue import Queue
import threading
import os


# TODO: web interface (web2py?) with uptime, playercount, editable config, and of course a console

# TODO: password challenge based on password set in master config, which should have other options (meta-server and UI stuff like colors)


# TODO: iterate over a SERVERS_DIR to get subfolder names of potential servers, then check them to make sure they are servers
load_dotenv()
server_dir = os.getenv("SERVER_DIR")


class Listener:
    def __init__(self, manager: ServerManager):
        self.messages_queue = Queue()
        self.manager = manager
        # DEBUG: queue is good, but should probably not be spawning threads here for printing, instead let main watch the queue with an async
        threading.Thread(target=self.clear_queue).start()

    def notify(self, message: str):
        self.messages_queue.put(message)

    def clear_queue(self):
        while (manager.server_running()):
            if (not self.messages_queue.empty()):
                print(self.messages_queue.get())


manager = ServerManager(server_dir)
manager.start_server()

listener = Listener(manager)
manager.server.add_listener(listener)

while (manager.server_running()):
    command = input().strip()
    manager.server.write(command)
