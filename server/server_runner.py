import subprocess
import os
import threading


class ServerRunner:
    '''
    Create an object referencing a running server.

    Parameters
    ----------
    server_directory: `str`
        The path to the directory of this server's jar file
    server_name: `str`
        The name of this server, or None to use the lowest directory of the server directory (i.e. Servers/ServerName/server.jar -> ServerName)
    jarname: `str`
        The server jar, default "server.jar"
    args: `list[str]`
        A list of console arguments, such as -Xmx2G (You may need to add -server before some options)
        These arguments are parsed as java <args> -jar <jarname> -nogui

    Attributes
    ----------
    server_directory: `str`
        The absolute path to the server directory containing the jar file
    server_name: `str`
        The name of the server being run (note that this is not necessarily read from the config file)
    '''

    def __init__(self, server_directory: str, server_name: str = None, jarname: str = "server.jar", args: list[str] = []):
        self._is_started = False
        self.server_directory = os.path.abspath(server_directory)
        if (server_name == None):
            self.server_name = os.path.basename(server_directory)
        else:
            self.server_name = server_name
        self._jarname = jarname
        self._args = args
        self._server = None
        self._listeners = set()

    async def run(self):
        '''Alias to start.'''
        await self.start()

    async def start(self):
        '''Start the server process if not already started.'''
        if (self._server == None or not self.is_active()):
            self._server = subprocess.Popen(["java"] + self._args + ["-jar"] + [self._jarname] + ["-nogui"],
                                            stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, cwd=self.server_directory)
            await self._listen_for_logs()

    async def _listen_for_logs(self):
        '''
        Monitors stdout for logs, reporting them to listeners.

        This function should only be called once per process.
        '''
        while (self.is_active()):
            line = self._server.stdout.readline().decode().strip()
            await self._check_if_started(line)
            await self._notify_listeners(line)
        # process is dead
        self._is_started = False
        self._server = None

    async def _check_if_started(self, msg: str):
        if not self._is_started and "INFO]: Done (" in msg:
            self._is_started = True

    async def _notify_listeners(self, msg: str):
        for listener in self._listeners:
            listener.notify(msg)

    def add_listener(self, listener_object):
        '''
        Subscribe the given object to be notified on this thread whenever there is a new message in the server console.

        The subscriber must contain the function "notify(message: `str`)"
        '''
        try:
            listener_object.notify(f"Subscribed to logs for {self.server_name}.")
        except Exception:
            raise AttributeError("Listener does not contain notify(message: str) attribute.")
        else:
            self._listeners.add(listener_object)

    def is_active(self) -> bool:
        '''Check if the server's thread is currently active (not necessarily that the server is running).'''
        return self._server != None and self._server.poll() == None

    def is_started(self) -> bool:
        '''Check if the server is currently started, i.e. players are able to join.'''
        return self._is_started

    def write(self, message):
        '''Write a single line message to the server console. Newline automatically appended.'''
        try:
            self._server.stdin.write(bytes(f"{message}\n", "utf-8"))
            self._server.stdin.flush()
        except Exception as e:
            print("Write failed:", e)

    def get_full_log(self) -> list[str]:
        '''Get a list of all console logs for the current server session.'''
        try:
            log_file = open(os.path.join(self.server_directory, "logs", "latest.log"), "r")
        except IOError:
            return "No latest log found."
        return log_file.readlines()

    def stop(self):
        '''Stop the server, ALWAYS call this before closing the server (unless you've sent stop via rcon).'''
        try:
            self._server.stdin.flush()
            self._server.communicate(b"stop\n")  # should kill process
        except Exception as e:
            print("Stop command failed:", e)
        finally:
            self._is_started = False

    def kill(self):
        '''Kills the server process. DO NOT RUN THIS UNLESS YOU ABSOLUTELY HAVE TO.'''
        self._server.kill()
        self._is_started = False
