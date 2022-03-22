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
        self._is_autorestarting = False
        self._load_server_information()
        self.reload_configs()

    def write(self, command: str):
        '''Sends a command to the server.'''
        command = command.strip()
        if command == "stop":
            self._sent_stop_signal = True
            self.server.stop()
        else:
            self.server.write(command)

    def stop_server(self):
        '''Sends a stop command to the server.'''
        self._sent_stop_signal = True
        self.server.stop()

    def restart_server(self):
        '''Sends a stop command to the server, but restarts.'''
        self._is_autorestarting = True
        self.server.stop()

    def start_server(self):
        '''Creates a new thread to run the server in and a thread to monitor it for crashing/backups/etc.'''
        self._server_should_be_running = True
        self.server = ServerRunner(self.server_directory, server_name=self.get_name(), jarname=self._server_jar, args=self._args)
        self._spawn_server_thread()
        self._spawn_monitor_thread()

    def _spawn_server_thread(self):
        self._server_start_time = self._get_current_time()
        self._server_thread = threading.Thread(target=self._asynced_server_start, name=f"ServerThread")
        self._server_thread.start()

    def _spawn_monitor_thread(self):
        self._monitor_thread = threading.Thread(target=self._asynced_running_loop_start, name=f"MonitorThread")
        self._monitor_thread.start()

    def _asynced_server_start(self):
        asyncio.run(self.server.start())

    def _asynced_running_loop_start(self):
        asyncio.run(self._running_loop())

    async def _running_loop(self):
        while (self.server_should_be_running()):
            time_until_restart = self._get_offset_until(self._autorestart_datetime)
            time_until_backup = self._get_offset_until(self._backup_datetime)
            while (self.server_thread_running()):
                await asyncio.sleep(5)  # longer causes high delay between server shutdown and server appearing shut down in _server_should_be_running

                if self._do_autorestart:
                    new_time_until_restart = self._get_offset_until(self._autorestart_datetime)
                    if new_time_until_restart > time_until_restart:  # passed timestamp, it's sending next occurrence
                        self.write("say Restarting now!")
                        self._is_autorestarting = True
                        self.server.stop()
                    elif new_time_until_restart <= 60 and time_until_restart > 60:
                        self.write("say Restarting in 60 seconds!")
                    elif new_time_until_restart <= 300 and time_until_restart > 300:
                        self.write("say Restarting in 5 minutes.")
                    elif new_time_until_restart <= 900 and time_until_restart > 900:
                        self.write("say Restarting in 15 minutes.")
                    time_until_restart = new_time_until_restart

                if self._do_backups:
                    new_time_until_backup = self._get_offset_until(self._backup_datetime)
                    if new_time_until_backup > time_until_backup:  # passed timestamp, it's sending next occurrence
                        self.backup_world()
                    time_until_backup = new_time_until_backup

            # clean up after the server closes based on whether or not we need to restart
            if self._is_autorestarting:
                self._update_server_listeners("Automatically restarting")
                self._reset_server_startup_vars()
                await self._spawn_server_thread()
            elif self._restart_on_crash and not self._sent_stop_signal:
                self._update_server_listeners("Detected server crash: Restarting")
                self._reset_server_startup_vars()
                await self._spawn_server_thread()
            else:
                self._server_should_be_running = False

    def _get_current_time(self) -> int:
        return int(time.time())

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
        offset -= current_time.second
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
        self._update_server_listeners("Backing up world")
        # turn off autosaving while doing the backup to prevent conflicts, but server might be off already so try/except
        if self.server.is_ready():
            try:
                self.write("save-off")
            except Exception:
                pass
        if self._max_backups > 0:
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
            self._update_server_listeners(f"Failed to back up world: {e}")
        # turn back on autosaving
        # NOTE: should probably save the initial state of it and set it back to that, rather than forcing it on (config?)
        if self.server.is_ready():
            try:
                self.write("save-on")
            except Exception:
                pass
        self._update_server_listeners("Backup completed")

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
        if self.server == None:
            return False
        return self.server.is_ready()

    def _load_server_information(self):
        config = MCPropertiesParser(os.path.join(self.server_directory, "server.properties"))
        self._level_name = config.get("level-name").strip()
        self._motd = config.get("motd").strip()

    def _update_server_listeners(self, message: str):
        timestamp = f"[{datetime.now().strftime('%H:%M:%S')}] [Manager]: "
        # headache: since the loop gets stuck in monitoring, it couldn't run this task
        # to fix: make sure that the monitor has an awaitable that lets other tasks go
        try:
            asyncio.get_running_loop().create_task(self.server._update_listeners(timestamp + message))
        except RuntimeError:  # called without async
            pass

    def reload_configs(self):
        '''Reload the configs from the current config file.'''
        config = ObsidiaConfigParser(os.path.join(self.server_directory, self.config_file))
        # NOTE: the config items could be None or invalid in some cases, but crashing is fine in these circumstances
        try:
            self._server_jar = config.get("Server Information", "server_jar")
            self._server_name = config.get("Server Information", "server_name")
            if self._server_name == "":
                self._server_name = None
            self._args = config.get("Server Information", "args").split(" ")

            self._do_autorestart = config.get("Restarts", "autorestart").lower() == "true"
            self._autorestart_datetime = config.get("Restarts", "autorestart_datetime")
            self._restart_on_crash = config.get("Restarts", "restart_on_crash").lower() == "true"

            self._do_backups = config.get("Backups", "backup").lower() == "true"
            self._max_backups = int(config.get("Backups", "max_backups"))
            self._backup_datetime = config.get("Backups", "backup_datetime")
            self._backup_directory = os.path.join(self.server_directory, config.get("Backups", "backup_folder"))

            config.write()
        except Exception as e:
            raise RuntimeError(f"Error reading configs for server: {e}")

    def uptime(self) -> int:
        '''Get the time the server has been running since it was last started, in seconds.'''
        if (self.server_thread_running()):
            return self._get_current_time() - self._server_start_time
        return 0

    def get_name(self) -> str:
        '''Get the name of the server in use.'''
        if self._server_name != None:
            return self._server_name
        else:
            return os.path.basename(self.server_directory)

    def get_latest_log(self) -> list[str]:
        '''Get a list of all console logs for the latest server session.'''
        try:
            log_file = open(os.path.join(self.server_directory, "logs", "latest.log"), "r")
        except IOError:
            return "No latest log found."
        return log_file.readlines()
