# reports.py

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_pdf import PdfPages

REPORT_DIR = "reports"
CHART_DIR = "charts"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

def generate_report(user_id, flags):
    conn = sqlite3.connect("finance.db")

    df_exp = pd.read_sql(f"SELECT * FROM expenses WHERE user_id={user_id}", conn)
    df_inc = pd.read_sql(f"SELECT * FROM income WHERE user_id={user_id}", conn)
    df_inv = pd.read_sql(f"SELECT * FROM investments WHERE user_id={user_id}", conn)
    df_loss = pd.read_sql(f"SELECT * FROM losses WHERE user_id={user_id}", conn)

    conn.close()

    # Filter by date
    if "7d" in flags:
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    elif "30d" in flags:
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        cutoff = "1970-01-01"

    df_exp = df_exp[df_exp['date'] >= cutoff]
    df_inc = df_inc[df_inc['date'] >= cutoff]
    df_loss = df_loss[df_loss['date'] >= cutoff]
    df_inv = df_inv[df_inv['start_date'] >= cutoff]

    totals = {
        "total_expenses": df_exp['amount'].sum(),
        "total_income": df_inc['amount'].sum(),
        "total_invested": df_inv['amount'].sum(),
        "total_roi": (df_inv['amount'] * df_inv['roi'] / 100).sum(),
        "total_losses": df_loss['amount'].sum()
    }

    report_type = "totals" if "totals" in flags else "full"
    format_type = "pdf" if "pdf" in flags else "xlsx"

    if report_type == "totals":
        df_report = pd.DataFrame([totals])
    else:
        df_report = pd.concat([
            df_exp.assign(type='Expense'),
            df_inc.assign(type='Income'),
            df_inv.assign(type='Investment'),
            df_loss.assign(type='Loss')
        ], ignore_index=True)

    filename = os.path.join(REPORT_DIR, f"{user_id}_report.{format_type}")

    if format_type == "xlsx":
        df_report.to_excel(filename, index=False)
    else:
        with PdfPages(filename) as pdf:
            fig, ax = plt.subplots()
            df_report.select_dtypes(include='number').sum().plot(kind='barh', ax=ax)
            ax.set_title("Financial Overview")
            pdf.savefig(fig)
            plt.close()

    return filename

def generate_chart(user_id, flag):
    conn = sqlite3.connect("finance.db")
    file = os.path.join(CHART_DIR, f"{user_id}_{flag}.png")

    def fetch(table, group_col, date_col):
        df = pd.read_sql(f"SELECT {group_col}, amount, {date_col} FROM {table} WHERE user_id = {user_id}", conn)
        df[date_col] = pd.to_datetime(df[date_col]).dt.date
        return df

    if flag == "chart_exp":
        df = fetch("expenses", "category", "date")
        df.groupby("category")['amount'].sum().plot(kind="bar", title="Expenses by Category")
    elif flag == "chart_inc":
        df = fetch("income", "source", "date")
        df.groupby("source")['amount'].sum().plot(kind="bar", title="Income by Source")
    elif flag == "chart_inv":
        df = fetch("investments", "type", "start_date")
        df.groupby("type")['amount'].sum().plot(kind="bar", title="Investments by Type")
    elif flag == "chart_all":
        exp = fetch("expenses", "category", "date")['amount'].sum()
        inc = fetch("income", "source", "date")['amount'].sum()
        inv = fetch("investments", "type", "start_date")['amount'].sum()
        plt.bar(["Expenses", "Income", "Investments"], [exp, inc, inv])
        plt.title("Expenses vs Income vs Investments")
    elif flag == "chart_ei":
        e = fetch("expenses", "category", "date").groupby("date")['amount'].sum()
        i = fetch("income", "source", "date").groupby("date")['amount'].sum()
        pd.concat([e.rename("Expenses"), i.rename("Income")], axis=1).fillna(0).plot(title="Expenses vs Income")
    elif flag == "chart_ii":
        i = fetch("income", "source", "date").groupby("date")['amount'].sum()
        v = fetch("investments", "type", "start_date").groupby("start_date")['amount'].sum()
        pd.concat([i.rename("Income"), v.rename("Investments")], axis=1).fillna(0).plot(title="Income vs Investments")

    plt.tight_layout()
    plt.savefig(file)
    plt.close()
    conn.close()
    return file
