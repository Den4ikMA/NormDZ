import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional


DB_NAME = r"C:\\фриланс\\freelance_board.db"


# --- 1. init_db() должна быть ВНУТРИ этого файла ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('client', 'freelancer')) NOT NULL,
        balance REAL DEFAULT 0.0
    );

    CREATE TABLE IF NOT EXISTS Tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        budget REAL NOT NULL,
        status TEXT CHECK(status IN ('open', 'in_progress', 'done', 'cancelled')) DEFAULT 'open',
        client_id INTEGER NOT NULL,
        contractor_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Users(id),
        FOREIGN KEY (contractor_id) REFERENCES Users(id)
    );

    CREATE TABLE IF NOT EXISTS Bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        freelancer_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES Tasks(id),
        FOREIGN KEY (freelancer_id) REFERENCES Users(id)
    );

    CREATE TABLE IF NOT EXISTS Messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES Tasks(id),
        FOREIGN KEY (sender_id) REFERENCES Users(id),
        FOREIGN KEY (receiver_id) REFERENCES Users(id)
    );

    CREATE TABLE IF NOT EXISTS Ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        contractor_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        score INTEGER CHECK(score BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES Tasks(id),
        FOREIGN KEY (contractor_id) REFERENCES Users(id),
        FOREIGN KEY (client_id) REFERENCES Users(id),
        UNIQUE(task_id)
    );

    CREATE TABLE IF NOT EXISTS Payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        contractor_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        status TEXT CHECK(status IN ('pending', 'frozen', 'paid', 'refunded')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES Tasks(id),
        FOREIGN KEY (client_id) REFERENCES Users(id),
        FOREIGN KEY (contractor_id) REFERENCES Users(id)
    );
    """)
    conn.commit()
    conn.close()


# --- 2. Остальные функции (create_user, auth_user и т.д.) ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, email: str, password: str, role: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO Users (username, email, password_hash, role)"
            " VALUES (?, ?, ?, ?)",
            (username, email, hash_password(password), role),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True


def auth_user(username: str, password: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    h = hash_password(password)
    cursor.execute(
        "SELECT id, username, email, role, balance FROM Users WHERE username = ? AND password_hash = ?",
        (username, h),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "role": row[3],
            "balance": row[4],
        }
    return None


def create_task(client_id: int, title: str, description: str, category: str, budget: float) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Tasks (title, description, category, budget, client_id)"
        " VALUES (?, ?, ?, ?, ?)",
        (title, description, category, budget, client_id),
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_tasks() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""SELECT t.*, u.username AS client_name FROM Tasks t
                      JOIN Users u ON t.client_id = u.id
                      ORDER BY t.created_at DESC""")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_bid(task_id: int, freelancer_id: int, amount: float, message: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Bids (task_id, freelancer_id, amount, message) VALUES (?, ?, ?, ?)",
        (task_id, freelancer_id, amount, message),
    )
    bid_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return bid_id


def get_bids_for_task(task_id: int) -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""SELECT b.*, u.username AS freelancer_name FROM Bids b
                      JOIN Users u ON b.freelancer_id = u.id
                      WHERE b.task_id = ?
                      ORDER BY b.amount ASC""", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def accept_bid(task_id: int, bid_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""SELECT b.freelancer_id, b.amount, t.budget
                      FROM Bids b
                      JOIN Tasks t ON b.task_id = t.id
                      WHERE b.id = ?""", (bid_id,))
    row = cursor.fetchone()
    if not row or row[1] > row[2]:
        conn.close()
        return False

    freelancer_id, amount, budget = row
    cursor.execute("UPDATE Tasks SET contractor_id = ?, status = 'in_progress' WHERE id = ?", (freelancer_id, task_id))
    cursor.execute(
        """INSERT INTO Payments (task_id, client_id, contractor_id, amount, status)
           SELECT ?, t.client_id, ?, ?, 'frozen' FROM Tasks t WHERE t.id = ?""",
        (task_id, freelancer_id, amount, task_id),
    )
    conn.commit()
    conn.close()
    return True


def create_message(task_id: int, sender_id: int, receiver_id: int, content: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Messages (task_id, sender_id, receiver_id, content) VALUES (?, ?, ?, ?)",
        (task_id, sender_id, receiver_id, content),
    )
    conn.commit()
    conn.close()


def get_messages(task_id: int) -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""SELECT m.*, u1.username AS sender_name, u2.username AS receiver_name
                      FROM Messages m
                      JOIN Users u1 ON m.sender_id = u1.id
                      JOIN Users u2 ON m.receiver_id = u2.id
                      WHERE m.task_id = ?
                      ORDER BY m.created_at ASC""", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_rating(task_id: int, client_id: int, contractor_id: int, score: int, comment: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO Ratings (task_id, contractor_id, client_id, score, comment)
               VALUES (?, ?, ?, ?, ?)""",
            (task_id, contractor_id, client_id, score, comment),
        )
        cursor.execute(
            "UPDATE Payments SET status = 'paid' WHERE task_id = ? AND status = 'frozen'",
            (task_id,),
        )
        cursor.execute(
            "UPDATE Tasks SET status = 'done' WHERE id = ?",
            (task_id,),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True


def get_average_rating(user_id: int) -> float:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT AVG(score) FROM Ratings WHERE contractor_id = ?",
        (user_id,),
    )
    avg = cursor.fetchone()[0]
    conn.close()
    return avg or 0.0


def top_categories(limit: int = 10) -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""SELECT category, COUNT(*) AS task_count
                      FROM Tasks
                      GROUP BY category
                      ORDER BY task_count DESC
                      LIMIT ?""", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# --- УБРАНО: CLI-блок main() и if __name__ == "__main__" под Streamlit
# Оставь пустым или закомментируй, если хочешь:
"""
def main():
    init_db()
    # твой CLI-интерфейс здесь
    ...

if __name__ == "__main__":
    main()
"""
