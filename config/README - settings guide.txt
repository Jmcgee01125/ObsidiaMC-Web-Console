----- [Server Information] -----


server_jar
The name of the server jar, such as server.jar (a vanilla jar).
Some versions, like fabric, may use alternates.

server_name
The name of the server as it should appear in interfaces.
This has no effect on the server itself.
If left blank, the directory of the server is used instead.

args
Server startup arguments, like setting the amount of RAM.
These arguments are parsed as "java <args> -jar <jarname> -nogui"


----- [Restarts] -----


autorestart
Automatically restart the server at specific times.

autorestart_datetime
The datetime to restart the server at (No effect if autorestart is false).
Follows the format of SMTWRFD HHMM, where SMTWRFD indicates days (Sun -> Sat) when a restart should occur.
HHMM is the time, in 24 hour time (0000 -> 2359) that the restart should happen at.
Players are given a 15 minute, 5 minute, and 1 minute warning before restarts.

restart_on_crash
Automatically restart the server when it goes down.
You MUST send a stop command via the web console to fully shut down a server.
(Stop commands sent in-game will be interpreted as crashes)


----- [Backups] -----


backup
If true, do backups at the specified interval.

max_backups
The maximum number of backups to keep.
Older backups will be deleted when new ones are made.
To disable, use a value less than or equal to 0.

backup_datetime
The datetime to backup the server at (No effect if backup is false)
Follows the format of SMTWRFD HHMM, where SMTWRFD indicates days (Sun -> Sat) when a backup should occur.
HHMM is the time, in 24 hour time (0000 -> 2359) that the backup should happen at.

backup_folder
The folder to make backups in.
This folder is nested within the server's directory.


----- [Website] -----


internet
True if the server should be accessible to the internet rather than just localhost.

port
The port the server is accessible over.

password
The admin password for the website.
PLEASE change from the default value.


----- [Servers] -----


directory
The directory where servers are located.
Directories from root/C/whatever are recommended, but not required (relative to the cwd of the web console).

start_all_servers_on_startup
If true, then all servers will be started when the program starts.
Otherwise, each will have to be turned on manually in the web console.
