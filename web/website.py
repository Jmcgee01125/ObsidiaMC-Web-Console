import time
from flask import Flask, abort, flash, redirect, render_template, session, request
from flask_mobility import Mobility
from server.server_manager import ServerManager
from config.configs import ObsidiaConfigParser
import uuid
import os


login_code = str(uuid.uuid4()) + "extras"

site_configs = ObsidiaConfigParser(os.path.join("config", "obsidia_website.conf"))
online = site_configs.get("Website", "internet").lower() == "true"
web_port = int(site_configs.get("Website", "port"))
server_password = site_configs.get("Website", "password")

app = Flask(__name__, static_folder=os.path.join("pages", "static"), template_folder="pages")
mobility = Mobility(app)
app.secret_key = str(uuid.uuid4())


class Login:
    '''Check if a given session is logged in, as well as logging in and out.'''

    @staticmethod
    def check_login(s) -> bool:
        '''Return true if logged in for this app, false otherwise.'''
        return "session_password" in s and s["session_password"] == login_code

    @staticmethod
    def log_in_user(s):
        '''Gives the user the login code.'''
        s["session_password"] = login_code

    @staticmethod
    def log_out_user(s):
        '''Resets the user's login code.'''
        s["session_password"] = ""


@app.route("/")
def homepage():
    return redirect("/login")


@app.route("/serverlist")
def serverlist():
    if not Login.check_login(session):
        abort(404)
    else:
        return render_template("serverlist.html")


@app.route("/selectserver", methods=["GET", "POST"])
def selectserver():
    if request.method == "POST":
        session["serverselection"] = request.form.get("serverselection")
        return redirect("/server")
    else:
        return redirect("/serverlist")


@app.route("/server", methods=["GET", "POST"])
def server():
    if request.method == "GET":
        if not Login.check_login(session):
            abort(404)
        elif "serverselection" not in session:
            return redirect("/serverlist")
        else:
            if request.MOBILE:
                return render_template("server_mobile.html")
            else:
                return render_template("server.html")
    elif request.method == "POST":
        manager = get_manager(session["serverselection"])
        selection = request.form.get("statusbutton", default=None)
        if selection != None:
            if selection == "stop" and manager.server_should_be_running():
                manager.stop_server()
            elif selection == "start" and not manager.server_should_be_running():
                manager.start_server()
            elif selection == "return":
                return redirect("/serverlist")
        else:
            command = request.form.get("commandentry", default=None)
            manager.write(command)
            time.sleep(1)
        return redirect("/server")


@app.errorhandler(404)
def error_404(error):
    return redirect("/")


def get_manager(server_name: str) -> ServerManager:
    '''Return the manager of the given server name.'''
    for server in server_handlers:
        if server.__str__() == server_name:
            return server.manager


def get_server_list() -> set[ServerManager]:
    return server_handlers


def get_server_name() -> str:
    manager = get_manager(session["serverselection"])
    return manager.get_name()


def get_server_log() -> list[str]:
    manager = get_manager(session["serverselection"])
    return manager.get_latest_log()


def get_server_status() -> str:
    manager = get_manager(session["serverselection"])
    if manager.server_active():
        return "Online"
    elif manager.server_should_be_running():
        return "Changing State"
    return "Offline"


@app.context_processor
def inject_load():
    symbols = dict()
    symbols["get_server_list"] = get_server_list
    symbols["get_server_name"] = get_server_name
    symbols["get_server_log"] = get_server_log
    symbols["get_server_status"] = get_server_status
    return symbols


@app.route("/login")
def login():
    if Login.check_login(session):
        return redirect("/serverlist")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    Login.log_out_user(session)
    return redirect("/")


@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        password = request.form.get("password", default="")
        if password == server_password:
            Login.log_in_user(session)
            return redirect("/serverlist")
        else:
            flash("Invalid password")
            return redirect("/login")
    else:
        return redirect("/login")


def start(handlers):
    global server_handlers
    server_handlers = handlers
    print("Web console coming online.")

    if online:
        app.run(host="0.0.0.0", port=web_port)
    else:
        app.run(port=web_port)

    print("Web console offline.")
