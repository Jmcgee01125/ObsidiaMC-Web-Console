from configparser import ConfigParser
from typing import Union
import os


class ObsidiaConfigParser:
    '''
    Open and interact with a config file.

    Parameters
    ----------
    config_file: `str`
        The config file to read from, will be created if nonexistant
    '''

    def __init__(self, config_file: str):
        self._file = os.path.abspath(config_file)
        self._parser = ConfigParser()
        exists = self._parser.read(self._file)
        # create an empty file that will just use defaults
        if len(exists) == 0:
            with open(self._file, "w") as file:
                file.write("\n")

        self._defaults_configs_file = os.path.join("config", "obsidia_defaults.conf")
        self._defaults_parser = ConfigParser()
        self._defaults_parser.read(self._defaults_configs_file)

    def read(self, config_file: str):
        '''Replaces the currently read file with the newly specified file.'''
        self._file = os.path.abspath(config_file)
        self._parser.read(self._file)

    def write(self):
        '''Writes the current config to the current file.'''
        self._parser.write(open(self._file, "w"), space_around_delimiters=False)

    def get_config_file(self):
        '''Returns the absolute path of the current config file.'''
        return self._file

    def get(self, section: str, option: str, return_default: bool = True) -> str:
        '''
        Returns a given option in the specified config file.

        Parameters
        ----------
        section: `str`
            The section that the data is under, such as [Settings]
        option: `str`
            The actual option name, such as varname in varname=42
        return_default: `bool`
            If true, will return the default value if the option does not exist. If true, will return None.
            If there is no default value, will return None.

        Return
        ------
        The string in the option or default, for the client to parse
        '''
        value = self._parser.get(section, option, fallback=None)
        if value == None:
            return self._defaults_parser.get(section, option, fallback=None)

    def add_section(self, section: str):
        '''Add a new section to the config.'''
        self._parser.add_section(section)

    def remove_section(self, section: str):
        '''Removes a section and all of its options.'''
        self._parser.remove_section(section)

    def set_option(self, section: str, option: str, value: Union[str, None]):
        '''Add a new option to the config, including the value.'''
        self._parser.set(section, option, value)


class MCPropertiesParser:
    '''
    Open and interact with a server.properties file.

    Parameters
    ----------
    properties_file: `str`
        The properties file to read from
    '''

    def __init__(self, properties_file: str):
        self._file = os.path.abspath(properties_file)

    def get(self, option: str) -> str:
        '''Read a specified option from the properties file.'''
        for line in open(self._file, "r"):
            if line[:len(option)] == option:
                return line[len(option) + 1:].strip()
        return None

    def set(self, option: str, value: str):
        '''
        Edit a specified option to a new value.

        If the option does not exist, there is no effect.
        '''
        full_lines = ""
        for line in open(self._file, "r"):
            if line[:len(option)] == option:
                full_lines += line[:len(option) + 1] + value + "\n"
            else:
                full_lines += line
        file_write = open(self._file, "w")
        file_write.write(full_lines)
        file_write.close()
