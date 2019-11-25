from bottle import run, request, ServerAdapter, Bottle, abort
from bottle_sqlite import SQLitePlugin
from beaker.middleware import SessionMiddleware
from cheroot import wsgi
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
from secrets import token_hex
from numpy import exp

app = Bottle()
using_timezone = "Asia/Calcutta"
chart_minute_scale_base = 2


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
        abort(401, "get out!")


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
    utc_offset = int(
        datetime.now(pytz.timezone(using_timezone)).utcoffset().total_seconds() / 60
    )

    timestamp_str = db_last_action_time(db, userid, utc_offset)
    now = datetime.now(pytz.timezone(using_timezone))
    if timestamp_str is None:
        delta = now - now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        timestamp = parser.parse(timestamp_str, default=now)
        delta = now - timestamp
    delta = delta.total_seconds() // 60
    return {"minutes_ago": int(delta)}


@app.route("/api_get_chart")
@login_required
def get_chart(db, userid):
    utc_offset = int(
        datetime.now(pytz.timezone(using_timezone)).utcoffset().total_seconds() / 60
    )
    df, df_groupby = db_get_action_current_day(db, userid, utc_offset)
    df["certainty"] = df["certainty"].apply(lambda x: exp(1 - x))
    df_groupby["certainty"] = df_groupby["certainty"].apply(lambda x: exp(1 - x))
    chart = alt.Chart(df_groupby)
    chart_activity_duarions = (
        chart.mark_bar(color="#202b38")
        .encode(
            y="activity",
            x=alt.X(
                "duration_minutes",
                scale=alt.Scale(type="log", base=chart_minute_scale_base),
            ),
        )
        .interactive()
    )
    chart_certainty = (
        chart.mark_bar(color="#202b38")
        .encode(y="activity", x="certainty")
        .interactive()
    )
    del chart, df_groupby
    chart = alt.Chart(df)
    chart_duarion_certainty = (
        chart.mark_circle()
        .encode(
            x="certainty",
            y=alt.Y(
                "duration_minutes",
                scale=alt.Scale(type="log", base=chart_minute_scale_base),
            ),
            color="activity",
            tooltip=("activity", "certainty", "duration_minutes"),
        )
        .interactive()
    )
    charts = alt.vconcat(
        chart_activity_duarions, chart_certainty, chart_duarion_certainty
    ).configure(background="white")
    html = StringIO()
    charts.save(html, "html")
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
    "session.secret": token_hex(20),
    "session.httponly": True,
}

if __name__ == "__main__":
    plugin = SQLitePlugin(dbfile="main.db")
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
