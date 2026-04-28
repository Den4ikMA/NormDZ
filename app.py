import sqlite3
import hashlib
from typing import List, Dict, Optional

DB_NAME = "freelance_board.db"  # ✅ ФИКС: простой путь

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('client', 'freelancer', 'admin')) NOT NULL DEFAULT 'client',
        balance REAL DEFAULT 0.0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        budget REAL DEFAULT 0.0,
        client_id INTEGER,
        freelancer_id INTEGER,
        status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'completed', 'paid')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(client_id) REFERENCES Users(id),
        FOREIGN KEY(freelancer_id) REFERENCES Users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL,
        method TEXT, status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER,
        client_id INTEGER, freelancer_id INTEGER, amount REAL,
        method TEXT, status TEXT DEFAULT 'pending'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
        
    # ✅ УБРАЛ ДУБЛИКАТ Bids
    c.execute('''CREATE TABLE IF NOT EXISTS Bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        freelancer_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        message TEXT,  
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("✅ БД готова!")

# Остальные функции БЕЗ ИЗМЕНЕНИЙ (твои оригинальные)...
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, email: str, password: str, role: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                      (username, email, hash_password(password), role))
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
    cursor.execute("SELECT id, username, email, role, balance FROM Users WHERE username = ? AND password_hash = ?", (username, h))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "email": row[2], "role": row[3], "balance": row[4]}
    return None

# 📋 Задачи
def create_task(client_id: int, title: str, description: str, category: str, budget: float) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Tasks (title, description, category, budget, client_id, status) VALUES (?, ?, ?, ?, ?, 'open')",
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
    cursor.execute("""
        SELECT t.*, u.username AS client_name 
        FROM Tasks t JOIN Users u ON t.client_id = u.id 
        ORDER BY t.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 💰 Ставки
def create_bid(task_id: int, freelancer_id: int, amount: float, message: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Bids (task_id, freelancer_id, amount, message) VALUES (?, ?, ?, ?)",
        (task_id, freelancer_id, amount, message or ""),
    )
    bid_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return bid_id

def get_bids_for_task(task_id: int) -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, u.username AS freelancer_name 
        FROM Bids b JOIN Users u ON b.freelancer_id = u.id 
        WHERE b.task_id = ? ORDER BY b.created_at DESC
    """, (task_id,))
    bids = []
    for row in cursor.fetchall():
        bids.append({
            'id': row[0], 'task_id': row[1], 'freelancer_id': row[2],
            'amount': row[3], 'message': row[4], 'freelancer_name': row[6]
        })
    conn.close()
    return bids

# 💬 Сообщения
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
    cursor.execute("""
        SELECT m.*, u1.username AS sender_name, u1.role AS sender_role,
               u2.username AS receiver_name 
        FROM Messages m 
        JOIN Users u1 ON m.sender_id = u1.id 
        JOIN Users u2 ON m.receiver_id = u2.id 
        WHERE m.task_id = ? ORDER BY m.created_at ASC
    """, (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 🏦 Финансы
def get_user_balance(user_id: int) -> float:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT balance FROM Users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return float(result[0]) if result else 0.0

def request_withdrawal(user_id: int, amount: float, method: str) -> str:
    if get_user_balance(user_id) < amount:
        return "❌ Недостаточно средств"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO Withdrawals (user_id, amount, method, status) VALUES (?, ?, ?, "success")', 
              (user_id, amount, method))
    c.execute('UPDATE Users SET balance = balance - ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    return f"✅ Вывод {amount}₽ на {method} успешен!"

def process_payment(task_id: int, amount: float, method: str, client_id: int, freelancer_id: int) -> str:
    if get_user_balance(client_id) < amount:
        return "❌ Недостаточно средств у клиента"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO Payments (task_id, client_id, freelancer_id, amount, method, status) VALUES (?, ?, ?, ?, ?, "success")', 
              (task_id, client_id, freelancer_id, amount, method))
    c.execute('UPDATE Users SET balance = balance - ? WHERE id = ?', (amount, client_id))
    c.execute('UPDATE Users SET balance = balance + ? WHERE id = ?', (amount, freelancer_id))
    c.execute('UPDATE Tasks SET status = "paid" WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return f"✅ Оплата {amount}₽ прошла!"

# 📊 Статистика и личный кабинет
def get_user_tasks(user_id: int, role: str) -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if role == 'freelancer':
        c.execute('SELECT id, title, status, client_id FROM Tasks WHERE freelancer_id = ?', (user_id,))
    elif role == 'client':
        c.execute('SELECT id, title, status, freelancer_id FROM Tasks WHERE client_id = ?', (user_id,))
    else:
        conn.close()
        return []
    
    tasks = []
    for row in c.fetchall():
        task = {'id': row[0], 'title': row[1], 'status': row[2]}
        if len(row) > 3: 
            task['client_id' if role == 'freelancer' else 'freelancer_id'] = row[3]
        tasks.append(task)
    conn.close()
    return tasks

def get_admin_stats() -> Dict:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM Users'); users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM Tasks'); tasks = c.fetchone()[0]
    c.execute('SELECT SUM(balance) FROM Users'); total = c.fetchone()[0] or 0
    conn.close()
    return {'users': users, 'tasks': tasks, 'total_balance': total}

# ⭐ Рейтинги (упрощенные)
def create_rating(task_id: int, client_id: int, freelancer_id: int, score: int, comment: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Ratings (task_id, client_id, freelancer_id, score, comment) VALUES (?, ?, ?, ?, ?)",
            (task_id, client_id, freelancer_id, score, comment),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_average_rating(user_id: int) -> float:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(score) FROM Ratings WHERE freelancer_id = ?", (user_id,))
    avg = cursor.fetchone()[0]
    conn.close()
    return round(float(avg) if avg else 0.0, 1)

def top_categories(limit: int = 10) -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, COUNT(*) AS task_count
        FROM Tasks WHERE category IS NOT NULL
        GROUP BY category ORDER BY task_count DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_balance(user_id: int, amount: float) -> str:
    if amount <= 0:
        return "❌ Сумма должна быть больше 0."
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE Users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return f"✅ Баланс пополнен на {amount:.2f}₽."
