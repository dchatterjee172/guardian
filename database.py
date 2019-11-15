import sqlite3
import bcrypt


def db_register(db, email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
    db.execute(
        f"""
        insert into user
        (
        email,
        password
        )
        values
        (
        "{email}",
        "{hashed}"
        )
        """
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
        create table activity_options
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
        create table activities
        (
        duration int not null,
        date datetime not null,
        activity_options_id,
        foreign key(activity_options_id) references
            activity_options(id)
        )
        """
    )
    conn.commit()
    conn.close()
