import sqlite3
import streamlit as st
from typing import Dict, Optional, List
import app

# Импорты
from app import (
    init_db, auth_user, create_user, get_tasks, create_task, create_bid,
    get_bids_for_task, get_messages, create_message, create_rating,
    get_average_rating, top_categories, get_user_tasks, get_user_balance,
    request_withdrawal, process_payment, get_admin_stats, add_balance
)

init_db()

if "page" not in st.session_state:
    st.session_state.page = "index"
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None

# Функции пользователя
def get_current_user() -> Optional[Dict]:
    user_id = st.session_state.get("user_id")
    if user_id is None: return None
    conn = sqlite3.connect(app.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, balance FROM Users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "email": row[2], "role": row[3], "balance": row[4]}
    return None

def is_logged() -> bool:
    return get_current_user() is not None

def logout():
    if "user_id" in st.session_state: del st.session_state.user_id
    st.session_state.page = "index"
    st.session_state.selected_task_id = None
    st.rerun()

def redirect_to(page: str, task_id: int = None):
    st.session_state.page = page
    if task_id is not None: st.session_state.selected_task_id = task_id
    st.rerun()

# Навигация
def show_navbar():
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("← Назад", key="nav_back"):
            redirect_to("index")

    current_user = get_current_user()
    if current_user:
        st.sidebar.write(f"**{current_user['username']} ({current_user['role']})**")
        if st.sidebar.button("Кабинет"): redirect_to("dashboard")
        if current_user['role'] == 'admin' and st.sidebar.button("Админ"): redirect_to("admin")
        if st.sidebar.button("Выйти"): logout()
    else:
        st.sidebar.info("Вы в режиме гостя.")
        if st.sidebar.button("Войти"): redirect_to("login")
        if st.sidebar.button("Регистрация"): redirect_to("register")


# Dashboard (с формой оплаты + новым функционалом)
def show_dashboard():
    show_navbar()
    current_user = get_current_user()
    if not current_user:
        redirect_to("index")

    st.header(f"Личный кабинет: {current_user['username']} ({current_user['role']})")
    st.metric("Баланс", f"{get_user_balance(current_user['id']):.2f} ₽")

    if current_user['role'] == 'freelancer':
        tasks = get_user_tasks(current_user['id'], 'freelancer')
        st.subheader("Ваши задачи")
        if not tasks:
            st.info("Задач пока нет.")
        else:
            for task in tasks:
                col1, col2 = st.columns(2)
                col1.metric(task['title'], task['status'])
                if task['status'] == 'completed':
                    col2.success("Готово к оплате")

    elif current_user['role'] == 'client':
        tasks = get_user_tasks(current_user['id'], 'client')
        st.subheader("Ваши задачи")

        if not tasks:
            st.info("Задач пока нет.")
        else:
            for task in tasks:
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.metric(task['title'], task['status'])

                # Если есть фрилансер, подтягиваем бюджет и имя через join
                if task.get('freelancer_id') is not None:
                    conn = sqlite3.connect(app.DB_NAME)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT t.budget, u.username AS freelancer_name
                        FROM Tasks t
                        JOIN Users u ON t.freelancer_id = u.id
                        WHERE t.id = ?
                    """, (task['id'],))
                    row = cursor.fetchone()
                    conn.close()

                    if not row:
                        continue

                    budget = float(row['budget'])
                    freelancer_name = row['freelancer_name']

                    col2.info(f"Фрилансер: {freelancer_name}")

                    # Логика статуса: "in_progress" → можно подтвердить выполнение
                    if task['status'] == 'in_progress':
                        if col3.button("✅ Подтвердить выполнение", key=f"confirm_{task['id']}"):
                            conn = sqlite3.connect(app.DB_NAME)
                            try:
                                cursor = conn.execute(
                                    "UPDATE Tasks SET status = 'completed' WHERE id = ? AND client_id = ? AND status = ?",
                                    (task['id'], current_user['id'], 'in_progress')
                                )
                                conn.commit()
                                if cursor.rowcount > 0:
                                    st.success("Задача отмечена как выполненная.")
                                    st.rerun()
                                else:
                                    st.error("Невозможно подтвердить выполнение.")
                            except Exception as e:
                                st.error(f"Ошибка: {e}")
                            finally:
                                conn.close()

                    # Если задача завершена, показываем платёж
                    elif task['status'] == 'completed':
                        balance = get_user_balance(current_user['id'])

                        if balance < budget:
                            col3.error("Недостаточно средств")
                            with st.form(key=f"topup_form_{task['id']}", clear_on_submit=True):
                                topup_amount = st.number_input(
                                    "Сумма пополнения (₽)", min_value=100.0, step=100.0,
                                    key=f"topup_amt_{task['id']}"
                                )
                                if st.form_submit_button("Пополнить баланс", key=f"topup_btn_{task['id']}"):
                                    msg = add_balance(current_user['id'], topup_amount)
                                    st.success(msg)
                                    st.rerun()
                        else:
                            with col3:
                                with st.form(key=f"pay_form_{task['id']}", clear_on_submit=True):
                                    method = st.selectbox(
                                        "Способ",
                                        ["card", "crypto"],
                                        key=f"method_{task['id']}"
                                    )
                                    if st.form_submit_button("✅ Оплатить заказ", key=f"pay_btn_{task['id']}"):
                                        msg = process_payment(
                                            task_id=task['id'],
                                            amount=budget,
                                            method=method,
                                            client_id=current_user['id'],
                                            freelancer_id=task['freelancer_id']
                                        )
                                        st.success(msg)
                                        st.rerun()

                    # Кнопка "отказаться от фрилансера" (без оплаты)
                    elif task['status'] in ['in_progress', 'completed']:
                        if col3.button("❌ Отказаться от фрилансера", key=f"cancel_{task['id']}"):
                            conn = sqlite3.connect(app.DB_NAME)
                            try:
                                cursor = conn.execute(
                                    "UPDATE Tasks SET status = 'cancelled', freelancer_id = NULL WHERE id = ? AND client_id = ? AND status IN ('in_progress', 'completed')",
                                    (task['id'], current_user['id'])
                                )
                                conn.commit()
                                if cursor.rowcount > 0:
                                    st.success("Вы отказались от фрилансера.")
                                    st.rerun()
                                else:
                                    st.error("Невозможно отказаться (задача уже завершена/отменена).")
                            except Exception as e:
                                st.error(f"Ошибка: {e}")
                            finally:
                                conn.close()

    st.subheader("Вывод средств")
    amount = st.number_input("Сумма", min_value=100.0)
    method = st.selectbox("Куда", ["card", "crypto"])
    if st.button("Вывести"):
        msg = request_withdrawal(current_user['id'], amount, method)
        st.success(msg)


def show_admin():
    show_navbar()
    current_user = get_current_user()
    if not current_user or current_user['role'] != 'admin':
        st.error("Доступ только админу")
        return

    stats = get_admin_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("Пользователи", stats['users'])
    col2.metric("Задачи", stats['tasks'])
    col3.metric("Общий баланс", f"{stats['total_balance']:.2f} ₽")


# Регистрация/логин
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
            st.success("Регистрация успешна!")
            redirect_to("login")
        else:
            st.error("Пользователь уже есть.")


def show_login():
    show_navbar()
    st.subheader("Вход")
    username = st.text_input("Имя пользователя", key="login_username")
    password = st.text_input("Пароль", type="password", key="login_password")
    if st.button("Войти", key="login_submit"):
        user = auth_user(username, password)
        if user:
            st.session_state.user_id = user["id"]
            redirect_to("index")
        else:
            st.error("Неправильные данные.")
    if st.button("Регистрация", key="login_register_btn"):
        redirect_to("register")


# Главная
def show_index():
    show_navbar()
    st.title("Фриланс‑борд")

    current_user = get_current_user()
    col1, col2 = st.columns(2)
    if not current_user:
        with col1:
            if st.button("Войти"):
                redirect_to("login")
        with col2:
            if st.button("Регистрация"):
                redirect_to("register")
    elif current_user["role"] == "client":
        if st.button("Создать задачу"):
            redirect_to("create_task")

    tasks = get_tasks()
    if not tasks:
        st.info("Задач пока нет.")
        return

    st.subheader("Список задач")
    for task in tasks:
        with st.container(border=True):
            st.markdown(f"**ID: {task['id']}** | {task['title']} | Бюджет: {task['budget']}₽ "
                        f"| Клиент: {task['client_name']} | {task['status']}")
            if st.button("Посмотреть", key=f"task_{task['id']}"):
                redirect_to("task_detail", task["id"])


# Создание задачи
def show_create_task():
    show_navbar()
    current_user = get_current_user()
    if not current_user or current_user["role"] != "client":
        st.warning("Только клиенты!")
        redirect_to("index")

    st.subheader("Создать задачу")
    title = st.text_input("Название")
    description = st.text_area("Описание")
    categories = ["DIY", "Электроника", "Кодинг", "Дизайн", "Текст", "Другое"]
    category = st.selectbox("Категория", categories)
    budget = st.number_input("Бюджет (₽)", min_value=100.0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Создать"):
            if title.strip():
                task_id = create_task(current_user["id"], title.strip(), description.strip(), category, budget)
                st.success(f"Задача #{task_id} создана!")
                redirect_to("task_detail", task_id)
            else:
                st.error("Название обязательно!")
    with col2:
        if st.button("Назад"):
            redirect_to("index")


def show_task_detail():
    show_navbar()
    if not st.session_state.selected_task_id:
        st.error("Задача не выбрана.")
        redirect_to("index")
        return

    task_id = st.session_state.selected_task_id
    conn = sqlite3.connect(app.DB_NAME)
    cursor = conn.execute("""
        SELECT t.id, t.title, t.description, t.category, t.budget, t.status,
               t.client_id, t.freelancer_id, c.username, f.username
        FROM Tasks t
        LEFT JOIN Users c ON t.client_id = c.id
        LEFT JOIN Users f ON t.freelancer_id = f.id
        WHERE t.id = ?
    """, (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("Задача не найдена.")
        redirect_to("index")
        return

    task = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "category": row[3],
        "budget": row[4],
        "status": row[5],
        "client_id": row[6],
        "freelancer_id": row[7],
        "client_name": row[8] or "N/A",
        "freelancer_name": row[9]
    }

    st.title(f"Задача #{task['id']}: {task['title']}")
    col1, col2 = st.columns(2)
    col1.metric("Клиент", task["client_name"])
    if task["freelancer_name"]:
        col2.metric("Фрилансер", task["freelancer_name"])
    st.metric("Бюджет", f"{task['budget']}₽")
    st.write(f"📂 {task['category']} | 🟢 {task['status']}")
    st.markdown(f"**Описание:**\n{task['description']}")
    st.markdown("---")

    current_user = get_current_user()

    if current_user and current_user["role"] == "freelancer" and not task["freelancer_id"] and task["status"] == "open":
        col1, col2 = st.columns(2)
        if col1.button("🚀 Взять работу", use_container_width=True):
            conn = sqlite3.connect(app.DB_NAME)
            try:
                cursor = conn.execute(
                    "UPDATE Tasks SET freelancer_id = ?, status = 'in_progress' WHERE id = ? AND freelancer_id IS NULL",
                    (current_user["id"], task_id)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    st.success("✅ Работа взята! Теперь чат активен.")
                    st.rerun()
                else:
                    st.error("Работа уже взята другим.")
            except Exception as e:
                st.error(f"Ошибка: {e}")
            finally:
                conn.close()

    if current_user and current_user["role"] == "client":
        if task["freelancer_id"] and task["status"] in ["in_progress", "completed"]:
            if st.button("❌ Отказаться от фрилансера", key=f"cancel_freelancer_{task['id']}"):
                conn = sqlite3.connect(app.DB_NAME)
                try:
                    cursor = conn.execute(
                        """
                        UPDATE Tasks
                        SET status = 'open', freelancer_id = NULL
                        WHERE id = ? AND client_id = ? AND freelancer_id IS NOT NULL
                        """,
                        (task["id"], current_user["id"])
                    )
                    conn.commit()
                    if cursor.rowcount > 0:
                        st.success("Вы отказались от фрилансера.")
                        st.rerun()
                    else:
                        st.error("Не удалось отменить задачу.")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
                finally:
                    conn.close()

    bids = get_bids_for_task(task_id)

    if task["status"] != "paid":
        st.subheader("💰 Ставки")
        if bids:
            for bid in bids:
                st.markdown(f"**{bid.get('freelancer_name', 'N/A')}**: {bid.get('amount', 0)}₽ | {bid.get('message', '—')}")
        else:
            st.info("Ставок пока нет.")

        if current_user and current_user["role"] == "freelancer":
            with st.form(key="bid_form", clear_on_submit=True):
                amount = st.number_input("Сумма (₽)", min_value=100.0, step=50.0)
                message = st.text_area("Комментарий", placeholder="Сделаю быстро...")
                if st.form_submit_button("🎯 Подать ставку"):
                    if amount > 0:
                        bid_id = create_bid(task_id, current_user["id"], amount, message.strip())
                        st.success(f"✅ Ставка #{bid_id} подана!")
                        st.rerun()
                    else:
                        st.error("Сумма > 100₽")
    else:
        st.subheader("💰 Ставки (просмотр)")
        st.info("Задача уже оплачена, ставки недоступны для подачи.")
        if bids:
            for bid in bids:
                st.markdown(f"**{bid.get('freelancer_name', 'N/A')}**: {bid.get('amount', 0)}₽ | {bid.get('message', '—')}")

    st.subheader("💬 Переписка")
    messages = get_messages(task_id) or []
    if messages:
        for msg in messages:
            st.markdown(f"**{msg.get('sender_name', 'N/A')}**: {msg.get('content', '')}")
    else:
        st.info("Сообщений нет.")

    if current_user:
        if task["freelancer_id"] is None:
            st.info("Чат недоступен: фрилансер не назначен.")
        else:
            with st.form(key=f"chat_form_{task['id']}", clear_on_submit=True):
                content = st.text_area("Сообщение", placeholder="Обсудим детали...")
                if st.form_submit_button("📤 Отправить"):
                    if content.strip():
                        if current_user["role"] == "freelancer":
                            receiver_id = task["client_id"]
                        elif current_user["role"] == "client":
                            receiver_id = task["freelancer_id"]
                        else:
                            receiver_id = None

                        if receiver_id is None:
                            st.error("Нельзя отправить сообщение: второй участник чата не назначен.")
                        else:
                            create_message(task_id, current_user["id"], receiver_id, content.strip())
                            st.success("✅ Отправлено!")
                            st.rerun()
                    else:
                        st.warning("Напиши текст!")

# Main роутер
def main():
    if st.session_state.page == "register": show_register()
    elif st.session_state.page == "login": show_login()
    elif st.session_state.page == "dashboard": show_dashboard()
    elif st.session_state.page == "admin": show_admin()
    elif st.session_state.page == "create_task": show_create_task()
    elif st.session_state.page == "task_detail": show_task_detail()
    else: show_index()

if __name__ == "__main__":
    main()
