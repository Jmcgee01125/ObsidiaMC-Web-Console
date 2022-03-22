from server.server_manager import ServerManager
from config.configs import ObsidiaConfigParser
from server.server import ServerListener
from web import website
import threading
import asyncio
import glob
import os


class DebugPrintListener:
    def __init__(self, listener: ServerListener, manager: ServerManager):
        self._listener = listener
        self._manager = manager

    def start(self):
        threading.Thread(target=self._print_queue).start()

    def _print_queue(self):
        while (self._manager.server_should_be_running()):
            if (self._listener.has_next()):
                print(self._listener.next())
        print("DebugPrintListener closing")


class ServerHandler:
    def __init__(self, server_directory: str):
        self.server_directory = server_directory
        self.manager: ServerManager = ServerManager(self.server_directory)

    async def start_server(self):
        await self.manager.start_server()

    def __str__(self):
        return self.manager.get_name()


if __name__ == "__main__":
    server_dir = ObsidiaConfigParser(os.path.join("config", "obsidia_website.conf")).get("Servers", "directory")
    server_handlers: set[ServerHandler] = set()
    for folder in os.listdir(server_dir):
        path = os.path.join(server_dir, folder)
        if len(glob.glob(os.path.join(path, "*.jar"))) != 0:
            server_handlers.add(ServerHandler(path))

    for handler in server_handlers:
        pass  # DEBUG: disabled
        # asyncio.run(handler.start_server())

    website.start(server_handlers)

    # ctrl-c in the console, shut down all servers that haven't caught it already
    for handler in server_handlers:
        try:
            handler.manager.stop_server()
        except Exception:
            pass  # ignore "already shut down" errors

    if threading.active_count() > 1:
        print("Waiting for latent threads to close:")
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                print(f"\t{thread.getName()}")
        asyncio.run(asyncio.sleep(5))

    if threading.active_count() > 1:
        print("Some threads remain:")
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                print(f"\t{thread.getName()}")
        print("Raising SystemExit to attempt to close them.")
        print("If this doesn't close the terminal, try killing the task I guess.")
        raise SystemExit
