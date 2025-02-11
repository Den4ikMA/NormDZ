import sqlite3

def create_and_populate_db(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # --- Create tables ---

        # groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id_group INTEGER PRIMARY KEY,
                name_group TEXT UNIQUE
            )
        """)

        # disciplines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS disciplines (
                id_discipline INTEGER PRIMARY KEY,
                name_discipline TEXT UNIQUE
            )
        """)

        # groups_disciplines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Groups_Disciplines (
                id INTEGER PRIMARY KEY,
                id_group INTEGER,
                id_discipline INTEGER,
                FOREIGN KEY (id_group) REFERENCES Groups (id_group),
                FOREIGN KEY (id_discipline) REFERENCES Disciplines (id_discipline)
            )
        """)

        # prepods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prepods (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        # week table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS week (
                id INTEGER PRIMARY KEY,
                dow TEXT
            )
        """)

         # timing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timing (
                id INTEGER PRIMARY KEY,
                group_id INTEGER,
                prep_id INTEGER,
                disc_id INTEGER,
                dow_id INTEGER,
                time_start TEXT,
                time_end TEXT,
                FOREIGN KEY (group_id) REFERENCES groups(id_group),
                FOREIGN KEY (prep_id) REFERENCES prepods(id),
                FOREIGN KEY (disc_id) REFERENCES disciplines(id_discipline),
                FOREIGN KEY (dow_id) REFERENCES week(id)
            )
        """)

        # --- Populate tables ---

        # groups data
        groups = [
            ('12у',), ('21у',), ('12в',), ('21в',), ('11юп',), ('21юп',),
            ('11ю',), ('21ю',), ('11м',), ('22м',), ('12м',), ('21м',),
            ('11л',), ('21л',), ('11б',), ('21б',), ('11п',), ('21п',),
            ('11д',), ('21д',)
        ]
        cursor.executemany("INSERT OR IGNORE INTO groups (name_group) VALUES (?)", groups)

        # disciplines data
        disciplines = [
            ('Математика',), ('Физика',), ('Химия',), ('Физ-ра',), ('География',), ('ОсПси',), ('РиКУЛЬПР',), ('ОсПед',), ('Рус.яз',), ('Инф',), ('Ин. яз',), ('Обществ.',),('ИТП',),('РиК',), ('История',), ('ДОУ',), ('Гр. право',),
            ('Анатомия',), ('ЗОЖ',), ('Уход',), ('Латынь',), ('ОЛД',), ('ОФГ',), ('ОБУ',), ('ЭВМ',), ('ИТ',), ('ДисМат',), ('ТеорВер',), ('ОПС',), ('Рисунок',), ('АрхАпс',), ('Биология',), ('ВАФГ',), ('ТГП',), ('КП',), ('ОПодг',),
            ('БЖДО',), ('ЭкОрг',), ('НиН',), ('ФиК',), ('ОФГ',), ('ОБД',), ('Живопись',), ('ИД',), ('Литература',), ('РиКП',), ('ЛОП',), ('ДП',), ('Генетика',), ('ОБОС',),
        ]
        cursor.executemany("INSERT OR IGNORE INTO disciplines (name_discipline) VALUES (?)", disciplines)

         # prepods data
        prepods = [
            ('Иванов И.И.',), ('Петров П.П.',), ('Сидоров С.С.',)
        ]
        cursor.executemany("INSERT OR IGNORE INTO prepods (name) VALUES (?)", prepods)

        # week data
        week = [
            ('Понедельник',), ('Вторник',), ('Среда',), ('Четверг',), ('Пятница',)
        ]
        cursor.executemany("INSERT OR IGNORE INTO week (dow) VALUES (?)", week)


        # --- Create relationships between groups and disciplines ---
        # You'll need to query the database to get the IDs of the groups and disciplines
        # and then insert them into the Groups_Disciplines table.

        # Example: Associate "12у" with "Математика"
        cursor.execute("SELECT id_group FROM groups WHERE name_group = '12у'")
        group_id = cursor.fetchone()[0]

        cursor.execute("SELECT id_discipline FROM disciplines WHERE name_discipline = 'Математика'")
        discipline_id = cursor.fetchone()[0]


        cursor.execute("INSERT OR IGNORE INTO Groups_Disciplines (id_group, id_discipline) VALUES (?, ?)", (group_id, discipline_id))

         # Example: Associate "21у" with "Физика"
        cursor.execute("SELECT id_group FROM groups WHERE name_group = '21у'")
        group_id = cursor.fetchone()[0]

        cursor.execute("SELECT id_discipline FROM disciplines WHERE name_discipline = 'Физика'")
        discipline_id = cursor.fetchone()[0]


        cursor.execute("INSERT OR IGNORE INTO Groups_Disciplines (id_group, id_discipline) VALUES (?, ?)", (group_id, discipline_id))

        #Timing data
        # Example timing data - Adjust these as needed
        timing_data = [
            (1, 1, 1, 1, '9:00', '10:30'),  # group_id, prep_id, disc_id, dow_id
            (2, 2, 2, 2, '11:00', '12:30'),
            (3, 1, 3, 3, '13:00', '14:30'),
        ]
        cursor.executemany("INSERT OR IGNORE INTO timing (group_id, prep_id, disc_id, dow_id, time_start, time_end) VALUES (?, ?, ?, ?, ?, ?)", timing_data)

        conn.commit()
        print("Database created and populated successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_file = 'schedule.db'  # Specify the database file name here
    create_and_populate_db(db_file)
