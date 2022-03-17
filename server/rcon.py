from mctools import RCONClient


class RCONConnection:
    '''
    Create an object referencing an rcon connection to the server.

    Parameters
    ----------
    hostname: `str`
        The address of the server, such as "hypixel.net" or "localhost" or "192.0.0.1"
    rcon_password: `str`
        The password to authenticate rcon with
    rcon_port: `int`
        The port to connect on, default 25575

    Attributes
    ----------
    hostname: `str`
        The address of the server, such as "hypixel.net" or "localhost" or "192.0.0.1"
    port: `str`
        The rcon port being connected on
    '''

    def __init__(self, hostname: str, rcon_password: str, rcon_port: int = 25575):
        self.hostname: str = hostname
        self.port: int = rcon_port
        self._password: str = rcon_password
        self._rcon: RCONClient = None

    def connect(self) -> bool:
        '''Create a new connection to RCON.'''
        if self._rcon != None and self._rcon.is_connected():
            raise ConnectionError("RCON already connected.")
        self._rcon = RCONClient(host=self.hostname, port=self.port)
        return self._rcon.login(self._password)

    def send_command(self, command: str) -> str:
        '''Send a command via rcon, returning the server's response.'''
        if self._rcon == None or not self._rcon.is_connected():
            raise ConnectionError("RCON not connected.")
        try:
            response = self._rcon.command(command)
        except Exception as e:
            return f"Failed: {e}"
        return response

    def stop(self):
        '''Close the rcon connection, ALWAYS call this to prevent leaving a stale connection.'''
        if self._rcon == None or not self._rcon.is_connected():
            raise ConnectionError("RCON not connected.")
        self._rcon.stop()
