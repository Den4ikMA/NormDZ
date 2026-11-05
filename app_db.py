import streamlit as st
import sqlite3
import os

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
    "менеджер": ["view_tovars", "view_orders", "sort_tovar"],
    "администратор": ["view_tovars", "view_orders", "edit_orders", "sort_tovar", "edit_tovar"]
    }

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
            st.rerun()
        else:
            st.write("неверный логин или пароль")

    if st.button("войти как гость"):
        st.session_state.logged_in = True
        st.session_state.user_name = ""
        st.session_state.user_role = "Гость"
        st.rerun()
        
else:
    st.subheader(f"Добро пожаловать, {st.session_state.user_role}  {st.session_state.user_name}")
    st.write("--------")
    st.title("Каталог товаров")

    sort = "tovar.name ASC"

    #функция проверки прав
    def has_permissions(action):
        current_role = st.session_state.get("user_role")

        allowed_actions = DOSTYP.get(current_role, [])

        return action in allowed_actions
    
    #сортировка
    if has_permissions("sort_tovar"):
        vybor = st.selectbox("Сортировать по:", ["алфавиту", "цене(по уменьшению)", "цене(по возрастанию)"])

        if vybor == "цене(по возрастанию)":
            sort = "tovar.price ASC"
        elif vybor == "цене(по уменьшению)":
            sort = "tovar.price DESC"
        else:
            sort = "tovar.name ASC"
            
    
    tovars = f"""
    SELECT
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
    ORDER BY {sort}
    """
    cursor.execute(tovars)
    all_tovars = cursor.fetchall()

    zagl_path = "assets\zagl.jpg"

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
                st.write(f"Цена: {tovar['price']} руб.")
                st.write(f"Количество на скдладе: {tovar['quantity']}")

            with col_discount:
                st.write(f"Действующая скидка: {tovar['discount']}%")
                #если админ или менеджер то кнопка удалить
                if has_permissions("edit_tovar"):
                    if st.button("удалить", key=f"del_{tovar['name']}"):
                        
                        st.write("Товар удалён!")

            
    if st.sidebar.button("выход"):
        st.session_state.logged_in = False
        st.rerun()
