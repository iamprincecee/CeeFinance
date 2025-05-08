# main.py

import os
import logging
from telegram.ext import CommandHandler  # Add this at the top if missing
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler,
    CallbackQueryHandler, filters
)
from db import (
    save_expense, save_income, save_investment, save_loss,
    init_db
)
from reports import generate_report, generate_chart

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Initialize database
init_db()

# Main menu layout
main_menu = ReplyKeyboardMarkup([
    ["➕ Add Expense", "💵 Add Income"],
    ["📈 Add Investment", "📉 Log Business Loss"],
    ["📊 View Report", "📈 View Charts"]
], resize_keyboard=True)


# Handle button-driven messages
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

    elif text == "📉 Log Business Loss":
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


# Handle inline button callbacks
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    chat_id = update.effective_user.id
    await update.callback_query.answer()

    if data.startswith(("rpt", "fmt", "view")):
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


# Build and start the bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))  
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()
