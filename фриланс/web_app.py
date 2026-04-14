from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

# --- импорт функций из app.py (твоего старого файла) ---
from app import (
    create_user,          # например, из твоего app.py
    auth_user,
    create_task,
    create_bid,
    get_tasks,
    get_bids_for_task,
    get_messages,
    create_message,
    create_rating,
    get_average_rating,
    top_categories,
)

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "freelance_board.db"


# --- Пользователи ---


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = "client" if "client" in request.form.get("role", "") else "freelancer"

        success = create_user(username, email, password, role)
        if success:
            flash("Регистрация успешна, войдите в систему.")
            return redirect(url_for("login"))
        else:
            flash("Пользователь с таким именем или email уже есть.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = auth_user(username, password)

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("index"))
        else:
            flash("Неправильное имя или пароль.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# --- Главная страница (лента задач) ---


@app.route("/")
def index():
    tasks = get_tasks()
    return render_template("index.html", tasks=tasks)


# --- Создание задачи ---


@app.route("/create_task", methods=["GET", "POST"])
def create_task_view():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        budget = float(request.form["budget"])

        task_id = create_task(
            client_id=session["user_id"],
            title=title,
            description=description,
            category=category,
            budget=budget,
        )

        flash("Задача создана.")
        return redirect(url_for("index"))

    return render_template("create_task.html")


# --- Детали задачи + ставки + чат ---


@app.route("/task/<int:task_id>", methods=["GET", "POST"])
def task_detail(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    # задача уже есть в БД, просто читаем
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    task = conn.execute("""
        SELECT t.*, c.username AS client_name, f.username AS contractor_name
        FROM Tasks t
        LEFT JOIN Users c ON t.client_id = c.id
        LEFT JOIN Users f ON t.contractor_id = f.id
        WHERE t.id = ?
    """, (task_id,)).fetchone()
    conn.close()

    if not task:
        from flask import abort
        abort(404)

    bids = get_bids_for_task(task_id)
    messages = get_messages(task_id)

    if request.method == "POST":
        if "amount" in request.form and session.get("role") == "freelancer":
            # ставка
            amount = float(request.form["amount"])
            message = request.form.get("message", "")

            create_bid(task_id=task_id, freelancer_id=session["user_id"], amount=amount, message=message)

        elif "message" in request.form:
            # сообщение
            content = request.form["message"]
            receiver_id = task["client_id"] if task["client_name"] == session["username"] else task["contractor_id"]

            create_message(
                task_id=task_id,
                sender_id=session["user_id"],
                receiver_id=receiver_id,
                content=content,
            )

        return redirect(url_for("task_detail", task_id=task_id))

    return render_template("task_detail.html", task=task, bids=bids, messages=messages)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
