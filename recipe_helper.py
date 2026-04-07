import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import textwrap

def wrap_text(text, width=120):
    """Разбивает текст на строки длиной ~width символов."""
    if not text:
        return ""
    return "\n".join(textwrap.wrap(text, width=width))

DB_PATH = "recipe.db"

NORMALIZE_MAP = {
    # яйца
    "яйца": "яйца",
    "яйцо": "яйца",
    "яичница": "яйца",
    "куриные яйца": "яйца",
    "куриные яйца сырой": "яйца",
    "перепелиные яйца": "яйца",
    "яйца перепелиные": "яйца",
    "яйца домашние": "яйца",
    "яйца куриные": "яйца",

    # молоко / молочные продукты
    "молоко": "молоко",
    "молоко домашнее": "молоко",
    "молоко коровье": "молоко",
    "молоко пастеризованное": "молоко",
    "молоко обезжиренное": "молоко",
    "молоко 2.5%": "молоко",
    "молоко 3.2%": "молоко",
    "сгущёнка": "сгущёнка",
    "сгущёнка варёная": "сгущёнка варёная",
    "сгущёнка варёнка": "сгущёнка варёная",
    "сгущёнка с сахаром": "сгущёнка",
    "сгущёнка без сахара": "сгущёнка",

    "сметана": "сметана",
    "сметана 15%": "сметана",
    "сметана 20%": "сметана",
    "сметана 25%": "сметана",
    "сметана 30%": "сметана",
    "сметана домашняя": "сметана",
    "сметана жирная": "сметана",
    "сметана нежирная": "сметана",

    "йогурт": "йогурт",
    "йогурт натуральный": "йогурт",
    "йогурт греческий": "йогурт",
    "йогурт с фруктами": "йогурт",

    "сливки": "сливки",
    "сливки 10%": "сливки",
    "сливки 20%": "сливки",
    "сливки 33%": "сливки",
    "сливки жирные": "сливки",
    "сливки для взбития": "сливки",

    # овощи / огурцы
    "огурцы": "огурцы",
    "огурцы свежие": "огурцы",
    "огурцы зелёные": "огурцы",
    "огурцы маленькие": "огурцы",
    "огурцы крупные": "огурцы",

    "огурцы солёные": "огурцы солёные",
    "солёные огурцы": "огурцы солёные",
    "сольные огурцы": "огурцы солёные",
    "огурцы маринованные": "огурцы маринованные",
    "маринованные огурцы": "огурцы маринованные",

    "помидоры": "помидоры",
    "помидоры свежие": "помидоры",
    "помидоры черри": "помидоры",
    "помидоры сорта «сливка»": "помидоры",
    "томаты": "помидоры",
    "томаты свежие": "помидоры",

    "картофель": "картофель",
    "картофель свежий": "картофель",
    "картошка": "картофель",
    "картофель варёный": "картофель",
    "картофель жареный": "картофель",

    "лук": "лук",
    "лук репчатый": "лук",
    "лук белый": "лук",
    "лук репка": "лук",
    "лук зелёный": "зелёный лук",
    "зелёный лук": "зелёный лук",
    "зелёный лук свежий": "зелёный лук",

    "морковь": "морковь",
    "морковь свежая": "морковь",
    "морковь молодая": "морковь",

    "свёкла": "свёкла",
    "свёкла свежая": "свёкла",
    "свёкла варёная": "свёкла",

    "капуста": "капуста",
    "капуста белокочанная": "капуста",
    "капуста свежая": "капуста",

    "болгарский перец": "болгарский перец",
    "болгарский перец красный": "болгарский перец",
    "болгарский перец жёлтый": "болгарский перец",
    "болгарский перец зелёный": "болгарский перец",
    "перец": "болгарский перец",

    "грибы": "грибы",
    "шампиньоны": "грибы шампиньоны",
    "грибы шампиньоны": "грибы шампиньоны",
    "лисички": "грибы лисички",
    "грибы лисички": "грибы лисички",
    "боровики": "грибы боровики",
    "грибы боровики": "грибы боровики",
    "опята": "грибы опята",
    "грибы опята": "грибы опята",
    "вешенки": "грибы вешенки",
    "грибы вешенки": "грибы вешенки",

    # крупы
    "рис": "рис",
    "рис длиннозерный": "рис",
    "рис круглозерный": "рис",
    "рис басмати": "рис",
    "рис арборио": "рис",

    "гречка": "гречка",
    "греча": "гречка",
    "гречка ядрица": "гречка",
    "гречка быстрого приготовления": "гречка",

    "кукурузная крупа": "кукурузная крупа",
    "кукурузная каша": "кукурузная крупа",
    "кукурузная каша мелкая": "кукурузная крупа",

    "фасоль": "фасоль",
    "фасоль консервированная": "фасоль консервированная",
    "фасоль в банке": "фасоль консервированная",
    "фасоль красная": "фасоль",

    # мясо
    "курица": "курица",
    "курица филе": "курица",
    "куриное филе": "курица",
    "курица грудка": "курица",
    "курица ножка": "курица",

    "индейка": "индейка",
    "филе индейки": "индейка",
    "индейка замороженная": "индейка",
    "индейка свежая": "индейка",

    "свинина": "свинина",
    "свиная вырезка": "свинина",
    "свинина отварная": "свинина",
    "свинина жареная": "свинина",

    "говядина": "говядина",
    "говяжья вырезка": "говядина",
    "говядина фарш": "говядина",
    "говяжий фарш": "говядина",

    "фарш": "фарш",
    "куриный фарш": "куриный фарш",
    "микс фарш": "микс фарш",

    "бекон": "бекон",
    "бекон французский": "бекон",
    "бекон сырокопчёный": "бекон",

    "рыба": "рыба",
    "рыба свежая": "рыба",
    "рыба замороженная": "рыба",
    "рыба филе": "рыба",
    "рыба горбуша": "рыба",
    "рыба окунь": "рыба",

    # макароны
    "макароны": "макароны",
    "спагетти": "макароны",
    "вермишель": "макароны",
    "лапша": "макароны",
    "лапша яичная": "макароны",
    "лапша домашняя": "макароны",

    # хлеб и мука
    "хлеб": "хлеб",
    "хлеб белый": "хлеб",
    "хлеб ржаной": "хлеб",
    "хлеб чёрный": "хлеб",
    "батон": "хлеб",
    "булка": "хлеб",

    "мука": "мука",
    "пшеничная мука": "мука",
    "мука 1 сорта": "мука",
    "мука 2 сорта": "мука",
    "мука высшего сорта": "мука",

    # фрукты
    "яблоко": "яблоки",
    "яблоко красное": "яблоки",
    "яблоко зелёное": "яблоки",
    "яблоки": "яблоки",
    "яблоки зелёные": "яблоки",
    "яблоки красные": "яблоки",

    "банан": "бананы",
    "бананы": "бананы",
    "банан крупный": "бананы",
    "банан мелкий": "бананы",

    "мёд": "мёд",
    "мёд липовый": "мёд",
    "мёд цветочный": "мёд",
    "мёд акациевый": "мёд",
    "мёд горный": "мёд",
    "мёд натуральный": "мёд",

    "сахар": "сахар",
    "сахарный песок": "сахар",
    "сахар белый": "сахар",
    "сахар-песок": "сахар",
    "сахар кристаллы": "сахар",

    "шоколад": "шоколад",
    "шоколад молочный": "шоколад",
    "шоколад горький": "шоколад",
    "тёмный шоколад": "шоколад",
    "белый шоколад": "шоколад",

    "корица": "корица",
    "молотая корица": "корица",
    "корица палочки": "корица",
}

def normalize_ingredient_name(name):
    name = name.strip().lower()
    return NORMALIZE_MAP.get(name, name)

# === 1. Инициализация БД ===
def setup_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS Ingredients (
        ingredient_id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS Recipes (
        recipe_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        instructions TEXT,
        time_min INTEGER,
        difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard'))
    );
    CREATE TABLE IF NOT EXISTS RecipeIngredients (
        recipe_id INTEGER,
        ingredient_id INTEGER,
        quantity TEXT,
        FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id) ON DELETE CASCADE,
        PRIMARY KEY (recipe_id, ingredient_id)
    );
    CREATE TABLE IF NOT EXISTS Pantry (
        user_id INTEGER,
        ingredient_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, ingredient_id)
    );
    CREATE TABLE IF NOT EXISTS Likes (
        user_id INTEGER,
        recipe_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, recipe_id)
    );
    """)
    conn.commit()
    conn.close()


# === 2. Заполнение холодильника (пользовательский ввод) ===
def load_pantry():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cur = conn.cursor()

    cur.execute("DELETE FROM Pantry WHERE user_id = 1")
    cur.execute("INSERT OR IGNORE INTO Users (user_id, username) VALUES (1, 'student')")
    conn.commit()

    text = entry_ingredients.get("1.0", "end-1c").strip()
    if not text:
        messagebox.showwarning("Ошибка", "Введите ингредиенты через запятую.")
        return

    ingredients = [i.strip() for i in text.split(",") if i.strip()]
    for raw_name in ingredients:
        norm_name = normalize_ingredient_name(raw_name)

        cur.execute("INSERT OR IGNORE INTO Ingredients (name) VALUES (?);", (norm_name,))
        cur.execute("SELECT ingredient_id FROM Ingredients WHERE name = ?", (norm_name,))
        row = cur.fetchone()
        if row:
            cur.execute("INSERT OR IGNORE INTO Pantry (user_id, ingredient_id) VALUES (1, ?)", (row[0],))

    conn.commit()
    conn.close()
    messagebox.showinfo("Готово", "Холодильник обновлён!\nНажмите 'Поиск'.")

def generate_weekly_menu():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cur = conn.cursor()

    # === 1. Проверяем, есть ли в холодильнике ингредиенты ===
    cur.execute("SELECT COUNT(*) FROM Pantry WHERE user_id = 1;")
    pantry_count = cur.fetchone()[0]

    recipes_for_week = []

    if pantry_count > 0:
        # есть ингредиенты → выбираем рецепты с совпадением >= 50%
        query = """
        WITH user_pantry AS (
            SELECT ingredient_id
            FROM Pantry
            WHERE user_id = 1
        ),
        recipe_ingredients_count AS (
            SELECT
                ri.recipe_id,
                COUNT(ri.ingredient_id) AS total_ingredients
            FROM RecipeIngredients ri
            GROUP BY ri.recipe_id
        ),
        matching_ingredients AS (
            SELECT
                ri.recipe_id,
                COUNT(ri.ingredient_id) AS matching_ingredients
            FROM RecipeIngredients ri
            JOIN user_pantry p ON p.ingredient_id = ri.ingredient_id
            GROUP BY ri.recipe_id
        ),
        coverage AS (
            SELECT
                r.recipe_id,
                r.name,
                r.time_min,
                COALESCE(m.matching_ingredients, 0) AS ok,
                c.total_ingredients
            FROM Recipes r
            JOIN recipe_ingredients_count c ON c.recipe_id = r.recipe_id
            LEFT JOIN matching_ingredients m ON m.recipe_id = r.recipe_id
        )
        SELECT DISTINCT
            recipe_id, name, time_min, ok, total_ingredients
        FROM coverage
        WHERE total_ingredients > 0 AND ok * 100.0 / total_ingredients >= 50.0
        ORDER BY RANDOM()
        LIMIT 100;
        """
        cur.execute(query)
        rows = cur.fetchall()

        # берём не более 7 разных рецептов
        selected = {}
        for row in rows:
            recipe_id = row[0]
            if recipe_id not in selected and len(selected) < 7:
                selected[recipe_id] = row
        recipes_for_week = list(selected.values())

    else:
        # холодильник пуст → просто 7 разных рецептов (без условий по %)
        cur.execute("""
            SELECT DISTINCT recipe_id, name, time_min, 0 AS ok, 0 AS total_ingredients
            FROM Recipes
            ORDER BY RANDOM()
            LIMIT 7;
        """)
        recipes_for_week = cur.fetchall()

    conn.close()

    # если вообще ничего не нашлось
    if not recipes_for_week:
        messagebox.showinfo("Меню на неделю", "Не нашлось рецептов.")
        return

    # === 2. Собираем список ингредиентов и покупок (как раньше) ===
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cur = conn.cursor()

    recipe_ids = [str(row[0]) for row in recipes_for_week]
    if not recipe_ids:
        conn.close()
        messagebox.showinfo("Меню на неделю", "Не нашлось рецептов.")
        return

    placeholders = ",".join("?" * len(recipe_ids))
    cur.execute(f"""
        SELECT ri.recipe_id, i.name, ri.quantity
        FROM RecipeIngredients ri
        JOIN Ingredients i ON i.ingredient_id = ri.ingredient_id
        WHERE ri.recipe_id IN ({placeholders})
        ORDER BY i.name
    """, recipe_ids)

    menu_ingredients = {}
    user_pantry_dict = set()

    # текущий холодильник
    cur.execute("""
        SELECT i.name
        FROM Pantry p
        JOIN Ingredients i ON p.ingredient_id = i.ingredient_id
        WHERE p.user_id = 1
    """)
    for (name,) in cur.fetchall():
        user_pantry_dict.add(name)

    for recipe_id, ing_name, qty in cur.fetchall():
        key = ing_name.lower()
        if key not in menu_ingredients:
            menu_ingredients[key] = {"name": ing_name, "qty": qty, "needed": True, "in_pantry": False}

        if ing_name in user_pantry_dict:
            menu_ingredients[key]["in_pantry"] = True
            menu_ingredients[key]["needed"] = False

    conn.close()

    # === 3. Формируем текст сообщения ===
    menu_text = "МЕНЮ НА НЕДЕЛЮ:\n\n"
    for i, (recipe_id, name, time_min, _, _) in enumerate(recipes_for_week):
        menu_text += f"{i+1}. {name} — {time_min} мин\n"

    shopping_list = "\nСПИСОК ПОКУПОК:\n"
    for key, data in menu_ingredients.items():
        if data["needed"]:
            shopping_list += f"- {data['name']} ({data['qty']})\n"

    if shopping_list == "\nСПИСОК ПОКУПОК:\n":
        shopping_list += "- Ничего дополнительно покупать не нужно.\n"

    messagebox.showinfo("Меню на неделю", menu_text + shopping_list)
    
# === 3. Поиск рецептов по ингредиентам (с процентом совпадения) ===
def search_recipes():
    tree.delete(*tree.get_children())

    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cur = conn.cursor()
    
# флаги для фильтров (можно завязать на Checkbox или Radiobutton)
    is_vegan = False
    is_gluten_free = False
    is_nut_free = False
    
    filter_parts = []

    if is_vegan:
        filter_parts.append("tags LIKE '%веган%'")

    if is_gluten_free:
        filter_parts.append("tags LIKE '%без глютена%'")

    if is_nut_free:
        filter_parts.append("tags LIKE '%без орехов%'")

    where_clause = ""
    if filter_parts:
        where_clause = "WHERE " + " AND ".join(filter_parts) + " AND "
    else:
        where_clause = "WHERE "
    
    query = """
    WITH user_pantry AS (
        SELECT ingredient_id
        FROM Pantry
        WHERE user_id = 1
    ),
    recipe_ingredients_count AS (
        SELECT
            ri.recipe_id,
            COUNT(ri.ingredient_id) AS total_ingredients
        FROM RecipeIngredients ri
        GROUP BY ri.recipe_id
    ),
    matching_ingredients AS (
        SELECT
            ri.recipe_id,
            COUNT(ri.ingredient_id) AS matching_ingredients
        FROM RecipeIngredients ri
        JOIN user_pantry p ON p.ingredient_id = ri.ingredient_id
        GROUP BY ri.recipe_id
    )
    SELECT
        r.recipe_id,
        r.name,
        r.time_min,
        r.difficulty,
        r.instructions,
        COALESCE(m.matching_ingredients, 0) AS ok,
        c.total_ingredients
    FROM Recipes r
    JOIN recipe_ingredients_count c ON c.recipe_id = r.recipe_id
    LEFT JOIN matching_ingredients m ON m.recipe_id = r.recipe_id
    WHERE COALESCE(m.matching_ingredients, 0) * 100.0 / c.total_ingredients >= 50.0
    ORDER BY (ok * 100.0 / c.total_ingredients) DESC;
    """

    try:
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            recipe_id, name, time_min, difficulty, instr, ok, total = row
            if total == 0:
                continue
            coverage = round(ok * 100.0 / total)
            wrapped_instr = wrap_text(instr, width=120)

            # Передаём те же values, но в нужном порядке под новый tree
            tree.insert(
                "",
                "end",
                values=(name, time_min, wrapped_instr),  # не нужно recipe_id и coverage в GUI
                tags=(recipe_id, coverage)  # если потом нужно использовать ID/percent где-то
            )
    except sqlite3.Error as e:
        conn.close()
        messagebox.showerror("Ошибка SQL", f"Запрос не выполнился:\n{str(e)}")


# === 4. GUI (Tkinter) ===
setup_db()  # вызов отсюда возможен, потому что setup_db объявлена выше

window = tk.Tk()
window.title("Рецепт‑помощник: что приготовить из того, что есть?")
window.geometry("1000x600")

tk.Label(window, text="Ингредиенты в холодильнике (через запятую):", font=("Arial", 12)).pack(pady=5)

entry_ingredients = tk.Text(window, height=3, font=("Arial", 12))
entry_ingredients.pack(padx=10, pady=5, fill="x")

btn_load = tk.Button(window, text="Загрузить холодильник", font=("Arial", 12), command=load_pantry)
btn_load.pack(pady=5)

btn_search = tk.Button(window, text="Поиск подходящих блюд", font=("Arial", 12), command=search_recipes)
btn_search.pack(pady=5)

btn_menu = tk.Button(window, text="Сформировать меню на неделю", font=("Arial", 12), command=generate_weekly_menu)
btn_menu.pack(pady=10)
columns = ("name", "time_min", "instructions")  # не нужно показывать ID и процент

tree = ttk.Treeview(window, columns=columns, show="headings", height=15)

tree.heading("name", text="Блюдо")
tree.column("name", width=200)

tree.heading("time_min", text="Время (мин)")
tree.column("time_min", width=80)

tree.heading("instructions", text="Рецепт")
tree.column("instructions", width=600)

scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(padx=10, pady=10, fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

window.mainloop()
