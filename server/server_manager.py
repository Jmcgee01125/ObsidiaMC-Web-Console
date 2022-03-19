from config.configs import ConfigReader
from server.server import ServerRunner
import threading
import asyncio
import os


class ServerManager:
    '''
    Create and run a server given the directory.

    Parameters
    ----------
    server_directory: `str`
        The directory of the server, the server's jar and server.properties should be one layer below (e.g. server_directory/server.jar)
    config_file: `str`
        The basename of the config file for the server manager, default "obsidia.conf"
    '''

    def __init__(self, server_directory: str, config_file: str = "obsidia.conf"):
        self.server_directory = os.path.abspath(server_directory)
        self.config_file = os.path.join(self.server_directory, config_file)
        self.server: ServerRunner = None
        self._server_thread: threading.Thread = None
        self._load_server_information()
        self.reload_configs()

    def start_server(self):
        '''Creates a new thread to run the server in, returning the Server object.'''
        self.server = ServerRunner(self.server_directory, server_name=self._motd, jarname=self._server_jar, args=self._args)
        self._server_thread = threading.Thread(target=self._asynced_server_start)
        self._server_thread.start()
        # TODO: need some kind of monitor that autorestarts if it dies and self._restart_on_crash is true
        # TODO: also need a timed restarter and backup script, maybe make an awaitable event loop and add those checks to it?

    def server_running(self) -> bool:
        '''Returns true if the server thread is running, false otherwise.'''
        return self._server_thread != None and self._server_thread.is_alive()

    def _asynced_server_start(self):
        asyncio.run(self.server.start())

    def _load_server_information(self):
        for line in open(os.path.join(self.server_directory, "server.properties"), "r"):
            if "level-name" in line:
                self._level_name = line[11:].strip()
            if "motd" in line:
                self._motd = line[5:].strip()
            # TODO: port and other stuff like allow-flight (to be toggled in gui - or should gui read that? server.properties parser?)

    def reload_configs(self):
        '''Reload the configs from the current config file.'''
        config = ConfigReader(os.path.join(self.server_directory, self.config_file))

        # NOTE: the config items could be None in some cases, but we /should/ be reading from defaults anyway

        self._server_jar = config.get("Server Information", "server_jar").strip()
        self._args = config.get("Server Information", "args").strip().split(" ")
        self._server_name = config.get("Server Information", "server_name").strip()
        if self._server_name == "":
            self._server_name = None

        self._do_autorestart = config.get("Restarts", "autorestart").strip().lower() == "true"
        self._autorestart_datetime = config.get("Restarts", "autorestart_datetime").strip()
        self._restart_on_crash = config.get("Restarts", "restart_on_crash").strop().lower() == "true"

        self._do_backups = config.get("Backups", "do_backups").strip().lower() == "true"
        self._max_backups = int(config.get("Backups", "max_backups").strip())
        self._backup_datetime = config.get("Backups", "backup_datetime").strip()

        config.write()

    # TODO: don't forget server-icon.png! get_favicon or something

    # TODO: get information about the server like playercount, uptime,
    # TODO: by tracking console logs like who joins and whatnot, we don't need mctools at all - await self._parse_new_message(line)
