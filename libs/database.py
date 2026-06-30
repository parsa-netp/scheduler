import sqlite3
import os
from datetime import date, datetime

DB_DIR = "settings"
DB_FILE = os.path.join(DB_DIR, "scheduler.db")


def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    
    cursor = conn.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]

    if version == 0:
        # Check if this is a fresh install or an upgrade from the unversioned schema
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        has_tables = cursor.fetchone() is not None

        if not has_tables:
            # Fresh install
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_dt TEXT NOT NULL,
                    end_dt TEXT NOT NULL,
                    icon TEXT DEFAULT 'EVENT',
                    color TEXT DEFAULT 'BLUE_700',
                    description TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    color TEXT NOT NULL DEFAULT 'GREY_700',
                    pinned INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    reminder_dt TEXT NOT NULL,
                    color TEXT DEFAULT 'AMBER_700',
                    all_day INTEGER DEFAULT 0
                )
            """)
        else:
            # Upgrade from unversioned schema - run safe alter statements one last time
            try: conn.execute("ALTER TABLE notes ADD COLUMN title TEXT NOT NULL DEFAULT ''")
            except Exception: pass
            try: conn.execute("ALTER TABLE notes ADD COLUMN color TEXT NOT NULL DEFAULT 'GREY_700'")
            except Exception: pass
            try: conn.execute("ALTER TABLE notes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
            except Exception: pass
            try: conn.execute("ALTER TABLE notes ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
            except Exception: pass
            try: conn.execute("ALTER TABLE notes ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
            except Exception: pass
            try: conn.execute("ALTER TABLE events ADD COLUMN description TEXT NOT NULL DEFAULT ''")
            except Exception: pass
            try: conn.execute("ALTER TABLE reminders ADD COLUMN all_day INTEGER NOT NULL DEFAULT 0")
            except Exception: pass

        conn.execute("PRAGMA user_version = 1")
    
    # Future migrations will look like:
    # if version == 1:
    #     conn.execute("ALTER TABLE ...")
    #     conn.execute("PRAGMA user_version = 2")

    conn.commit()
    conn.close()


def get_all_notes():
    conn = get_db()
    cursor = conn.execute("SELECT * FROM notes ORDER BY pinned DESC, updated_at DESC")
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes


def add_note(title="", content="", color="GREY_700"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO notes (title, content, color, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (title, content, color, now, now),
    )
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id


def get_note_by_id(note_id):
    conn = get_db()
    cursor = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_note(note_id, title=None, content=None, color=None, pinned=None):
    conn = get_db()
    fields = []
    values = []
    if title is not None:
        fields.append("title=?")
        values.append(title)
    if content is not None:
        fields.append("content=?")
        values.append(content)
    if color is not None:
        fields.append("color=?")
        values.append(color)
    if pinned is not None:
        fields.append("pinned=?")
        values.append(1 if pinned else 0)
    if fields:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields.append("updated_at=?")
        values.append(now)
        values.append(note_id)
        conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    conn.close()


def delete_note(note_id):
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()


def add_event(title, start_dt, end_dt, icon="EVENT", color="BLUE_700", description=""):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO events (title, start_dt, end_dt, icon, color, description) VALUES (?, ?, ?, ?, ?, ?)",
        (title, start_dt, end_dt, icon, color, description),
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id


def get_events_for_day(target_date: date):
    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM events WHERE start_dt LIKE ? ORDER BY start_dt",
        (target_date.strftime("%Y-%m-%d") + "%",),
    )
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events


def get_all_events():
    conn = get_db()
    cursor = conn.execute("SELECT * FROM events ORDER BY start_dt")
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events


def update_event(event_id: int, title: str, start_dt: str, end_dt: str, icon: str = "EVENT", color: str = "BLUE_700", description: str = ""):
    conn = get_db()
    conn.execute(
        "UPDATE events SET title=?, start_dt=?, end_dt=?, icon=?, color=?, description=? WHERE id=?",
        (title, start_dt, end_dt, icon, color, description, event_id),
    )
    conn.commit()
    conn.close()


def delete_event(event_id: int):
    conn = get_db()
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


def get_reminders_for_day(target_date: date):
    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM reminders WHERE reminder_dt LIKE ? ORDER BY reminder_dt",
        (target_date.strftime("%Y-%m-%d") + "%",),
    )
    reminders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reminders


def add_reminder(title, reminder_dt, color="AMBER_700", all_day=0):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO reminders (title, reminder_dt, color, all_day) VALUES (?, ?, ?, ?)",
        (title, reminder_dt, color, all_day),
    )
    conn.commit()
    reminder_id = cursor.lastrowid
    conn.close()
    return reminder_id


def delete_reminder(reminder_id: int):
    conn = get_db()
    conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


def update_reminder(reminder_id: int, title: str = None, reminder_dt: str = None, color: str = None, all_day: int = None):
    conn = get_db()
    fields = []
    values = []
    if title is not None:
        fields.append("title=?")
        values.append(title)
    if reminder_dt is not None:
        fields.append("reminder_dt=?")
        values.append(reminder_dt)
    if color is not None:
        fields.append("color=?")
        values.append(color)
    if all_day is not None:
        fields.append("all_day=?")
        values.append(all_day)
    if fields:
        values.append(reminder_id)
        conn.execute(f"UPDATE reminders SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    conn.close()