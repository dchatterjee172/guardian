import sqlite3

if __name__ == "__main__":
    conn = sqlite3.connect("example.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(
        """
        CREATE TABLE user
        (id integer primary key autoincrement not null,
        email text not null unique, password TEXT)
        """
    )
    c.execute(
        """
        CREATE TABLE activity_options
        (id integer primary key autoincrement not null,
        user_id integer not null,
        activity text not null,
        foreign key (user_id) references user(id),
        constraint unq unique (user_id, activity))
        """
    )
    c.execute(
        """
        CREATE TABLE activities
        (duration int not null,
        date datetime not null,
        activity_options_id,
        foreign key(activity_options_id) references
            activity_options(id))"""
    )
    conn.commit()
    conn.close()
