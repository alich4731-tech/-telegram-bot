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


# =========================================================
# صفحه اصلی
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["menu_level"] = "main"

    keyboard = [
        ["🎓 دوره‌های آموزشی", "📱 ارتباط با ما"],
        ["🎬 ویدئوهای آموزشی"]
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


# =========================================================
# دوره‌های آموزشی
# =========================================================

async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["menu_level"] = "courses"

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


# =========================================================
# دوره آموزش پاور کوئری
# =========================================================

async def power_query(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["menu_level"] = "power_query"

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


# =========================================================
# لینک دوره پاور کوئری
# =========================================================

async def power_query_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "power_query_link"

    keyboard = [
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات و ثبت‌نام دوره، "
        "روی لینک زیر کلیک کنید:\n\n"
        "https://maliplusco.ir/product/%d8%af%d9%88%d8%b1%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
        reply_markup=reply_markup
    )


# =========================================================
# ارتباط با ما
# =========================================================

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["menu_level"] = "contact"

    keyboard = [
        ["📸 اینستاگرام"],
        ["📢 کانال تلگرام"],
        ["🟠 کانال روبیکا"],
        ["🏠 منوی اصلی"]
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


# =========================================================
# اینستاگرام
# =========================================================

async def instagram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "instagram"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📸 اینستاگرام:\n\n"
        "https://instagram.com/ali_chavoshi.official",
        reply_markup=reply_markup
    )


# =========================================================
# کانال تلگرام
# =========================================================

async def telegram_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "telegram"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📢 کانال تلگرام:\n\n"
        "https://t.me/Alichavoshiaccounting",
        reply_markup=reply_markup
    )


# =========================================================
# کانال روبیکا
# =========================================================

async def rubika(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "rubika"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🟠 کانال روبیکا:\n\n"
        "https://rubika.ir/Alichavoshiaccounting",
        reply_markup=reply_markup
    )


# =========================================================
# ویدئوهای آموزشی
# =========================================================

async def educational_videos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "educational_videos"

    keyboard = [
        ["📗 ویدئوهای آموزشی مقدماتی اکسل"],
        ["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"],
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🎬 ویدئوهای آموزشی\n\n"
        "سطح آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )


# =========================================================
# ویدئوهای آموزشی مقدماتی اکسل
# =========================================================

async def excel_beginner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "excel_beginner"

    keyboard = [
        ["📥 لینک‌های دانلود دوره"],
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📗 ویدئوهای آموزشی مقدماتی اکسل\n\n"
        "برای دریافت لینک‌های دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )


# =========================================================
# لینک دانلود مقدماتی اکسل
# =========================================================

async def excel_beginner_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "excel_beginner_download"

    keyboard = [
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی مقدماتی اکسل:\n\n"
        "https://my.uupload.ir/f/alichavoshi/ویدئو%20کوتاه%20آموزشی%20اکسل",
        reply_markup=reply_markup
    )


# =========================================================
# ویدئوهای آموزشی نیمه پیشرفته اکسل
# =========================================================

async def excel_intermediate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "excel_intermediate"

    keyboard = [
        ["📥 لینک‌های دانلود دوره"],
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\n"
        "برای دریافت لینک‌های دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )


# =========================================================
# لینک دانلود نیمه پیشرفته اکسل
# =========================================================

async def excel_intermediate_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "excel_intermediate_download"

    keyboard = [
        ["🔙 بازگشت"],
        ["🏠 منوی اصلی"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی سطح نیمه پیشرفته:\n\n"
        "https://my.uupload.ir/f/alichavoshi/ویدئو%20های%20آموزشی%20سطح%20نیمه%20پیشرفته",
        reply_markup=reply_markup
    )


# =========================================================
# بازگشت یک مرحله‌ای
# =========================================================

async def back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    level = context.user_data.get("menu_level")

    # -----------------------------------------------------
    # دوره‌های آموزشی
    # -----------------------------------------------------

    if level == "power_query":
        await courses(update, context)

    elif level == "power_query_link":
        await power_query(update, context)

    elif level == "courses":
        await start(update, context)

    # -----------------------------------------------------
    # ارتباط با ما
    # -----------------------------------------------------

    elif level == "instagram":
        await contact(update, context)

    elif level == "telegram":
        await contact(update, context)

    elif level == "rubika":
        await contact(update, context)

    # -----------------------------------------------------
    # ویدئوهای آموزشی
    # -----------------------------------------------------

    elif level == "educational_videos":
        await start(update, context)

    elif level == "excel_beginner":
        await educational_videos(update, context)

    elif level == "excel_beginner_download":
        await excel_beginner(update, context)

    elif level == "excel_intermediate":
        await educational_videos(update, context)

    elif level == "excel_intermediate_download":
        await excel_intermediate(update, context)

    # -----------------------------------------------------
    # حالت پیش‌فرض
    # -----------------------------------------------------

    else:
        await start(update, context)


# =========================================================
# منوی اصلی
# =========================================================

async def main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await start(update, context)


# =========================================================
# ساخت ربات
# =========================================================

app = Application.builder().token(TOKEN).build()


# =========================================================
# دستور /start
# =========================================================

app.add_handler(
    CommandHandler("start", start)
)


# =========================================================
# منوی اصلی
# =========================================================

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

app.add_handler(
    MessageHandler(
        filters.Text(["🎬 ویدئوهای آموزشی"]),
        educational_videos
    )
)


# =========================================================
# دوره‌های آموزشی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📊 دوره آموزش پاور کوئری"]),
        power_query
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📊 مشاهده و ثبت‌نام دوره"]),
        power_query_link
    )
)


# =========================================================
# ارتباط با ما
# =========================================================

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


# =========================================================
# ویدئوهای آموزشی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📗 ویدئوهای آموزشی مقدماتی اکسل"]),
        excel_beginner
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"]),
        excel_intermediate
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📥 لینک‌های دانلود دوره"]),
        lambda update, context: (
            excel_beginner_download(update, context)
            if context.user_data.get("menu_level") == "excel_beginner"
            else excel_intermediate_download(update, context)
        )
    )
)


# =========================================================
# بازگشت
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🔙 بازگشت"]),
        back
    )
)


# =========================================================
# منوی اصلی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🏠 منوی اصلی"]),
        main_menu
    )
)


# =========================================================
# اجرای Webhook
# =========================================================

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram"
)