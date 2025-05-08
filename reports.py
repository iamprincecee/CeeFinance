# reports.py
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def generate_report(user_id, flags):
    conn = sqlite3.connect("finance.db")
    df_exp = pd.read_sql(f"SELECT * FROM expenses WHERE user_id={user_id}", conn)
    df_inc = pd.read_sql(f"SELECT * FROM income WHERE user_id={user_id}", conn)
    df_inv = pd.read_sql(f"SELECT * FROM investments WHERE user_id={user_id}", conn)
    df_loss = pd.read_sql(f"SELECT * FROM losses WHERE user_id={user_id}", conn)

    # Apply filters (for simplicity, handle flags logic as stubs)
    if "7d" in flags:
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        df_exp = df_exp[df_exp['date'] >= cutoff]
        df_inc = df_inc[df_inc['date'] >= cutoff]
        df_loss = df_loss[df_loss['date'] >= cutoff]

    report_type = "totals" if "totals" in flags else "full"
    format_type = "pdf" if "pdf" in flags else "xlsx"

    # Compute totals
    totals = {
        "total_expenses": df_exp['amount'].sum(),
        "total_income": df_inc['amount'].sum(),
        "total_invested": df_inv['amount'].sum(),
        "total_roi": (df_inv['amount'] * df_inv['roi'] / 100).sum(),
        "total_losses": df_loss['amount'].sum()
    }

    if report_type == "totals":
        df_report = pd.DataFrame([totals])
    else:
        df_report = pd.concat([df_exp.assign(type='Expense'),
                               df_inc.assign(type='Income'),
                               df_inv.assign(type='Investment'),
                               df_loss.assign(type='Loss')], ignore_index=True)

    file = f"report_{user_id}.{format_type}"
    if format_type == "xlsx":
        df_report.to_excel(file, index=False)
    else:
        import matplotlib.backends.backend_pdf as pdf
        p = pdf.PdfPages(file)
        fig, ax = plt.subplots()
        df_report.plot(kind='barh', ax=ax)
        p.savefig(fig)
        p.close()

    return file

def generate_chart(user_id, flag):
    conn = sqlite3.connect("finance.db")
    chart_map = {
        "chart_exp": ("expenses", "category"),
        "chart_inc": ("income", "source"),
        "chart_inv": ("investments", "type"),
        "chart_all": None,
        "chart_ei": None,
        "chart_ii": None
    }
    file = f"chart_{user_id}.png"
    if flag in chart_map and chart_map[flag]:
        table, group_col = chart_map[flag]
        df = pd.read_sql(f"SELECT * FROM {table} WHERE user_id={user_id}", conn)
        df.groupby(group_col)['amount'].sum().plot(kind='bar', title=flag)
        plt.tight_layout()
        plt.savefig(file)
        plt.clf()
    elif flag == "chart_all":
        df_exp = pd.read_sql(f"SELECT * FROM expenses WHERE user_id={user_id}", conn)
        df_inc = pd.read_sql(f"SELECT * FROM income WHERE user_id={user_id}", conn)
        df_inv = pd.read_sql(f"SELECT * FROM investments WHERE user_id={user_id}", conn)
        totals = [
            df_exp['amount'].sum(),
            df_inc['amount'].sum(),
            df_inv['amount'].sum()
        ]
        plt.bar(["Expenses", "Income", "Investments"], totals)
        plt.title("Expenses vs Income vs Investments")
        plt.savefig(file)
        plt.clf()
    # Extend for chart_ei and chart_ii similarly...
    return file
