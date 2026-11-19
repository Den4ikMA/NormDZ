import streamlit as st
import sqlite3
import os
from st_keyup import st_keyup
from datetime import date, timedelta
import random


st.set_page_config(layout="wide")

@st.cache_resource
def db_connection():
    conn = sqlite3.connect('database_primer.db', check_same_thread=False)
    conn.row_factory=sqlite3.Row
    return conn

conn = db_connection()
cursor = conn.cursor()

DOSTYP = {
    "Гость": ["view_tovars"],
    "авторизированный кдиент": ["view_tovars"],
    "менеджер": ["view_tovars", "view_orders", "filt_tovars","sort_tovar", "search_tovars"],
    "администратор": ["view_tovars", "search_tovars", "view_orders", "edit_orders", "filt_tovars", "sort_tovar", "edit_tovar"]
    }

if "page" not in st.session_state:
    st.session_state.page = "catalog"

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Авторизация")

    login = st.text_input("Ваш логин:")
    password = st.text_input("Ваш пароль:", type="password")

    if st.button("вход"):
        vhod = """
        SELECT users.name, user_roles.role
        FROM users
        INNER JOIN user_roles ON users.role_id = user_roles.id
        WHERE users.login = ? AND users.password = ?
        """
        cursor.execute(vhod,(login, password))
        user = cursor.fetchone()
        
        if user is not None:
            st.session_state.logged_in = True
            st.session_state.user_name = user['name']
            st.session_state.user_role = user['role']
            st.session_state.page = "catalog"
            st.rerun()
        else:
            st.write("неверный логин или пароль")

    if st.button("войти как гость"):
        st.session_state.logged_in = True
        st.session_state.user_name = ""
        st.session_state.user_role = "Гость"
        st.session_state.page = "catalog"
        st.rerun()
        
else:
    st.subheader(f"Добро пожаловать, {st.session_state.user_role}  {st.session_state.user_name}")
    st.write("--------")

   
    def has_permissions(action):
        current_role = st.session_state.get("user_role")
        allowed_actions = DOSTYP.get(current_role, [])
        return action in allowed_actions

    
    if st.session_state.page == "catalog":
        
    
        if has_permissions("view_orders"):
            if st.button("Перейти к заказам"):
                st.session_state.page = "orders"
                st.rerun()

        st.title("Каталог товаров")

        sort = "tovar.name ASC"

        filt = ""

        if has_permissions("filt_tovars"):
            take = st.selectbox("фильтр:", ["ВСЕ","SVМЕБЕЛЬ", "Мебелони", "Инвуд", "RIDBERG"])

            if take == "ВСЕ":
                filt = ""
            elif take == "SVМЕБЕЛЬ":
                filt = " AND manufacturer.name = 'SVМЕБЕЛЬ'"
            elif take == "Мебелони":
                filt = " AND manufacturer.name = 'Мебелони'"
            elif take == "Инвуд":
                filt = " AND manufacturer.name = 'Инвуд'"
            else:
                filt = " AND manufacturer.name = 'RIDBERG'"
        

        if has_permissions("sort_tovar"):
            vybor = st.selectbox("Сортировать по:", ["алфавиту", "цене(по уменьшению)", "цене(по возрастанию)", "количеству на складе(по уменьшению)", "количеству на складе(по возрастанию)"])

            if vybor == "цене(по возрастанию)":
                sort = "tovar.price ASC"
            elif vybor == "цене(по уменьшению)":
                sort = "tovar.price DESC"
            elif vybor == "количеству на складе(по уменьшению)":
                sort = "tovar.quantity DESC"
            elif vybor == "количеству на складе(по возрастанию)":
                sort = "tovar.quantity ASC"
            else:
                sort = "tovar.name ASC"
                
        poisk = "WHERE tovar.vid = 1"
        params = []

        if has_permissions("search_tovars"):
            search = st_keyup("Поиск товара", debounce=300)
            if search:
                poisk = """
                WHERE tovar.vid = 1
                AND (LOWER(tovar.name) LIKE LOWER(?) OR LOWER(category.name) LIKE LOWER(?))
                """
                params = [f"%{search}%", f"%{search}%"]
                
        tovars = f"""
        SELECT
        tovar.id,
        tovar.name,
        tovar.discription,
        tovar.price,
        tovar.discount,
        tovar.supplier_id,
        tovar.manufacturer_id,
        tovar.quantity,
        tovar.photo,
        tovar.category_id,
        category.name AS category_name,
        supplier.name AS supplier_name,
        manufacturer.name AS manufacturer_name
        FROM tovar
        INNER JOIN category ON tovar.category_id = category.id
        INNER JOIN supplier ON tovar.supplier_id = supplier.id
        INNER JOIN manufacturer ON tovar.manufacturer_id = manufacturer.id
        {poisk}
        {filt}
        ORDER BY {sort}
        """
        cursor.execute(tovars, params)
        all_tovars = cursor.fetchall()
            

        zagl_path = "assets\\zagl.jpg"

        for tovar in all_tovars:
            with st.container(border=True):
                col_photo, col_info, col_discount = st.columns([1,6,1])

                with col_photo:
                    if tovar['photo'] is not None and tovar['photo'] != "":
                        image_path = os.path.join("assets", tovar['photo'])
                        if os.path.exists(image_path):
                            st.image(image_path, use_container_width=True)
                        else:
                            st.image(zagl_path, use_container_width=True)
                    else:
                        st.image(zagl_path, use_container_width=True)
                    
                with col_info:
                    st.subheader(f"{tovar['category_name']} | {tovar['name']}")
                    st.write(f"Производитель: {tovar['manufacturer_name']}")
                    st.write(f"Поставщик: {tovar['supplier_name']}")
                    st.write(f"Описание: {tovar['discription']}")
                    st.write(f"Цена: {tovar['price']} руб.")
                    st.write(f"Количество на скдладе: {tovar['quantity']}")

                with col_discount:
                    st.write(f"Действующая скидка: {tovar['discount']}%")
                    if has_permissions("edit_tovar"):
                        if st.button("удалить", key=f"del_{tovar['id']}"):
                            cursor.execute("UPDATE tovar SET vid = 2 WHERE id = ?",[tovar['id']])
                            conn.commit()
                            st.rerun()

    elif st.session_state.page == "orders" and has_permissions("view_orders"):
        
        if st.button("Назад к товарам"):
            st.session_state.page = "catalog"
            st.rerun()

        if has_permissions("edit_orders"):
            if st.button("Добавить заказ"):
                st.session_state.page = "add_order"
                st.rerun()

        
        st.title("Таблица заказов")
        
        zakaz = f"""
        SELECT
        orders.id,
        orders.date_order,
        orders.date_delivery,
        orders.code,
        tovar.sku,
        tovar.name,
        pvz.address,
        users.name,
        order_status.status,
        order_items.id
        FROM orders
        INNER JOIN order_items ON orders.id = order_items.id
        INNER JOIN pvz ON orders.pvz_id = pvz.id
        INNER JOIN users ON orders.user_id = users.id
        INNER JOIN tovar ON order_items.id_tovar = tovar.id
        INNER JOIN order_status ON orders.status_id = order_status.id
        ORDER BY orders.id ASC
        """

        cursor.execute(zakaz)
        all_zakaz = cursor.fetchall()

        if all_zakaz:
            orders_table = [dict(row) for row in all_zakaz]
            st.dataframe(orders_table, use_container_width=True)
        else:
            st.info("Заказов нет")

    elif st.session_state.page == "add_order" and has_permissions("edit_orders"):
        st.subheader("Добавление заказа")

        if st.button("Назад к заказам"):
            st.session_state.page = "orders"
            st.rerun()

        
        cursor.execute("SELECT id, name FROM tovar WHERE vid = 1")
        tovars_dict = {f"{row['name']} (ID: {row['id']})": row['id'] for row in cursor.fetchall()}

       
        cursor.execute("SELECT id, address FROM pvz")
        pvzs_dict = {row['address']: row['id'] for row in cursor.fetchall()}

        with st.form("add_order_form"):
            select_tovar = st.selectbox("Товар", options=list(tovars_dict.keys()))
            client_fio = st.text_input("ФИО покупателя")
            select_pvz = st.selectbox("ПВЗ", options=list(pvzs_dict.keys()))

            submitted = st.form_submit_button("Сохранить заказ")
            if submitted:
                fio_clean = client_fio.strip()

                if not fio_clean:
                    st.error("Забыли ввести имя")
                    st.stop()

                
                cursor.execute("SELECT id FROM users WHERE name = ?", [fio_clean])
                user_row = cursor.fetchone()

                if user_row is not None:
                    user_id = user_row['id']
                else:
                    cursor.execute("INSERT INTO users (name, role_id) VALUES (?, 3)", [fio_clean])
                    user_id = cursor.lastrowid

                
                tovar_id = tovars_dict[select_tovar]
                pvz_id = pvzs_dict[select_pvz]
                date_order = date.today().strftime("%d.%m.%Y")
                date_delivery = (date.today() + timedelta(days=5)).strftime("%d.%m.%Y")
                code = random.randint(900, 999)
                status_id = 1

               
                cursor.execute("""
                    INSERT INTO orders (date_order, date_delivery, pvz_id, user_id, code, status_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date_order, date_delivery, pvz_id, user_id, code, status_id))

                new_order_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO order_items (id, id_tovar)
                    VALUES (?, ?)
                """, (new_order_id, tovar_id))

                conn.commit()

                
                st.session_state.page = "orders"
                st.rerun()

                  
    if st.sidebar.button("выход"):
        st.session_state.logged_in = False
        st.rerun()
