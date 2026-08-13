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


# ==========================================
# صفحه اصلی
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🎓 دوره‌های آموزشی", "📱 ارتباط با ما"]
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


# ==========================================
# دوره‌های آموزشی
# ==========================================

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


# ==========================================
# دوره پاور کوئری
# ==========================================

async def power_query(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["📊 مشاهده و ثبت‌نام دوره"],
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات دوره و ثبت‌نام، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )


# ==========================================
# لینک دوره پاور کوئری
# ==========================================

async def power_query_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📊 مشاهده و ثبت‌نام دوره پاور کوئری:\n\n"
        "https://maliplusco.ir/product/%d8%af%d9%88%d8%b1%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
        reply_markup=reply_markup
    )


# ==========================================
# ارتباط با ما
# ==========================================

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["📸 اینستاگرام"],
        ["📢 کانال تلگرام"],
        ["🟠 کانال روبیکا"],
        ["🔙 بازگشت"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )


# ==========================================
# اینستاگرام
# ==========================================

async def instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📸 اینستاگرام:\n\n"
        "https://instagram.com/ali_chavoshi.official"
    )


# ==========================================
# تلگرام
# ==========================================

async def telegram_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📢 کانال تلگرام:\n\n"
        "https://t.me/Alichavoshiaccounting"
    )


# ==========================================
# روبیکا
# ==========================================

async def rubika(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🟠 کانال روبیکا:\n\n"
        "https://rubika.ir/Alichavoshiaccounting"
    )


# ==========================================
# ساخت ربات
# ==========================================

app = Application.builder().token(TOKEN).build()


# ==========================================
# /start
# ==========================================

app.add_handler(
    CommandHandler("start", start)
)


# ==========================================
# صفحه اصلی
# ==========================================

app.add_handler(
    MessageHandler(
        filters.Text(["🎓 دوره‌های آموزشی"]),
        courses
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📱 ارتباط با ما"]),
        contact
    )
)


# ==========================================
# دوره آموزش پاور کوئری
# ==========================================

app.add_handler(
    MessageHandler(
        filters.Text(["📊 دوره آموزش پاور کوئری"]),
        power_query
    )
)


# ==========================================
# مشاهده دوره
# ==========================================

app.add_handler(
    MessageHandler(
        filters.Text(["📊 مشاهده و ثبت‌نام دوره"]),
        power_query_link
    )
)


# ==========================================
# ارتباط با ما
# ==========================================

app.add_handler(
    MessageHandler(
        filters.Text(["📸 اینستاگرام"]),
        instagram
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📢 کانال تلگرام"]),
        telegram_channel
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["🟠 کانال روبیکا"]),
        rubika
    )
)


# ==========================================
# بازگشت یک مرحله‌ای
# ==========================================

# از دوره‌های آموزشی → صفحه اصلی
app.add_handler(
    MessageHandler(
        filters.Text(["🔙 بازگشت"]),
        start
    )
)


# ==========================================
# منوی اصلی
# ==========================================

app.add_handler(
    MessageHandler(
        filters.Text(["🏠 منوی اصلی"]),
        start
    )
)


# ==========================================
# اجرای Webhook
# ==========================================

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram"
)