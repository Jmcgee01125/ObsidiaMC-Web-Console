from flask import Flask, abort, flash, redirect, render_template, session, request
from config.configs import ObsidiaConfigParser
import uuid
import os


login_code = str(uuid.uuid4()) + "extras"

site_configs = ObsidiaConfigParser(os.path.join("config", "obsidia_website.conf"))
online = site_configs.get("Website", "internet").strip().lower() == "true"
web_port = int(site_configs.get("Website", "port").strip())
server_password = site_configs.get("Website", "password").strip()

app = Flask(__name__, static_folder=os.path.join("pages", "static"), template_folder="pages")
app.secret_key = str(uuid.uuid4())


class Login():
    '''Check if a given session is logged in, as well as logging in and out.'''

    @staticmethod
    def check_login(s) -> bool:
        return "session_password" in s and s["session_password"] == login_code

    @staticmethod
    def log_in_user(s):
        s["session_password"] = login_code

    @staticmethod
    def log_out_user(s):
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


@app.route("/server")
def server():
    if not Login.check_login(session):
        abort(404)
    elif "serverselection" not in session:
        return redirect("/serverlist")
    else:
        return render_template("server.html")


def get_server_info() -> str:
    # TODO: turn this into a function or group of functions that server.html can use to build itself
    return session["serverselection"]


def get_server_list() -> list[str]:
    return ["server1", "server2", "server3"]


app.jinja_env.globals.update(get_server_info=get_server_info)
app.jinja_env.globals.update(get_server_list=get_server_list)


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
            flash("Invalid password.")
            return redirect("/login")
    else:
        return redirect("/login")


def start():
    print("Web console coming online.")

    if online:
        app.run(host="0.0.0.0", port=web_port)
    else:
        app.run(port=web_port)

    print("Web console offline.")
