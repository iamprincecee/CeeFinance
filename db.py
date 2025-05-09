# db.py

import sqlite3
from datetime import datetime

# --- INIT DB ---
def init_db():
    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            date TEXT
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            source TEXT,
            date TEXT
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            roi REAL,
            interval TEXT,
            start_date TEXT
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS losses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            reason TEXT,
            date TEXT
        )""")
    conn.commit()
    conn.close()

# --- SAVE FUNCTIONS ---
def save_expense(user_id, amount, category):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                     (user_id, float(amount), category, datetime.now().strftime("%Y-%m-%d %H:%M")))

def save_income(user_id, amount, source):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO income (user_id, amount, source, date) VALUES (?, ?, ?, ?)",
                     (user_id, float(amount), source, datetime.now().strftime("%Y-%m-%d %H:%M")))

def save_investment(user_id, amount, inv_type, roi, interval):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO investments (user_id, amount, type, roi, interval, start_date) VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, float(amount), inv_type, float(roi.strip('%')), interval, datetime.now().strftime("%Y-%m-%d")))

def save_loss(user_id, amount, reason):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO losses (user_id, amount, reason, date) VALUES (?, ?, ?, ?)",
                     (user_id, float(amount), reason, datetime.now().strftime("%Y-%m-%d %H:%M")))

# --- GET RECENT FUNCTIONS ---
def get_recent_expenses(user_id, limit=5):
    with sqlite3.connect("finance.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?", (user_id, limit))
        return [dict(row) for row in cur.fetchall()]

def get_recent_income(user_id, limit=5):
    with sqlite3.connect("finance.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM income WHERE user_id = ? ORDER BY date DESC LIMIT ?", (user_id, limit))
        return [dict(row) for row in cur.fetchall()]

def get_recent_investments(user_id, limit=5):
    with sqlite3.connect("finance.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM investments WHERE user_id = ? ORDER BY start_date DESC LIMIT ?", (user_id, limit))
        return [dict(row) for row in cur.fetchall()]

def get_recent_losses(user_id, limit=5):
    with sqlite3.connect("finance.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM losses WHERE user_id = ? ORDER BY date DESC LIMIT ?", (user_id, limit))
        return [dict(row) for row in cur.fetchall()]

# --- UPDATE FUNCTIONS ---
def update_expense(expense_id, new_amount, new_category):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("""
            UPDATE expenses
            SET amount = ?, category = ?, date = ?
            WHERE id = ?
        """, (float(new_amount), new_category, datetime.now().strftime("%Y-%m-%d %H:%M"), expense_id))

def update_income(income_id, new_amount, new_source):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("""
            UPDATE income
            SET amount = ?, source = ?, date = ?
            WHERE id = ?
        """, (float(new_amount), new_source, datetime.now().strftime("%Y-%m-%d %H:%M"), income_id))

def update_investment(investment_id, new_amount, new_type):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("""
            UPDATE investments
            SET amount = ?, type = ?, start_date = ?
            WHERE id = ?
        """, (float(new_amount), new_type, datetime.now().strftime("%Y-%m-%d"), investment_id))

def update_loss(loss_id, new_amount, new_reason):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("""
            UPDATE losses
            SET amount = ?, reason = ?, date = ?
            WHERE id = ?
        """, (float(new_amount), new_reason, datetime.now().strftime("%Y-%m-%d %H:%M"), loss_id))

# --- PAGINATION SUPPORT ---
def get_paginated_entries(user_id, kind, page, limit=5):
    offset = page * limit
    table_map = {
        "expenses": "expenses",
        "income": "income",
        "investments": "investments",
        "losses": "losses"
    }
    if kind not in table_map:
        return []

    table = table_map[kind]
    with sqlite3.connect("finance.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"""
            SELECT * FROM {table}
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        return [dict(row) for row in cur.fetchall()]

# --- DELETION SUPPORT ---
def delete_entry(kind, entry_id):
    table_map = {
        "expenses": "expenses",
        "income": "income",
        "investments": "investments",
        "losses": "losses"
    }
    if kind not in table_map:
        return

    with sqlite3.connect("finance.db") as conn:
        conn.execute(f"DELETE FROM {table_map[kind]} WHERE id = ?", (entry_id,))

# --- SEARCH FUNCTIONALITY ---
def search_entries(user_id, category, date_prefix):
    tables = {
        "expenses": "category",
        "income": "source",
        "investments": "type",
        "losses": "reason"
    }
    results = []

    with sqlite3.connect("finance.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        for table, field in tables.items():
            date_field = "start_date" if table == "investments" else "date"
            cur.execute(f"""
                SELECT * FROM {table}
                WHERE user_id = ?
                AND {field} LIKE ?
                AND {date_field} LIKE ?
                ORDER BY {date_field} DESC
            """, (user_id, f"%{category}%", f"{date_prefix}%"))
            results.extend([dict(row) for row in cur.fetchall()])

    return sorted(results, key=lambda x: x.get("date", x.get("start_date", "")), reverse=True)
