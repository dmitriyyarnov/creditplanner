from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import sqlite3
import pandas as pd
import io

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
                    due_date TEXT NOT NULL,
                    comment TEXT
                )''')
    try:
        c.execute("ALTER TABLE credits ADD COLUMN comment TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


init_db()


# --- Главная страница ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request, month: str = Query(None)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, amount, due_date, comment FROM credits ORDER BY due_date")
    credits = c.fetchall()
    conn.close()

    now = datetime.now()
    if not month:
        month = now.strftime("%Y-%m")

    filtered = [cr for cr in credits if cr[3].startswith(month)]
    total_month = sum(cr[2] for cr in filtered)

    # Суммы по месяцам для графика
    monthly_totals = {}
    for _, _, amount, due_date, _ in credits:
        ym = due_date[:7]
        monthly_totals[ym] = monthly_totals.get(ym, 0) + amount

    return templates.TemplateResponse("index.html", {
        "request": request,
        "credits": filtered,
        "total_month": total_month,
        "month": month,
        "monthly_totals": monthly_totals
    })


# --- Добавление кредита ---
@app.post("/add")
def add_credit(
    name: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    comment: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO credits (name, amount, due_date, comment) VALUES (?, ?, ?, ?)",
              (name, amount, due_date, comment))
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


# --- Экспорт Excel ---
@app.get("/export/xlsx")
def export_xlsx():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM credits", conn)
    conn.close()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Credits")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=credits.xlsx"}
    )



















