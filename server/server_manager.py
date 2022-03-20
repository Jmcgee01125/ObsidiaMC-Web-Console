from config.configs import MCPropertiesParser, ObsidiaConfigParser
from server.server import ServerRunner
from datetime import datetime
import threading
import asyncio
import shutil
import time
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

    def _get_current_time(self) -> int:
        return time.time() // 1000

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
        self._server_start_time = self._get_current_time()
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
        while (self.server_should_be_running()):
            restart_on_next_loop = False
            backup_on_next_loop = False
            while (self.server_thread_running()):
                time.sleep(10)  # longer delays cause an unreasonable wait between server shutdown and server appearing shut down

                # TODO: use a better scheduler, track a last_restart/backup_time and use that
                if restart_on_next_loop:
                    self.write("say Restarting now!")
                    self.server.stop()
                    restart_on_next_loop = False
                elif self._do_autorestart:
                    time_until_autorestart = self._get_offset_until(self._autorestart_datetime)
                    if time_until_autorestart <= 60:
                        self.write("say Restarting in 60 seconds!")
                        restart_on_next_loop = True
                    elif time_until_autorestart <= 300:
                        self.write("say Restarting in 5 minutes.")
                    elif time_until_autorestart <= 900:
                        self.write("say Restarting in 15 minutes.")

                if backup_on_next_loop:
                    self.backup_world()
                    backup_on_next_loop = False
                elif self._do_backups:
                    time_until_backup = self._get_offset_until(self._backup_datetime)
                    if time_until_backup < 60:
                        self.backup_world()

            # clean up after the server closes based on whether or not we need to restart
            if (self._restart_on_crash and not self._sent_stop_signal):
                self._update_server_listeners("Manager detected server crash: Restarting.")
                self._reset_server_startup_vars()
                await self._spawn_server_thread()
            else:
                self._server_should_be_running = False
                self._server_thread = None
                self._monitor_thread = None

    def _get_offset_until(self, timestamp: str) -> int:
        '''Parse SMTWRFD HHMM timestamp and check how far away it is from now, in seconds.'''
        offset = 0
        current_time = datetime.now()
        timestamp_parts = timestamp.split(" ")
        days = timestamp_parts[0]
        hour = int(timestamp_parts[1][:2])
        mins = int(timestamp_parts[1][2:])
        offset += (hour - current_time.hour) * 3600
        offset += (mins - current_time.minute) * 60
        current_day_num = (current_time.weekday() + 1) % 7
        for i in range(14 - current_day_num):  # 14 not 7 because we have to account for wrapping if we skip the one day a week it runs
            # check offset < 0 because we need to skip if we already passed the timestamp on the first day checked (today)
            if "SMTWRFDSMTWRFD"[current_day_num + i] not in days or offset < 0:
                offset += 86400
            else:
                break
        return offset

    def backup_world(self):
        '''Creates a backup of the world in the backup directory, deleting older backups to maintain max.'''
        self._update_server_listeners("Backing up world.")
        # turn off autosaving while doing the backup to prevent conflicts, but server might be off already so try/except
        try:
            self.write("save-off")
        except Exception:
            pass
        # hacky way to check which backups were created automatically and use the timestamp name
        backup_list = self.list_backups()
        total_backups = 0
        oldest_backup = 1000000000000000000000  # eh good enough
        for backup in backup_list:
            try:
                backup = int(backup)
            except:
                pass
            else:
                oldest_backup = min(backup, oldest_backup)
                total_backups += 1
        if total_backups >= self._max_backups:
            self._delete_world(os.path.join(self._backup_directory, f"{oldest_backup}"))
        # alright, now we can backup
        world_dir = os.path.join(self.server_directory, self._level_name)
        backup_dir = os.path.join(self._backup_directory, f"{self._get_current_time()}")
        try:
            self._copy_world(world_dir, backup_dir)
        except Exception as e:
            self._update_server_listeners("Failed to back up world:", f"{e}")
        # turn back on autosaving
        # NOTE: should probably save the initial state of it and set it back to that, rather than forcing it on (config?)
        try:
            self.write("save-on")
        except Exception:
            pass
        self._update_server_listeners("Backup completed.")

    def list_backups(self) -> list[str]:
        '''Returns a list of world backups.'''
        return os.listdir(self._backup_directory)

    def restore_backup(self, backup: str):
        '''
        Restores a backup from a specified timestamp.

        Fails if the server is currently running, or if the specified backup does not exist.
        (Note that only the existance of the directory pointed to is checked. It may be empty.)
        '''
        if self.server_should_be_running():
            raise RuntimeError("Cannot restore backup while server is running.")
        backup_list = self.list_backups()
        if backup in backup_list:
            world_dir = os.path.join(self.server_directory, self._level_name)
            backup_dir = os.path.join(self._backup_directory, backup)
            self._delete_world(world_dir)
            self._copy_world(backup_dir, world_dir)
        else:
            raise FileNotFoundError("Specified backup does not exist.")

    def _copy_world(self, source, destination):
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("*.lock"))

    def _delete_world(self, world):
        shutil.rmtree(world)

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

    def _update_server_listeners(self, *strs):
        message = ""
        for str in strs:
            message += str + " "
        asyncio.get_running_loop().create_task(self.server._update_listeners(message[:-1]))

    def reload_configs(self):
        '''Reload the configs from the current config file.'''
        config = ObsidiaConfigParser(os.path.join(self.server_directory, self.config_file))
        # NOTE: the config items could be None or invalid in some cases, but crashing is fine in these circumstances
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
            self._backup_directory = os.path.join(self.server_directory, config.get("Backups", "backup_folder").strip())

            config.write()
        except Exception as e:
            raise RuntimeError("Error reading configs for server:", e)

    def uptime(self) -> int:
        '''Get the time the server has been running since it was last started, in seconds.'''
        if (self.server_thread_running()):
            return self._get_current_time() - self._server_start_time
        return 0
