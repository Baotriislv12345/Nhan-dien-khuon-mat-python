import sqlite3
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "attendance.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT    NOT NULL,
                date      TEXT    NOT NULL,
                time      TEXT    NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_name_date
            ON attendance (name, date)
            """
        )
        conn.commit()


def mark_attendance(name: str) -> tuple[bool, str]:
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
                (name, today, now),
            )
            conn.commit()
        return True, now
    except sqlite3.IntegrityError:
        return False, "đã điểm danh hôm nay"


def get_attendance(filter_date: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if filter_date:
            rows = conn.execute(
                "SELECT name, date, time FROM attendance WHERE date = ? ORDER BY time",
                (filter_date,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT name, date, time FROM attendance ORDER BY date DESC, time DESC"
            ).fetchall()
    return [dict(row) for row in rows]


def get_attendance_dates() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT date FROM attendance ORDER BY date DESC"
        ).fetchall()
    return [row["date"] for row in rows]


def get_attendance_names() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT name FROM attendance ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [row["name"] for row in rows]


def delete_attendance_by_names(names: list[str]) -> int:
    if not names:
        return 0

    placeholders = ",".join("?" for _ in names)
    with get_connection() as conn:
        cursor = conn.execute(
            f"DELETE FROM attendance WHERE name IN ({placeholders})",
            names,
        )
        conn.commit()
        return cursor.rowcount


def clear_attendance():
    with get_connection() as conn:
        conn.execute("DELETE FROM attendance")
        conn.commit()


init_db()
