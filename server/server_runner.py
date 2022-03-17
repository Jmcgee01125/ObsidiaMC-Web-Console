import subprocess
import os


class ServerRunner:
    '''
    Create an object referencing a running server.

    Parameters
    ----------
    server_directory: `str`
        The path to the directory of this server's jar file
    jarname: `str`
        The server jar, default "server.jar"
    args: `list[str]`
        A list of console arguments, such as -Xmx2G (You may need to add -server before some options)
        These arguments are parsed as java <args> -jar <jarname> -nogui

    Attributes
    ----------
    server_directory: `str`
        The absolute path to the server directory containing the jar file.
    '''

    def __init__(self, server_directory: str, jarname: str = "server.jar", args: list[str] = []):
        self.server_directory = os.path.abspath(server_directory)
        self._jarname = jarname
        self._args = args
        self._server = None

    def start(self):
        '''
        Start the server.

        Blocks until the server is fully started (may be half a minute or more).
        '''
        self._server = subprocess.Popen(["java"] + self._args + ["-jar"] + [self._jarname] + ["-nogui"],
                                        stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, cwd=self.server_directory)
        # TODO: block until stdout reports that server is started, and set a flag

    def write(self, message):
        '''Writes a single line message to the server console. \n automatically appended.'''
        try:
            self._server.stdin.write(bytes(f"{message}\n", "utf-8"))
            self._server.stdin.flush()
        except Exception as e:
            print("Write failed:", e)

    def is_running(self) -> bool:
        '''Check if the server is currently running.'''
        # TODO: bad, use a variable self.is_running that toggles in start and stop
        return self._server.poll() != None

    # TODO: listener for messages, loop stuck on for `line in iter(self.server.stdout.readline, "")`
    # should probably use an observer system

    def get_full_log(self) -> list[str]:
        '''Get a list of all console logs for the current server session.'''
        try:
            log_file = open(os.path.join(self.server_directory, "logs", "latest.log"))
        except IOError:
            return "No latest log found."
        return log_file.readlines()

    def stop(self):
        '''Stop the server, ALWAYS call this before closing the server (unless you've sent stop via rcon)'''
        # TODO: set flag is_running to false
        try:
            self._server.stdin.flush()
            self._server.communicate(b"stop\n")
        except Exception as e:
            print("Stop command failed:", e)
