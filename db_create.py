import sqlite3

DB_NAME = "marketplace.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("PRAGMA foreign_keys = ON;")

    c.execute('''CREATE TABLE IF NOT EXISTS Categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Manufacturers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS PickupPoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        postal_code TEXT NOT NULL,
        city TEXT NOT NULL DEFAULT 'г. Лесной',
        street TEXT NOT NULL,
        house TEXT NOT NULL,
        UNIQUE(postal_code, street, house) -- Обеспечение уникальности каждого ПВЗ
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fio TEXT NOT NULL,
        login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT CHECK(role IN ('администратор', 'менеджер', 'клиент')) NOT NULL DEFAULT 'клиент'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Products (
        article TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        discount REAL DEFAULT 0.0 CHECK(discount >= 0 AND discount <= 100),
        stock_quantity INTEGER DEFAULT 0 CHECK(stock_quantity >= 0),
        description TEXT,
        photo_path TEXT,
        category_id INTEGER,
        manufacturer_id INTEGER,
        supplier_id INTEGER,
        FOREIGN KEY(category_id) REFERENCES Categories(id) ON DELETE SET NULL,
        FOREIGN KEY(manufacturer_id) REFERENCES Manufacturers(id) ON DELETE SET NULL,
        FOREIGN KEY(supplier_id) REFERENCES Suppliers(id) ON DELETE SET NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Orders (
        order_number TEXT PRIMARY KEY,        -- Уникальный номер заказа
        user_id INTEGER NOT NULL,             -- Ссылка на покупателя/пользователя
        pvz_id INTEGER NOT NULL,              -- Ссылка на ПВЗ (адрес в виде ID)
        pickup_code TEXT NOT NULL,            -- Код для получения
        status TEXT NOT NULL,                 -- Статус заказа
        order_date TEXT NOT NULL,             -- Дата заказа
        delivery_date TEXT,                   -- Дата доставки
        FOREIGN KEY(user_id) REFERENCES Users(id) ON DELETE RESTRICT,
        FOREIGN KEY(pvz_id) REFERENCES PickupPoints(id) ON DELETE RESTRICT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS OrderItems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT NOT NULL,           -- Связь с таблицей Orders
        article TEXT NOT NULL,                -- Связь с таблицей Products
        quantity INTEGER NOT NULL CHECK(quantity > 0), -- Количество товара (чистый INTEGER)
        FOREIGN KEY(order_number) REFERENCES Orders(order_number) ON DELETE CASCADE,
        FOREIGN KEY(article) REFERENCES Products(article) ON DELETE RESTRICT
    )''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
