import sqlite3
import bcrypt


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
    action_ids = db.execute(
        """
        select id from activities
        where activity in ?
        """,
        actions,
    )


if __name__ == "__main__":
    conn = sqlite3.connect("main.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(
        """
        create table user
        (
        id integer primary key autoincrement not null,
        email text not null unique,
        password text not null unique
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
        constraint unq unique (user_id, activity)
        )
        """
    )
    c.execute(
        """
        create table actions
        (
        duration int not null,
        date datetime not null,
        activity_id,
        foreign key(activity_id) references
            activities(id)
        )
        """
    )
    conn.commit()
    conn.close()
