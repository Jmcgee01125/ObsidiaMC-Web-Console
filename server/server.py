from typing import List
import subprocess
import queue
import os


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

    def __init__(self, server_directory: str, server_name: str = None, jarname: str = "server.jar", args: List[str] = []):
        self._is_ready = False
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
            cmd = f"java "
            for arg in self._args:
                cmd += f"{arg} "
            cmd += f"-jar {self._jarname} -nogui"
            self._server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, cwd=self.server_directory)
            await self._listen_for_logs()

    async def _listen_for_logs(self):
        '''
        Monitors stdout for logs, reporting them to listeners.

        This function should only be called once per server thread.
        '''
        while (self.is_active()):
            try:
                line = self._server.stdout.readline().decode().strip()
            except ValueError:  # info->buf could be NUL
                pass
            else:
                await self._update_listeners(line)
                if not self._is_ready:
                    await self._check_if_ready(line)
        # process is dead
        self._is_ready = False
        self._server = None

    async def _check_if_ready(self, msg: str):
        if "INFO]: Done (" in msg:
            self._is_ready = True
        elif "INFO]: You need to agree to the EULA" in msg:
            self.kill()

    async def _update_listeners(self, msg: str):
        for listener in self._listeners:
            listener.update(msg)

    def add_listener(self, listener_object):
        '''
        Subscribe the given object to be notified on this thread whenever there is a new message in the server console.

        The subscriber must contain the function "update(message: `str`)", otherwise throws AttributeError when adding listener.
        '''
        try:
            listener_object.update(f"Subscribed to logs for {self.server_name}.")
        except AttributeError:
            raise AttributeError("Listener does not contain update(message: str) attribute.")
        else:
            self._listeners.add(listener_object)

    def remove_listener(self, listener_object):
        '''Unsubscribes an object from updates.'''
        try:
            self._listeners.remove(listener_object)
        except KeyError:
            pass
        else:
            try:
                listener_object.update(f"Unsubscribed from logs for {self.server_name}.")
            except AttributeError:
                raise AttributeError("Listener does not contain update(message: str) attribute.")

    def is_active(self) -> bool:
        '''Check if the server's thread is currently active (not necessarily that the server is running).'''
        return self._server != None and self._server.poll() == None

    def is_ready(self) -> bool:
        '''Check if the server is currently started, i.e. players are able to join.'''
        return self._is_ready

    def write(self, command: str):
        '''Write a single line command to the server console. Newline automatically appended.'''
        try:
            self._server.stdin.write(bytes(f"{command}\n", "utf-8"))
            self._server.stdin.flush()
        except Exception as e:
            print("Write failed:", e)

    def stop(self):
        '''
        Stop the server, ALWAYS call this before closing the server (unless you've sent stop via rcon).

        Note that is_restarting only changes the message that users see, and does not actually restart.
        '''
        try:
            self._server.stdin.flush()
            self._server.communicate(b"stop\n", timeout=5)
        except Exception as e:
            print("Stop command failed:", e, "\n\t(Server may already be offline.)")
        finally:
            self._is_ready = False

    def kill(self):
        '''Kills the server process. DO NOT RUN THIS UNLESS YOU ABSOLUTELY HAVE TO.'''
        self._server.kill()
        self._is_ready = False


class ServerListener:
    '''
    Listens to a given server and creates a queue that can be queried for messages.
    Automatically subscribes to the server passed as parameter.

    Parameters
    ----------
    server: `ServerRunner`
        The server to listen to
    '''

    def __init__(self, server: ServerRunner):
        self._server = server
        self._message_queue = queue.Queue()
        self.subscribe()

    def subscribe(self):
        '''Subscribes this listener to the server passed in __init__.'''
        self._server.add_listener(self)

    def unsubscribe(self):
        '''Unsubscribes from the server's listener pool.'''
        self._server.remove_listener(self)

    def update(self, message: str):
        self._message_queue.put(message)

    def next(self) -> str:
        '''Returns the first message in the queue, or None if empty.'''
        if (self._message_queue.empty()):
            return None
        else:
            # it's possible to pass an empty check but not have an item, this causes a block until an item is added (hence timeout w/ try)
            try:
                return self._message_queue.get(timeout=1)
            except queue.Empty:
                return None

    def has_next(self) -> bool:
        '''Returns true if there is a message in queue, false otherwise.'''
        return not self._message_queue.empty()
