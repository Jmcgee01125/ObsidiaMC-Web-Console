from server.server_runner import ServerRunner
from configparser import ConfigParser
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
        self._load_server_information()
        self._load_config_information()
        self.server: ServerRunner = None

    def start_server(self):
        '''Creates a new thread to run the server in, returning the Server object.'''
        self.server = ServerRunner(self.server_directory, server_name=self._motd, jarname=self._server_jar, args=self._args)
        server_thread = threading.Thread(target=self._asynced_server_start)
        server_thread.start()

    def _asynced_server_start(self):
        asyncio.run(self.server.start())

    def _load_server_information(self):
        for line in open(os.path.join(self.server_directory, "server.properties"), "r"):
            if "level-name" in line:
                self._level_name = line[11:].strip()
            if "motd" in line:
                self._motd = line[5:].strip()

    def _load_config_information(self):
        config = ConfigParser()
        conf_exists = config.read(os.path.join(self.server_directory, self.config_file))
        if len(conf_exists) != 0:
            self._server_jar = config.get("Server Information", "server_jar").strip()
            self._args = config.get("Server Information", "args").strip().split(" ")
            self._do_autorestart = config.get("Restarts", "autorestart").strip().lower() == "true"
            self._autorestart_datetime = config.get("Restarts", "autorestart_datetime").strip()
            self._do_backups = config.get("Backups", "do_backups").strip().lower() == "true"
            self._max_backups = int(config.get("Backups", "max_backups").strip())
            self._backup_datetime = config.get("Backups", "backup_datetime").strip()
        else:
            self._create_config()

    def _create_config(self):
        with open(self.config_file, "w") as file:
            file.write("# For datetimes, input as SMTWRFD where S = Sunday, D = Saturday, etc.\n")
            file.write("# Present letters indicate days where the action will be taken.\n")
            file.write("# Additionally, add the timestamp in HHMM format, 24-hour time.\n")
            file.write("\n")
            file.write("[Server Information]\n")
            file.write("server_jar=server.jar\n")
            file.write("args=-server -Xmx3G -Xms3G\n")
            file.write("\n")
            file.write("[Restarts]\n")
            file.write("autorestart=False\n")
            file.write("autorestart_datetime=SMTWRFD 0000\n")
            file.write("\n")
            file.write("[Backups]\n")
            file.write("do_backups=True\n")
            file.write("max_backups=3\n")
            file.write("backup_datetime=SMTWRFD 0000\n")
            file.write("\n")
        self._load_config_information()

    # TODO: edit_config function that then calls _create_config, which only loads defaults if there isn't anything loaded when it's called

    # TODO: config option for server name or use motd (Server Name or blank)
    # TODO: don't forget server-icon.png! get_favicon or something

    # TODO: get information about the server like playercount, uptime,
    # TODO: by tracking console logs like who joins and whatnot, we don't need mctools at all - await self._parse_new_message(line)
