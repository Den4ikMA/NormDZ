import sqlite3
import os

# Названия файлов
DB_NAME = "database.db"
SCHEMA_NAME = "schema.sql"


def create_database()
    if not os.path.exists(SCHEMA_NAME):
        print(f"Ошибка: Файл схемы '{SCHEMA_NAME}' не найден!")
        return

    try:
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

       
        with open(SCHEMA_NAME, "r", encoding="utf-8") as f:
            sql_script = f.read()

        
        cursor.executescript(sql_script)

       
        conn.commit()
        print(
            f"Успех: База данных '{DB_NAME}' успешно создана на основе '{SCHEMA_NAME}'."
        )

    except sqlite3.Error as e:
        print(f"Ошибка при работе с SQLite: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_database()
