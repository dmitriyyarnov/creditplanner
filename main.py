from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from datetime import datetime
import sqlite3
import pandas as pd
import io
import calendar

# Импорт из config.py
from config import static_files, templates, DB_PATH

app = FastAPI(title="Credit Planner")

app.mount("/static", static_files, name="static")

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

def generate_month_calendar(year: int, month: int, payment_days: list):
    cal = calendar.Calendar()
    weeks = cal.monthdayscalendar(year, month)

    html = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; text-align: center;">'
    html += '<tr>'
    for day_name in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
        html += f'<th>{day_name}</th>'
    html += '</tr>'

    for week in weeks:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td></td>'
            elif day in payment_days:
                html += f'<td style="background-color: #36a2eb; color:white; font-weight:bold;">💰 {day}</td>'
            else:
                html += f'<td>{day}</td>'
        html += '</tr>'

    html += '</table>'
    return html

@app.get("/", response_class=HTMLResponse)
def index(request: Request, month: str = Query(None)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, amount, due_date, comment FROM credits ORDER BY due_date")
    credits = c.fetchall()
    conn.close()

    now = datetime.now()
    if not month or month.strip() == "":
        month = now.strftime("%Y-%m")

    filtered = [cr for cr in credits if cr[3].startswith(month)]
    total_month = sum(cr[2] for cr in filtered)

    year, month_num = map(int, month.split('-'))
    payment_days = [int(cr[3].split('-')[2]) for cr in filtered if cr[3]]

    calendar_html = generate_month_calendar(year, month_num, payment_days)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "credits": filtered,
        "total_month": total_month,
        "month": month,
        "calendar_html": calendar_html
    })

@app.post("/add")
def add_credit(
    name: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    comment: str = Form(""),
    month: str = Form(None)
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO credits (name, amount, due_date, comment) VALUES (?, ?, ?, ?)",
              (name, amount, due_date, comment))
    conn.commit()
    conn.close()

    redirect_url = f"/?month={month}" if month else "/"
    return RedirectResponse(url=redirect_url, status_code=303)

@app.post("/delete/{credit_id}")
def delete_credit(credit_id: int, month: str = Form(None)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
    conn.commit()
    conn.close()

    redirect_url = f"/?month={month}" if month else "/"
    return RedirectResponse(url=redirect_url, status_code=303)

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









