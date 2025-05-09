# main.py

import os
import logging
from telegram.ext import CommandHandler
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler,
    CallbackQueryHandler, filters
)
from db import (
    save_expense, save_income, save_investment, save_loss,
    init_db, get_recent_expenses, update_expense,
    get_recent_income, update_income,
    get_recent_investments, update_investment,
    get_recent_losses, update_loss,
    get_paginated_entries, delete_entry, search_entries
)
from reports import generate_report, generate_chart

logging.basicConfig(level=logging.INFO)
load_dotenv()
TOKEN = os.getenv("TOKEN")

init_db()

main_menu = ReplyKeyboardMarkup([
    ["➕ Add Expense", "💵 Add Income"],
    ["📈 Add Investment", "📉 Log Incurred Losses"],
    ["📊 View Report", "📈 View Charts"],
    ["✏️ Edit Entry", "🔍 Search Data"],
    ["🧾 View Entries"]
], resize_keyboard=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_user.id
    action = context.user_data.get("action")

    if text == "➕ Add Expense":
        await update.message.reply_text("Enter expense as: amount category")
        context.user_data["action"] = "add_expense"

    elif text == "💵 Add Income":
        await update.message.reply_text("Enter income as: amount source")
        context.user_data["action"] = "add_income"

    elif text == "📈 Add Investment":
        await update.message.reply_text("Enter investment as: amount type ROI% interval")
        context.user_data["action"] = "add_investment"

    elif text == "📉 Log Incurred Losses":
        await update.message.reply_text("Enter loss as: amount reason")
        context.user_data["action"] = "add_loss"

    elif text == "📊 View Report":
        buttons = [
            [InlineKeyboardButton("Last 7 Days", callback_data="rpt_7d"),
             InlineKeyboardButton("Last 30 Days", callback_data="rpt_30d")],
            [InlineKeyboardButton("Custom Date", callback_data="rpt_custom")],
            [InlineKeyboardButton("PDF", callback_data="fmt_pdf"),
             InlineKeyboardButton("Spreadsheet", callback_data="fmt_xlsx")],
            [InlineKeyboardButton("Totals Only", callback_data="view_totals"),
             InlineKeyboardButton("Full Breakdown", callback_data="view_full")]
        ]
        await update.message.reply_text("Choose report options:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "📈 View Charts":
        buttons = [
            [InlineKeyboardButton("Expenses", callback_data="chart_exp"),
             InlineKeyboardButton("Income", callback_data="chart_inc")],
            [InlineKeyboardButton("Investments", callback_data="chart_inv")],
            [InlineKeyboardButton("Exp vs Inc", callback_data="chart_ei"),
             InlineKeyboardButton("Inc vs Inv", callback_data="chart_ii")],
            [InlineKeyboardButton("All 3", callback_data="chart_all")]
        ]
        await update.message.reply_text("Choose chart type:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "✏️ Edit Entry":
        buttons = [
            [InlineKeyboardButton("Edit Expense", callback_data="editcat_expense")],
            [InlineKeyboardButton("Edit Income", callback_data="editcat_income")],
            [InlineKeyboardButton("Edit Investment", callback_data="editcat_investment")],
            [InlineKeyboardButton("Edit Loss", callback_data="editcat_loss")]
        ]
        await update.message.reply_text("What would you like to edit?", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "🧾 View Entries":
        buttons = [
            [InlineKeyboardButton("Expenses", callback_data="view_expenses_0")],
            [InlineKeyboardButton("Income", callback_data="view_income_0")],
            [InlineKeyboardButton("Investments", callback_data="view_investments_0")],
            [InlineKeyboardButton("Losses", callback_data="view_losses_0")]
        ]
        await update.message.reply_text("Choose data to view:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "🔍 Search Data":
        await update.message.reply_text("Enter search as: category,date (e.g. groceries,2025-05)")
        context.user_data["action"] = "search_data"

    elif action == "add_expense":
        amount, category = text.split(maxsplit=1)
        save_expense(chat_id, amount, category)
        await update.message.reply_text(f"✅ Logged {amount} for {category}")
        context.user_data["action"] = None

    elif action == "add_income":
        amount, source = text.split(maxsplit=1)
        save_income(chat_id, amount, source)
        await update.message.reply_text(f"✅ Logged {amount} from {source}")
        context.user_data["action"] = None

    elif action == "add_investment":
        amount, inv_type, roi, interval = text.split(maxsplit=3)
        save_investment(chat_id, amount, inv_type, roi, interval)
        await update.message.reply_text(f"✅ Investment logged: {amount} in {inv_type} with {roi} ROI ({interval})")
        context.user_data["action"] = None

    elif action == "add_loss":
        amount, reason = text.split(maxsplit=1)
        save_loss(chat_id, amount, reason)
        await update.message.reply_text(f"✅ Loss of {amount} logged: {reason}")
        context.user_data["action"] = None

    elif action == "search_data":
        try:
            category, date = text.split(",")
            results = search_entries(chat_id, category.strip(), date.strip())
            if results:
                output = "\n".join([
                    f"{r['amount']} {r.get('category') or r.get('source') or r.get('type') or r.get('reason')} ({r['date']})"
                    for r in results
                ])
                await update.message.reply_text(f"🔍 Results:\n{output}")
            else:
                await update.message.reply_text("No results found.")
        except:
            await update.message.reply_text("⚠️ Use format: category,date")
        context.user_data["action"] = None


    elif action == "edit_expense":
        try:
            amount, category = [v.strip() for v in text.split(",")]
            index = context.user_data.get("edit_index")
            entries = context.user_data.get("edit_list")
            entry_id = entries[index]['id']
            update_expense(entry_id, amount, category)
            await update.message.reply_text(f"✅ Expense updated to {amount} for {category}.")
        except:
            await update.message.reply_text("⚠️ Invalid format. Use: amount, category")
        context.user_data["action"] = None

    elif action == "edit_income":
        try:
            amount, source = [v.strip() for v in text.split(",")]
            index = context.user_data.get("edit_index")
            entries = context.user_data.get("edit_list")
            entry_id = entries[index]['id']
            update_income(entry_id, amount, source)
            await update.message.reply_text(f"✅ Income updated to {amount} from {source}.")
        except:
            await update.message.reply_text("⚠️ Invalid format. Use: amount, source")
        context.user_data["action"] = None

    elif action == "edit_investment":
        try:
            amount, inv_type = [v.strip() for v in text.split(",")]
            index = context.user_data.get("edit_index")
            entries = context.user_data.get("edit_list")
            entry_id = entries[index]['id']
            update_investment(entry_id, amount, inv_type)
            await update.message.reply_text(f"✅ Investment updated to {amount} in {inv_type}.")
        except:
            await update.message.reply_text("⚠️ Invalid format. Use: amount, type")
        context.user_data["action"] = None

    elif action == "edit_loss":
        try:
            amount, reason = [v.strip() for v in text.split(",")]
            index = context.user_data.get("edit_index")
            entries = context.user_data.get("edit_list")
            entry_id = entries[index]['id']
            update_loss(entry_id, amount, reason)
            await update.message.reply_text(f"✅ Loss updated to {amount} for {reason}.")
        except:
            await update.message.reply_text("⚠️ Invalid format. Use: amount, reason")
        context.user_data["action"] = None


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    chat_id = update.effective_user.id
    await update.callback_query.answer()

    def format_entries(entries, prefix):
        return [[InlineKeyboardButton(
            f"{e['amount']} {e.get('category') or e.get('source') or e.get('type') or e.get('reason')} ({e['date']})",
            callback_data=f"{prefix}_{i}"
        )] for i, e in enumerate(entries)]

    if data.startswith("view_"):
        _, kind, page = data.split("_")
        entries = get_paginated_entries(chat_id, kind, int(page))
        if not entries:
            await update.callback_query.message.reply_text("No data found.")
            return
        context.user_data["edit_list"] = entries
        buttons = format_entries(entries, f"del_{kind}")
        nav = []
        if int(page) > 0:
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"view_{kind}_{int(page) - 1}"))
        if len(entries) == 5:
            nav.append(InlineKeyboardButton("➡️ Next", callback_data=f"view_{kind}_{int(page) + 1}"))
        if nav:
            buttons.append(nav)
        await update.callback_query.message.reply_text(
            f"{kind.capitalize()} - Page {int(page) + 1}:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("del_"):
        _, kind, index = data.split("_")
        entries = context.user_data.get("edit_list")
        entry = entries[int(index)]
        delete_entry(kind, entry['id'])
        await update.callback_query.message.reply_text(f"🗑️ Deleted {kind[:-1]} entry.")

    elif data.startswith("edit_"):
        index = int(data.split("_")[-1])
        context.user_data["edit_index"] = index
        if "exp" in data:
            context.user_data["action"] = "edit_expense"
            await update.callback_query.message.reply_text("Enter the corrected value in format: amount, category")
        elif "inc" in data:
            context.user_data["action"] = "edit_income"
            await update.callback_query.message.reply_text("Enter the corrected value in format: amount, source")
        elif "inv" in data:
            context.user_data["action"] = "edit_investment"
            await update.callback_query.message.reply_text("Enter the corrected value in format: amount, type")
        elif "loss" in data:
            context.user_data["action"] = "edit_loss"
            await update.callback_query.message.reply_text("Enter the corrected value in format: amount, reason")

    elif data.startswith("editcat_"):
        kind = data.split("_")[1]
        if kind == "expense":
            entries = get_recent_expenses(chat_id)
            prefix = "edit_exp"
        elif kind == "income":
            entries = get_recent_income(chat_id)
            prefix = "edit_inc"
        elif kind == "investment":
            entries = get_recent_investments(chat_id)
            prefix = "edit_inv"
        elif kind == "loss":
            entries = get_recent_losses(chat_id)
            prefix = "edit_loss"
        else:
            return

        if not entries:
            await update.callback_query.message.reply_text("No recent entries to edit.")
            return
        context.user_data["edit_list"] = entries
        buttons = format_entries(entries, prefix)
        await update.callback_query.message.reply_text("Select an entry to edit:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith(("rpt", "fmt", "view")):
        file = generate_report(chat_id, data)
        await update.callback_query.message.reply_document(open(file, "rb"))

    elif data.startswith("chart"):
        file = generate_chart(chat_id, data)
        await update.callback_query.message.reply_photo(photo=open(file, "rb"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to CeeFiBot!\n\nUse the menu below to start tracking your finances:",
        reply_markup=main_menu
    )


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()
