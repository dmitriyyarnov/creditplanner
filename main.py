from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import sqlite3

app = FastAPI(title="Credit Planner")

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "db.sqlite3"

# --- Инициализация базы ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    due_date TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

# --- Главная страница ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, amount, due_date FROM credits ORDER BY due_date")
    credits = c.fetchall()
    conn.close()

    # Подсчёт общей суммы за текущий месяц
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    total_month = sum(
        amount for _, _, amount, due_date in credits if due_date.startswith(current_month)
    )

    return templates.TemplateResponse("index.html", {
        "request": request,
        "credits": credits,
        "total_month": total_month
    })


# --- Добавление кредита ---
@app.post("/add")
def add_credit(name: str = Form(...), amount: float = Form(...), due_date: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO credits (name, amount, due_date) VALUES (?, ?, ?)", (name, amount, due_date))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)


# --- Удаление кредита ---
@app.post("/delete/{credit_id}")
def delete_credit(credit_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

















