import os

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
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


# =========================
# منوی اصلی
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🎓 دوره‌ها", "📱 ارتباط با ما"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات ما خوش آمدید 🌱\n\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=reply_markup
    )


# =========================
# دوره‌ها
# =========================

async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["📊 دوره آموزش پاور کوئری"],
        ["🔙 بازگشت"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🎓 دوره‌های آموزشی\n\n"
        "دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )


# =========================
# دوره پاور کوئری
# =========================

async def power_query(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 مشاهده و ثبت‌نام دوره پاور کوئری",
                url="https://maliplusco.ir/product/%d8%af%d9%88%d8%b1%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات و ثبت‌نام دوره، "
        "روی دکمه زیر بزنید.",
        reply_markup=reply_markup
    )

    # نمایش دکمه بازگشت در منوی پایین
    keyboard_back = [
        ["🔙 بازگشت به دوره‌ها"]
    ]

    reply_markup_back = ReplyKeyboardMarkup(
        keyboard_back,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "برای بازگشت به لیست دوره‌ها:",
        reply_markup=reply_markup_back
    )


# =========================
# ارتباط با ما
# =========================

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🔙 بازگشت"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"

        "📸 اینستاگرام:\n"
        "https://instagram.com/ali_chavoshi.official\n\n"

        "📢 کانال تلگرام:\n"
        "https://t.me/Alichavoshiaccounting\n\n"

        "🟠 کانال روبیکا:\n"
        "https://rubika.ir/Alichavoshiaccounting",
        reply_markup=reply_markup
    )


# =========================
# ساخت ربات
# =========================

app = Application.builder().token(TOKEN).build()


# /start
app.add_handler(
    CommandHandler("start", start)
)


# دوره‌ها
app.add_handler(
    MessageHandler(
        filters.Text(["🎓 دوره‌ها"]),
        courses
    )
)


# پاور کوئری
app.add_handler(
    MessageHandler(
        filters.Text(["📊 دوره آموزش پاور کوئری"]),
        power_query
    )
)


# ارتباط با ما
app.add_handler(
    MessageHandler(
        filters.Text(["📱 ارتباط با ما"]),
        contact
    )
)


# بازگشت از دوره‌ها به منوی اصلی
app.add_handler(
    MessageHandler(
        filters.Text(["🔙 بازگشت"]),
        start
    )
)


# بازگشت از پاور کوئری به دوره‌ها
app.add_handler(
    MessageHandler(
        filters.Text(["🔙 بازگشت به دوره‌ها"]),
        courses
    )
)


# =========================
# Webhook
# =========================

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram"
)