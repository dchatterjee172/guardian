from bottle import run, request, ServerAdapter, Bottle, abort
from bottle.ext import sqlite
from beaker.middleware import SessionMiddleware
from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
import ssl
import os
from database import (
    db_register,
    db_login,
    db_get_activities,
    db_add_activities,
    db_add_actions,
    db_last_action_time,
)
from sqlite3 import IntegrityError
from inspect import getargspec
from functools import wraps

app = Bottle()


class Unauthenticated_user(Exception):
    pass


class SSLCherryPyServer(ServerAdapter):
    def run(self, handler):
        server = wsgi.Server((self.host, self.port), handler)
        server.ssl_adapter = BuiltinSSLAdapter("cacert.pem", "privkey.pem")
        server.ssl_adapter.context.options |= ssl.OP_NO_TLSv1
        server.ssl_adapter.context.options |= ssl.OP_NO_TLSv1_1
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
            abort(400, "get out!")

    @wraps(func)
    def checker():
        try:
            userid = current_user()
            return func(userid=userid)
        except Unauthenticated_user:
            abort(400, "get out!")

    args = getargspec(func).args
    return checker_db if "db" in args else checker


@app.route("/register", method="post")
def register(db):
    payload = request.json
    email = str(payload["email"])
    password = str(payload["password"])
    try:
        db_register(db, email, password)
        return "registration succesful!"
    except IntegrityError:
        return abort(400, "you are doing something fishy!")


@app.route("/whoami")
@login_required
def whoami(userid):
    return {"userid": userid}


@app.route("/login", method="POST")
def login(db):
    payload = request.json
    email = str(payload["email"])
    password = str(payload["password"])
    id_, judgement = db_login(db, email, password)
    print(id_)
    if judgement:
        session = beaker_session()
        session["userid"] = id_
    else:
        abort(400, "get out!")


@app.route("/logout")
def logout():
    session = beaker_session()
    session.delete()


@app.route("/get_activities")
@login_required
def get_activities(db, userid):
    activities = db_get_activities(db, userid)
    return {"activities": activities}


@app.route("/add_activities", method="POST")
@login_required
def add_activities(db, userid):
    payload = request.json
    activities = payload["activities"]
    db_add_activities(db, userid, activities)


@app.route("/add_actions", method="POST")
@login_required
def add_actions(db, userid):
    payload = request.json
    actions = payload["actions"]
    db_add_actions(db, userid, actions)


@app.route("/last_action_time")
@login_required
def last_action_time(db, userid):
    time = db_last_action_time(db, userid)
    return {"time": time}


session_opts = {
    "session.type": "file",
    "session.data_dir": "./data",
    "session.auto": True,
    "session.cookie_expires": True,
    "session.save_accessed_time": True,
    "session.secure": True,
    "session.timeout": 300,
    "session.secret": dict(os.environ)["SECRET"],
    "session.httponly": True,
}

if __name__ == "__main__":
    plugin = sqlite.Plugin(dbfile="main.db")
    app.install(plugin)
    session_app = SessionMiddleware(app, session_opts)
    run(
        app=session_app,
        host="0.0.0.0",
        port=443,
        server=SSLCherryPyServer,
        debug=True,
        numthreads=1,
        reload=True,
    )
