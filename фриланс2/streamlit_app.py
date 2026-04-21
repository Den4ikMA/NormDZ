import sqlite3
import streamlit as st
from typing import Dict, Optional, List
import app  # import модуля для app.DB_NAME


# --- Инициализация и сессия ---
from app import (
    init_db,
    auth_user,
    create_user,
    get_tasks,
    create_task,
    create_bid,
    get_bids_for_task,
    get_messages,
    create_message,
    create_rating,
    get_average_rating,
    top_categories,
)

init_db()

if "page" not in st.session_state:
    st.session_state.page = "index"  # ["index", "register", "login", "create_task"]
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None


# --- Функции работы с пользователем ---
def get_current_user() -> Optional[Dict]:
    user_id = st.session_state.get("user_id")
    if user_id is None:
        return None
    conn = sqlite3.connect(app.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, role, balance FROM Users WHERE id = ?",
        (user_id,)
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


def is_logged() -> bool:
    return get_current_user() is not None


def logout():
    if "user_id" in st.session_state:
        del st.session_state.user_id
    st.session_state.page = "index"
    st.session_state.selected_task_id = None
    st.rerun()


def redirect_to(page: str, task_id: int = None):
    st.session_state.page = page
    if task_id is not None:
        st.session_state.selected_task_id = task_id
    st.rerun()


# --- Универсальная навигация сверху ---
def show_navbar():
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("← Назад", key="nav_back"):
            redirect_to("index")

    current_user = get_current_user()
    if current_user:
        st.sidebar.write(f"**{current_user['username']} ({current_user['role']})**")
        if st.sidebar.button("Выйти"):
            logout()
    else:
        st.sidebar.info("Вы в режиме гостя.")
        if st.sidebar.button("Войти"):
            redirect_to("login")
        if st.sidebar.button("Регистрация"):
            redirect_to("register")


# --- Регистрация ---
def show_register():
    show_navbar()

    st.subheader("Регистрация")
    username = st.text_input("Имя пользователя", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Пароль", type="password", key="reg_password")
    role = st.radio("Роль", ["client", "freelancer"], key="reg_role")

    if st.button("Зарегистрироваться", key="reg_submit"):
        if not username.strip() or not email.strip() or not password.strip():
            st.error("Заполните все поля.")
        elif create_user(username.strip(), email.strip(), password.strip(), role):
            st.success("Регистрация успешна, можете войти.")
            redirect_to("login")
        else:
            st.error("Пользователь с таким именем или email уже есть.")


# --- Вход ---
def show_login():
    show_navbar()

    st.subheader("Вход")
    username = st.text_input("Имя пользователя", key="login_username")
    password = st.text_input("Пароль", type="password", key="login_password")

    if st.button("Войти", key="login_submit"):
        user = auth_user(username, password)
        if user:
            st.session_state.user_id = user["id"]  # ← только user_id
            redirect_to("index")
        else:
            st.error("Неправильное имя или пароль.")

    if st.button("Регистрация", key="login_register_btn"):
        redirect_to("register")


# --- Главная страница — список задач ---
def show_index():
    show_navbar()

    st.title("Фриланс‑борд")

    col1, col2 = st.columns(2)
    current_user = get_current_user()

    if not current_user:
        with col1:
            if st.button("Войти"):
                redirect_to("login")
        with col2:
            if st.button("Регистрация"):
                redirect_to("register")
    else:
        if current_user["role"] == "client":
            if st.button("Создать задачу"):
                redirect_to("create_task")

    tasks = get_tasks()
    if not tasks:
        st.info("Задач пока нет.")
        return

    st.subheader("Список задач")
    for task in tasks:
        with st.container(border=True):
            st.markdown(
                f"**ID: {task['id']}** | {task['title']} | "
                f"Бюджет: {task['budget']} | "
                f"Клиент: {task['client_name']} | "
                f"Статус: {task['status']}"
            )
            if st.button("Посмотреть задачу", key=f"task_btn_{task['id']}"):
                redirect_to("task_detail", task_id=task["id"])


# --- Создание задачи ---
def show_create_task():
    show_navbar()

    current_user = get_current_user()
    if not current_user:
        st.warning("Сначала войдите в систему.")
        redirect_to("login")

    if current_user["role"] != "client":
        st.warning("Создавать задачи может только клиент.")
        redirect_to("index")

    st.subheader("Создать задачу")
    title = st.text_input("Название задачи")
    description = st.text_area("Описание")
    category = st.text_input("Категория")
    budget = st.number_input("Бюджет", min_value=0.0, step=1.0)

    col1, col2 = st.columns(2)
    if col1.button("Создать задачу"):
        if not title.strip():
            st.error("Укажите название задачи.")
        else:
            task_id = create_task(
                client_id=current_user["id"],
                title=title.strip(),
                description=description.strip(),
                category=category.strip(),
                budget=budget,
            )
            st.success(f"Задача создана (ID: {task_id}).")
            redirect_to("task_detail", task_id=task_id)
    if col2.button("Назад"):
        redirect_to("index")


# --- Страница задачи: детали, ставки, чат ---
def show_task_detail():
    show_navbar()

    if not st.session_state.selected_task_id:
        st.error("Задача не выбрана.")
        redirect_to("index")
        return

    task_id = st.session_state.selected_task_id

    conn = sqlite3.connect(app.DB_NAME)
    conn.row_factory = sqlite3.Row
    task = conn.execute("""SELECT t.*, c.username AS client_name, f.username AS contractor_name
                           FROM Tasks t
                           LEFT JOIN Users c ON t.client_id = c.id
                           LEFT JOIN Users f ON t.contractor_id = f.id
                           WHERE t.id = ?""", (task_id,)).fetchone()
    conn.close()
    if not task:
        st.error("Задача не найдена.")
        redirect_to("index")
        return

    st.title(f"Задача #{task['id']}")
    st.subheader(task["title"])
    st.write(f"**Клиент:** {task['client_name']}")
    if task["contractor_name"]:
        st.write(f"**Исполнитель:** {task['contractor_name']}")
    st.write(f"**Бюджет:** {task['budget']}")
    st.write(f"**Категория:** {task['category']}")
    st.write(f"**Описание:** {task['description']}")
    st.write(f"**Статус:** {task['status']}")
    st.markdown("---")

    # Ставки
    bids = get_bids_for_task(task_id)
    st.subheader("Ставки")
    if bids:
        for bid in bids:
            st.markdown(
                f"- **{bid['freelancer_name']}**: {bid['amount']} | {bid['message'] or '—'}"
            )
    else:
        st.info("Ставок пока нет.")

    current_user = get_current_user()
    if current_user and current_user["role"] == "freelancer":
        with st.form("bid_form"):
            amount = st.number_input("Размер ставки", min_value=0.0, step=0.1)
            message = st.text_area("Сообщение", placeholder="Комментарий к ставке")
            if st.form_submit_button("Сделать ставку"):
                create_bid(
                    task_id=task_id,
                    freelancer_id=current_user["id"],
                    amount=amount,
                    message=message,
                )
                st.success("Ставка сделана.")
                st.rerun()

    # Чат
    st.subheader("Переписка")
    messages = get_messages(task_id)
    if messages:
        for msg in messages:
            st.markdown(
                f"<div style='margin: 4px 0; padding: 4px; border-left: 3px solid #333'>"
                f"<b>{msg['sender_name']}</b> ({msg['created_at']}):<br>{msg['content']}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Сообщений ещё нет.")

    if current_user:
        with st.form("message_form"):
            content = st.text_area("Сообщение")
            if st.form_submit_button("Отправить сообщение"):
                receiver_id = (
                    task["client_id"]
                    if task["client_name"] == current_user["username"]
                    else task["contractor_id"]
                )
                if receiver_id:
                    create_message(
                        task_id=task_id,
                        sender_id=current_user["id"],
                        receiver_id=receiver_id,
                        content=content,
                    )
                    st.rerun()
                else:
                    st.warning("Нельзя отправить сообщение: нет контрагента.")


# --- Основной роутер страниц ---
def main():
    if st.session_state.page == "register":
        show_register()
        if st.button("Уже есть аккаунт, войти"):
            redirect_to("login")

    elif st.session_state.page == "login":
        show_login()

    elif st.session_state.page == "create_task":
        show_create_task()

    elif st.session_state.page == "task_detail":
        show_task_detail()

    else:
        show_index()


if __name__ == "__main__":
    main()
