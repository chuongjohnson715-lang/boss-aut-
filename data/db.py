import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "boss.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            position TEXT,
            education TEXT,
            school TEXT,
            major TEXT,
            gender TEXT,
            status TEXT DEFAULT 'pending',
            message1_sent INTEGER DEFAULT 0,
            resume_received INTEGER DEFAULT 0,
            message2_sent INTEGER DEFAULT 0,
            qualified INTEGER DEFAULT 0,
            pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
def _column_exists(conn, table, column):
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(col[1] == column for col in cols)


def _add_column(conn, table, column, definition):
    if not _column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_extensions():
    """在旧版 init_db() 基础上补充新表和兼容字段。"""
    conn = get_connection()

    _add_column(conn, "candidates", "school_type", "TEXT DEFAULT ''")
    _add_column(conn, "candidates", "source", "TEXT DEFAULT ''")
    _add_column(conn, "candidates", "remark", "TEXT DEFAULT ''")
    _add_column(conn, "candidates", "last_error", "TEXT DEFAULT ''")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS automation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()


def is_contacted(name, position):
    """判断候选人是否已联系过（已发送过常用语1）。

    用于「遍历候选人并筛选未回复的候选人」：重复运行时跳过
    数据库中已经发过常用语1 的候选人，避免重复骚扰。
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT message1_sent FROM candidates WHERE name = ? AND position = ?",
            (name or "", position or "")
        ).fetchone()
    finally:
        conn.close()
    return bool(row) and bool(row[0])


def add_log(level, message):
    conn = get_connection()
    conn.execute(
        "INSERT INTO automation_logs(level, message) VALUES (?, ?)",
        (level, message)
    )
    conn.commit()
    conn.close()


def upsert_candidate(
    name=None,
    position=None,
    education=None,
    school=None,
    major=None,
    gender=None,
    status="pending",
    message1_sent=0,
    resume_received=0,
    message2_sent=0,
    qualified=0,
    pinned=0,
    school_type="",
    source="",
    remark="",
    last_error=""
):
    """按姓名 + 岗位 简单去重；若已存在则更新。"""
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    existing = conn.execute(
        "SELECT id FROM candidates WHERE name = ? AND position = ?",
        (name or "", position or "")
    ).fetchone()

    if existing:
        conn.execute("""
            UPDATE candidates SET
                education = COALESCE(?, education),
                school = COALESCE(?, school),
                major = COALESCE(?, major),
                gender = COALESCE(?, gender),
                status = ?,
                message1_sent = MAX(message1_sent, ?),
                resume_received = MAX(resume_received, ?),
                message2_sent = MAX(message2_sent, ?),
                qualified = MAX(qualified, ?),
                pinned = MAX(pinned, ?),
                school_type = COALESCE(?, school_type),
                source = COALESCE(?, source),
                remark = COALESCE(?, remark),
                last_error = COALESCE(?, last_error),
                updated_at = ?
            WHERE id = ?
        """, (
            education, school, major, gender, status,
            message1_sent, resume_received, message2_sent, qualified, pinned,
            school_type, source, remark, last_error, now, existing[0]
        ))
    else:
        conn.execute("""
            INSERT INTO candidates(
                name, position, education, school, major, gender, status,
                message1_sent, resume_received, message2_sent, qualified, pinned,
                school_type, source, remark, last_error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name or "", position or "", education or "", school or "",
            major or "", gender or "", status,
            int(message1_sent or 0), int(resume_received or 0),
            int(message2_sent or 0), int(qualified or 0), int(pinned or 0),
            school_type or "", source or "", remark or "", last_error or "",
            now, now
        ))

    conn.commit()
    conn.close()


def update_candidate_status(candidate_id, status, **fields):
    conn = get_connection()
    sets = ["status = ?", "updated_at = ?"]
    values = [status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    for key, value in fields.items():
        sets.append(f"{key} = ?")
        values.append(value)
    values.append(candidate_id)
    conn.execute(
        f"UPDATE candidates SET {', '.join(sets)} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    init_extensions()
    print("数据库初始化完成")
    print(DB_PATH)
