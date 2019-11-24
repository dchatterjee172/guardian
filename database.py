import bcrypt
import pandas as pd


def db_register(db, email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
    db.execute(
        """
        insert into user
        (
        email,
        password
        )
        values
        (?, ?)
        """,
        (email, hashed),
    )


def db_login(db, email, password):
    userid, truth = db.execute(
        """
        select id, password from user
        where email = ?
        """,
        (email,),
    ).fetchone()
    return userid, bcrypt.checkpw(password.encode(), truth.encode())


def db_get_activities(db, userid):
    activities = db.execute(
        """
        select activity from activities
        where user_id = ?
        """,
        (userid,),
    ).fetchall()
    for i in range(len(activities)):
        activities[i] = activities[i][0]
    return activities


def db_add_activities(db, userid, activities):
    counts = db.execute(
        """
        select count(activity)
        from activities
        where user_id = ?
        """,
        (userid,),
    ).fetchone()[0]
    if counts + len(activities) > 100:
        raise sqlite3.IntegrityError("too many activities!")
    db.executemany(
        """
        insert into activities
        (
        user_id,
        activity
        )
        values
        (?, ?)
        """,
        ((userid, activity) for activity in activities),
    )


def db_add_actions(db, userid, actions):
    cursor = db.cursor()
    activities_ids = []
    for activity in actions.keys():
        activities_ids.append(
            cursor.execute(
                """
            select id from activities
            where activity=? and user_id=?
            """,
                (activity, userid),
            ).fetchone()[0]
        )
    db.executemany(
        """
        insert into actions
        (
        activity_id,
        duration_minutes,
        actions_logged_together
        )
        values
        (?, ?, ?)
        """,
        (
            (activities_id, duration_minutes, len(actions))
            for activities_id, duration_minutes in zip(activities_ids, actions.values())
        ),
    )


def db_last_action_time(db, userid, utc_offset):
    utc_offset = f"{utc_offset} minutes"
    time = db.execute(
        """
        select datetime(timestamp, ?)
        from actions inner join activities
        on actions.activity_id = activities.id
        where activities.user_id = ? and
        date(timestamp, ?) == date('now', ?)
        order by timestamp desc
        limit 1
        """,
        (utc_offset, userid, utc_offset, utc_offset),
    ).fetchone()
    if time is None:
        pass
    else:
        time = time[0]
    return time


def db_get_action_current_day(db, userid, utc_offset):
    utc_offset = f"{utc_offset} minutes"
    query = """
                select activity, sum(duration_minutes) as duration_minutes
                from actions inner join activities
                on actions.activity_id = activities.id
                where
                activities.user_id = ?
                and
                date(timestamp, ?) == date('now', ?)
                group by activity;
            """
    df = pd.read_sql_query(query, db, params=(userid, utc_offset, utc_offset))
    return df


if __name__ == "__main__":
    import sqlite3
    from pathlib import Path
    import sys

    path = Path("./main.db")
    if path.is_file():
        print("db exists!")
        sys.exit(0)
    conn = sqlite3.connect("main.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(
        """
        create table user
        (
        id integer primary key autoincrement not null,
        email text not null unique,
        password text not null unique,
        check(length(email) < 100)
        )
        """
    )
    c.execute(
        """
        create table activities
        (
        id integer primary key autoincrement not null,
        user_id integer not null,
        activity text not null,
        foreign key (user_id) references user(id),
        constraint unq unique (user_id, activity),
        check(length(activity) < 100)
        )
        """
    )
    c.execute(
        """
        create table actions
        (
        duration_minutes int not null,
        timestamp datetime default current_timestamp,
        activity_id int not null,
        actions_logged_together int not null,
        foreign key(activity_id) references
            activities(id),
        check(duration_minutes > 0)
        )
        """
    )
    conn.commit()
    conn.close()
