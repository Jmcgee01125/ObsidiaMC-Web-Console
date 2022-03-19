from config.configs import MCPropertiesParser, ObsidiaConfigParser
from server.server import ServerRunner
from time import sleep
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

    Attributes
    ----------
    server: `ServerRunner`
        The server being run.
        Note that it is recommended to use ServerManager's write method, not ServerRunners.
    config_file: `str`
        The config file in use
    server_directory: `str`
        The absolute path to the server directory containing the jar file
    '''

    def __init__(self, server_directory: str, config_file: str = "obsidia.conf"):
        self.server_directory = os.path.abspath(server_directory)
        self.config_file = os.path.join(self.server_directory, config_file)
        self.server: ServerRunner = None
        self._server_thread: threading.Thread = None
        self._monitor_thread: threading.Thread = None
        self._server_should_be_running = False
        self._reset_server_startup_vars()

    def _reset_server_startup_vars(self):
        '''Initial vars are those that need to be reset every time the server is launched, NOT threads or the like.'''
        self._sent_stop_signal = False
        self._load_server_information()
        self.reload_configs()

    def write(self, command: str) -> str:
        '''Sends a command to the server, returning its response.'''
        command = command.strip()
        if command == "stop":
            self._sent_stop_signal = True
        self.server.write(command)

    async def start_server(self):
        '''Creates a new thread to run the server in and a thread to monitor it for crashing/backups/etc.'''
        self._server_should_be_running = True
        self.server = ServerRunner(self.server_directory, server_name=self._motd, jarname=self._server_jar, args=self._args)
        await self._spawn_server_thread()
        await self._spawn_monitor_thread()

    async def _spawn_server_thread(self):
        self._server_thread = threading.Thread(target=self._asynced_server_start)
        self._server_thread.start()

    async def _spawn_monitor_thread(self):
        self._monitor_thread = threading.Thread(target=self._asynced_running_loop_start)
        self._monitor_thread.start()

    def _asynced_server_start(self):
        asyncio.run(self.server.start())

    def _asynced_running_loop_start(self):
        asyncio.run(self._running_loop())

    async def _running_loop(self):
        while (True):
            while (self.server_thread_running()):
                # TODO: check if time is past the autorestart time
                # TODO; check if time is past backup time
                sleep(5)
            if (self._restart_on_crash and not self._sent_stop_signal):
                self._reset_server_startup_vars()
                await self._spawn_server_thread()
            else:
                self._server_should_be_running = False
                self._server_thread = None
                self._monitor_thread = None
                break

    def backup_world(self):
        '''Creates a backup of the world in the backup directory, deleting older backups to maintain max.'''
        self.write("save-off")
        # TODO: do the backup
        self.write("save-on")

    def server_should_be_running(self) -> bool:
        '''Returns true if the server should be running (but might be restarting), false otherwise.'''
        return self._server_should_be_running

    def server_thread_running(self) -> bool:
        '''Returns true if the server's thread is currently running, false otherwise.'''
        return self._server_thread != None and self._server_thread.is_alive()

    def server_active(self) -> bool:
        '''Returns true if the server is active and ready to take commands.'''
        return self.server.is_ready()

    def _load_server_information(self):
        config = MCPropertiesParser(os.path.join(self.server_directory, "server.properties"))
        self._level_name = config.get("level-name").strip()
        self._motd = config.get("motd").strip()

    def reload_configs(self):
        '''Reload the configs from the current config file.'''
        config = ObsidiaConfigParser(os.path.join(self.server_directory, self.config_file))
        # NOTE: the config items could be None or invaid in some cases, but crashing is fine in these circumstances
        try:
            self._server_jar = config.get("Server Information", "server_jar").strip()
            self._server_name = config.get("Server Information", "server_name").strip()
            if self._server_name == "":
                self._server_name = None
            self._args = config.get("Server Information", "args").strip().split(" ")

            self._do_autorestart = config.get("Restarts", "autorestart").strip().lower() == "true"
            self._autorestart_datetime = config.get("Restarts", "autorestart_datetime").strip()
            self._restart_on_crash = config.get("Restarts", "restart_on_crash").strip().lower() == "true"

            self._do_backups = config.get("Backups", "backup").strip().lower() == "true"
            self._max_backups = int(config.get("Backups", "max_backups").strip())
            self._backup_datetime = config.get("Backups", "backup_datetime").strip()
            self._backup_folder = os.path.join(self.server_directory, config.get("Backups", "backup_folder").strip())

            config.write()
        except Exception:
            raise RuntimeError("Error reading configs for server.")

    # TODO: get information about the server like playercount, uptime,
    # TODO: by tracking console logs like who joins and whatnot, we don't need mctools at all - await self._parse_new_message(line)
