import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# =========================================================
# تنظیمات
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
URL = os.getenv("RENDER_EXTERNAL_URL")


# =========================================================
# تابع ساخت کیبورد
# =========================================================

def create_keyboard(buttons):
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )


# =========================================================
# منوی اصلی
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["menu_level"] = "main"

    keyboard = [
        ["🎓 دوره‌های آموزشی", "🎬 ویدئوهای آموزشی"],
        ["📱 ارتباط با ما"]
    ]

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات ما خوش آمدید 🌱\n\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# دوره‌های آموزشی
# =========================================================

async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["menu_level"] = "courses"

    keyboard = [
        ["🏫 دوره‌های آموزشی حضوری"],
        ["💻 دوره‌های آموزشی آنلاین"],
        ["🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "🎓 دوره‌های آموزشی\n\n"
        "نوع دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# دوره‌های آموزشی حضوری
# =========================================================

async def in_person_courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "in_person_courses"

    keyboard = [
        ["📊 دوره آموزش پاور کوئری"],
        ["📑 دوره سامانه مودیان"],
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "🏫 دوره‌های آموزشی حضوری\n\n"
        "دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# دوره‌های آموزشی آنلاین
# =========================================================

async def online_courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "online_courses"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "💻 دوره‌های آموزشی آنلاین\n\n"
        "در حال حاضر دوره‌ای در این بخش قرار نگرفته است.",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# دوره سامانه مودیان
# =========================================================

async def tax_system(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "tax_system"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📑 دوره آموزش سامانه مودیان\n\n"
        "اطلاعات این دوره به‌زودی در ربات قرار خواهد گرفت.",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# دوره آموزش پاور کوئری
# =========================================================

async def power_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "power_query"

    keyboard = [
        ["📊 مشاهده و ثبت‌نام دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات دوره و ثبت‌نام، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
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
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات و ثبت‌نام دوره، "
        "روی لینک زیر کلیک کنید:\n\n"
        "https://maliplusco.ir/product/%d8%af%d9%88%d8%b1%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# ارتباط با ما
# =========================================================

async def contact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "contact"

    keyboard = [
        ["📸 اینستاگرام"],
        ["📢 کانال تلگرام"],
        ["🟠 کانال روبیکا"],
        ["🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
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

    await update.message.reply_text(
        "📸 اینستاگرام:\n\n"
        "https://instagram.com/ali_chavoshi.official",
        reply_markup=create_keyboard(keyboard)
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

    await update.message.reply_text(
        "📢 کانال تلگرام:\n\n"
        "https://t.me/Alichavoshiaccounting",
        reply_markup=create_keyboard(keyboard)
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

    await update.message.reply_text(
        "🟠 کانال روبیکا:\n\n"
        "https://rubika.ir/Alichavoshiaccounting",
        reply_markup=create_keyboard(keyboard)
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
        ["🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "🎬 ویدئوهای آموزشی\n\n"
        "سطح آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
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
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📗 ویدئوهای آموزشی مقدماتی اکسل\n\n"
        "برای دریافت لینک دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
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
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی مقدماتی اکسل:\n\n"
        "https://my.uupload.ir/d/pVZXk",
        reply_markup=create_keyboard(keyboard)
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
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\n"
        "برای دریافت لینک دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard)
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
        ["🔙 بازگشت", "🏠 منوی اصلی"]
    ]

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی سطح نیمه پیشرفته:\n\n"
        "https://my.uupload.ir/d/YL2XN",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# سیستم بازگشت
# =========================================================

async def back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    level = context.user_data.get("menu_level")

    # -----------------------------------------------------
    # دوره‌های آموزشی
    # -----------------------------------------------------

    if level == "in_person_courses":

        await courses(update, context)

    elif level == "online_courses":

        await courses(update, context)

    elif level == "tax_system":

        await in_person_courses(update, context)

    elif level == "power_query":

        await in_person_courses(update, context)

    elif level == "power_query_link":

        await power_query(update, context)

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
# مدیریت لینک دانلود
# =========================================================

async def download_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    level = context.user_data.get("menu_level")

    if level == "excel_beginner":

        await excel_beginner_download(update, context)

    elif level == "excel_intermediate":

        await excel_intermediate_download(update, context)


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
        filters.Text(["🎬 ویدئوهای آموزشی"]),
        educational_videos
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📱 ارتباط با ما"]),
        contact
    )
)


# =========================================================
# دوره‌های آموزشی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🏫 دوره‌های آموزشی حضوری"]),
        in_person_courses
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["💻 دوره‌های آموزشی آنلاین"]),
        online_courses
    )
)


# =========================================================
# دوره‌های حضوری
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📊 دوره آموزش پاور کوئری"]),
        power_query
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📑 دوره سامانه مودیان"]),
        tax_system
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


# =========================================================
# لینک‌های دانلود
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📥 لینک‌های دانلود دوره"]),
        download_links
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