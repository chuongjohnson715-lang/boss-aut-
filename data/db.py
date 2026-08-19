import sqlite3
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
    print(DB_PATH)