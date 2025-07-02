import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    """Создаёт новое подключение к БД"""
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализирует БД (вызывается при старте)"""
    db = get_db()
    try:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """)
        
        try:
            db.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", pwd_context.hash("admin123"), "admin")
            )
            db.commit()
        except sqlite3.IntegrityError:
            pass
    finally:
        db.close()

init_db()  # Вызываем при импорте