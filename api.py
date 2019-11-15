from bottle import run, request, ServerAdapter, Bottle
from bottle.ext import sqlite
from beaker.middleware import SessionMiddleware
from bottle_tools import fill_args
from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
import ssl

app = Bottle()


@app.route("/whoami", method="GET")
def whoami():
    try:
        username = current_user()
    except Exception:
        username = None
    return {"username": username}


@app.route("/login", method="POST")
@fill_args(coerce_types=True)
def login(name, password):
    if password == "123":
        session = beaker_session()
        session["username"] = name


@app.route("/logout", method="POST")
def logout():
    session = beaker_session()
    session.delete()


def beaker_session():
    return request.environ.get("beaker.session")


def current_user():
    session = beaker_session()
    username = session.get("username", None)
    if username is None:
        raise Exception("Unauthenticated user")
    return username


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
}

if __name__ == "__main__":
    plugin = sqlite.Plugin(dbfile="./main.db")
    app.install(plugin)
    session_app = SessionMiddleware(app, session_opts)
    run(app=session_app, host="0.0.0.0", port=443, server=SSLCherryPyServer, debug=True)
