from bottle import run, request, ServerAdapter, Bottle, abort
from bottle.ext import sqlite
from beaker.middleware import SessionMiddleware
from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
import ssl
import os
from database import db_register
from sqlite3 import IntegrityError

app = Bottle()


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
def whoami():
    try:
        userid = current_user()
    except Exception:
        userid = None
    return {"userid": userid}


@app.route("/login", method="POST")
def login(db):
    pass


@app.route("/logout", method="POST")
def logout():
    session = beaker_session()
    session.delete()


def beaker_session():
    return request.environ.get("beaker.session")


def current_user():
    session = beaker_session()
    userid = session.get("userid", None)
    if userid is None:
        raise Exception("Unauthenticated user")
    return userid


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


session_opts = {
    "session.type": "file",
    "session.data_dir": "./data",
    "session.auto": True,
    "save_accessed_time": True,
    "secure": True,
    "timeout": 300,
    "secret": dict(os.environ)["SECRET"],
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
    )
