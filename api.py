from bottle import run, request, ServerAdapter, Bottle, abort
from bottle.ext import sqlite
from beaker.middleware import SessionMiddleware
from cheroot import wsgi
import os
from database import (
    db_register,
    db_login,
    db_get_activities,
    db_add_activities,
    db_add_actions,
    db_last_action_time,
    db_get_action_current_day,
)
from sqlite3 import IntegrityError
from inspect import getargspec
from functools import wraps
import altair as alt
from io import StringIO
from datetime import datetime
from dateutil import parser
import pytz
from bs4 import BeautifulSoup

app = Bottle()
using_timezone = pytz.timezone("Asia/Calcutta")


class Unauthenticated_user(Exception):
    pass


class CherryPyServer(ServerAdapter):
    def run(self, handler):
        server = wsgi.Server((self.host, self.port), handler)
        try:
            server.start()
        finally:
            server.stop()


def beaker_session():
    return request.environ.get("beaker.session")


def current_user():
    session = beaker_session()
    userid = session.get("userid", None)
    if userid is None:
        raise Unauthenticated_user("Unauthenticated user")
    return userid


def login_required(func):
    @wraps(func)
    def checker_db(db):
        try:
            userid = current_user()
            return func(db=db, userid=userid)
        except Unauthenticated_user:
            abort(401, "get out!")

    @wraps(func)
    def checker():
        try:
            userid = current_user()
            return func(userid=userid)
        except Unauthenticated_user:
            abort(401, "get out!")

    args = getargspec(func).args
    return checker_db if "db" in args else checker


@app.route("/api_register", method="post")
def register(db):
    payload = request.json
    email = str(payload["email"])
    password = str(payload["password"])
    try:
        db_register(db, email, password)
        return {"success": True}
    except IntegrityError:
        return abort(400, "you are doing something fishy!")


@app.route("/api_whoami")
@login_required
def whoami(userid):
    return {"userid": userid}


@app.route("/api_login", method="POST")
def login(db):
    payload = request.json
    email = str(payload["email"])
    password = str(payload["password"])
    userid, judgement = db_login(db, email, password)
    if judgement:
        session = beaker_session()
        session["userid"] = userid
        return {"success": True}
    else:
        abort(400, "get out!")


@app.route("/api_logout")
def logout():
    session = beaker_session()
    session.delete()
    return {"success": True}


@app.route("/api_get_activities")
@login_required
def get_activities(db, userid):
    activities = db_get_activities(db, userid)
    return {"activities": sorted(activities)}


@app.route("/api_add_activities", method="POST")
@login_required
def add_activities(db, userid):
    payload = request.json
    activities = payload["activities"]
    db_add_activities(db, userid, activities)
    return {"success": True}


@app.route("/api_add_actions", method="POST")
@login_required
def add_actions(db, userid):
    payload = request.json
    actions = payload["actions"]
    db_add_actions(db, userid, actions)
    return {"success": True}


@app.route("/api_last_action_time")
@login_required
def last_action_time(db, userid):
    timestamp_str = db_last_action_time(db, userid)
    now = datetime.now(pytz.timezone("GMT"))
    if timestamp_str is None:
        now = now.astimezone(using_timezone)
        delta = now - now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        timestamp = parser.parse(timestamp_str, default=now)
        now = now.astimezone(using_timezone)
        delta = now - timestamp.astimezone(using_timezone)
    delta = delta.total_seconds() // 60
    return {"minutes_ago": int(delta)}


@app.route("/api_get_chart")
@login_required
def get_chart(db, userid):
    df = db_get_action_current_day(db, userid)
    chart = alt.Chart(df).mark_bar().encode(x="activity", y="duration_minutes")
    html = StringIO()
    chart.save(html, "html")
    html.seek(0)
    html = html.read()
    html = BeautifulSoup(html)
    body = html.body
    script = body.find("script")
    return {"script": script.contents[0]}


session_opts = {
    "session.type": "file",
    "session.data_dir": "./data",
    "session.auto": True,
    "session.cookie_expires": True,
    "session.save_accessed_time": True,
    "session.secure": True,
    "session.timeout": 3000,
    "session.secret": dict(os.environ)["SECRET"],
    "session.httponly": True,
}

if __name__ == "__main__":
    plugin = sqlite.Plugin(dbfile="main.db")
    app.install(plugin)
    session_app = SessionMiddleware(app, session_opts)
    run(
        app=session_app,
        host="localhost",
        port=8080,
        server=CherryPyServer,
        debug=True,
        numthreads=1,
    )
