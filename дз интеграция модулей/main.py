import time
import uuid
from typing import List, Literal
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Task Stock API")

# Включаем CORS, чтобы ваш HTML-файл мог делать запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище в оперативной памяти
user_data = {"balance": 100}
tasks_db = {}
penalized_tasks = set()


# --- Схемы валидации данных ---
class TaskCreate(BaseModel):
    text: str
    duration_seconds: int
    cost: int

class TaskResponse(BaseModel):
    id: str
    text: str
    deadline: int
    cost: int
    status: Literal["active", "expired", "completed"]


# --- Служебные функции ---
def get_current_timestamp_ms() -> int:
    return int(time.time() * 1000)

def update_and_get_status(task_id: str) -> str:
    task = tasks_db[task_id]
    if task["is_completed"]:
        return "completed"
        
    current_time = get_current_timestamp_ms()
    if task["deadline"] > current_time:
        return "active"
    else:
        # Автоматическое списание монет при переходе в expired
        if task_id not in penalized_tasks:
            user_data["balance"] -= task["cost"]
            penalized_tasks.add(task_id)
        return "expired"


# --- Спецификация REST API ---

@app.get("/api/user")
def get_user_balance():
    return {"balance": user_data["balance"]}


@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks():
    response = []
    for task_id, task in tasks_db.items():
        current_status = update_and_get_status(task_id)
        response.append({
            "id": task_id,
            "text": task["text"],
            "deadline": task["deadline"],
            "cost": task["cost"],
            "status": current_status
        })
    return response


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    task_id = str(uuid.uuid4())
    deadline_ms = get_current_timestamp_ms() + (payload.duration_seconds * 1000)
    
    tasks_db[task_id] = {
        "text": payload.text,
        "deadline": deadline_ms,
        "cost": payload.cost,
        "is_completed": False
    }
    return {
        "id": task_id,
        "text": payload.text,
        "deadline": deadline_ms,
        "cost": payload.cost,
        "status": "active"
    }


@app.patch("/api/tasks/{task_id}/complete")
def complete_task(task_id: str, response: Response):
    if task_id not in tasks_db:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Задача не найдена"}
        
    current_status = update_and_get_status(task_id)
    
    # Возвращаем ошибку 400 в формате, который ожидает фронтенд
    if current_status == "expired":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Время истекло, задача провалена!"}
        
    if current_status == "completed":
        return {"message": "Задача уже выполнена"}
        
    # Успешное выполнение
    tasks_db[task_id]["is_completed"] = True
    user_data["balance"] += tasks_db[task_id]["cost"]
    return {"message": "Успешно!"}
