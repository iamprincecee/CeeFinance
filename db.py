# db.py
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            user_id INTEGER,
            amount REAL,
            category TEXT,
            date TEXT
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            user_id INTEGER,
            amount REAL,
            source TEXT,
            date TEXT
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            user_id INTEGER,
            amount REAL,
            type TEXT,
            roi REAL,
            interval TEXT,
            start_date TEXT
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS losses (
            user_id INTEGER,
            amount REAL,
            reason TEXT,
            date TEXT
        )""")
    conn.commit()
    conn.close()

def save_expense(user_id, amount, category):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO expenses VALUES (?, ?, ?, ?)",
                     (user_id, float(amount), category, datetime.now().strftime("%Y-%m-%d %H:%M")))

def save_income(user_id, amount, source):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO income VALUES (?, ?, ?, ?)",
                     (user_id, float(amount), source, datetime.now().strftime("%Y-%m-%d %H:%M")))

def save_investment(user_id, amount, inv_type, roi, interval):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO investments VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, float(amount), inv_type, float(roi.strip('%')), interval, datetime.now().strftime("%Y-%m-%d")))

def save_loss(user_id, amount, reason):
    with sqlite3.connect("finance.db") as conn:
        conn.execute("INSERT INTO losses VALUES (?, ?, ?, ?)",
                     (user_id, float(amount), reason, datetime.now().strftime("%Y-%m-%d %H:%M")))
