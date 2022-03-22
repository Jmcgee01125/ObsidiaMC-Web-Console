# ObsidiaMC Web Console

A python-based web console for Minecraft servers.

---

## Requirements

flask (pip install flask)

flask_mobility (pip install flask_mobility)

---

## Features

Host multiple Minecraft servers at a time.

Web console with password protection.

Accessible from local-only or web.

Start, stop, and send any Minecraft console commands.

Automatic, user-defined restarts and backups.

---

## Setup

1) Clone this repository (git clone \<url\>).
  
2) Open "config/obsidia_website.conf" with any text editor.
  
    1) Change settings based on your preference, like allowing internet access to the console.
    
    2) **CHANGE THE DEFAULT ADMIN PASSWORD.** Anything will do, but at least change it.
    
    3) Set the directory where your servers are stored. This can be relative to \_\_main__.py, or absolute.
    
        1) This should be a folder containing the folders of servers. E.g. "directory" from "directory/myserver/server.jar".
  
3) Start the program by running \_\_main__.py.
  
    1) Quit by using Ctrl+C in the terminal that the program runs in.

4) Close the program and navigate to your servers.

5) Each server should have an "obsidia.conf" file with extra settings like autorestart.
  
    1) If you're confused about settings, such as how to use SMTWRFD 0000, open the readme in the config folder.
  
    2) You can set defaults by changing settings in "config/obsidia_defaults.conf".
  
    3) Note that these config files are overwritten and filled in with defaults (for missing items only) when launched. Comments will be removed.

6) To connect to the web console when it's running, go to localhost:5000 (or whatever you set the port to) in your browser.
  
    1) If you enabled internet connection, jot down your IP or grab a URL host. Don't forget to port forward.

---

## Screenshots

![image](https://user-images.githubusercontent.com/38796431/159392006-e3921650-ab03-44c0-a245-10cbe058238c.png)

![image](https://user-images.githubusercontent.com/38796431/159392081-f20ef5f2-56a8-4b24-ab43-b449daf8adfc.png)

![image](https://user-images.githubusercontent.com/38796431/159396804-7b52ba9e-216c-4374-a417-b7249ee382f8.png)

![image](https://user-images.githubusercontent.com/38796431/159396850-49902ddb-b632-4baa-83fd-88345012fc45.png)
