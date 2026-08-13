import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
URL = os.getenv("RENDER_EXTERNAL_URL")


# پیام /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["▶️ استارت", "📱 ارتباط با ما"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات ما خوش آمدید 🌱\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=reply_markup
    )


# دکمه ارتباط با ما
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"
        "📸 اینستاگرام:\n"
        "https://instagram.com/ali_chavoshi.official\n\n"
        "📢 کانال تلگرام:\n"
        "https://t.me/Alichavoshiaccounting"
    )


# ساخت ربات
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.Text(["📱 ارتباط با ما"]),
        contact
    )
)


app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram"
)
