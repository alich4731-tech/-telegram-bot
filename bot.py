import os

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

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
# منوی اصلی
# ==========================================

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


# ==========================================
# منوی دوره‌ها
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
        "برای مشاهده اطلاعات دوره، گزینه زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )


# ==========================================
# دوره پاور کوئری
# ==========================================

async def power_query(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 مشاهده و ثبت‌نام دوره",
                url="https://maliplusco.ir/product/%d8%af%d9%88%d8%b1%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به دوره‌ها",
                callback_data="back_courses"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات دوره، سرفصل‌ها و ثبت‌نام "
        "روی دکمه زیر بزنید:",
        reply_markup=reply_markup
    )


# ==========================================
# ارتباط با ما
# ==========================================

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📸 اینستاگرام",
                url="https://instagram.com/ali_chavoshi.official"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 کانال تلگرام",
                url="https://t.me/Alichavoshiaccounting"
            )
        ],
        [
            InlineKeyboardButton(
                "🟠 کانال روبیکا",
                url="https://rubika.ir/Alichavoshiaccounting"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_main"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"
        "برای ورود به شبکه‌های اجتماعی، "
        "گزینه مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )


# ==========================================
# مدیریت دکمه‌های Inline
# ==========================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    # بازگشت به منوی اصلی
    if query.data == "back_main":

        keyboard = [
            ["🎓 دوره‌ها", "📱 ارتباط با ما"]
        ]

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        await query.message.reply_text(
            "منوی اصلی:",
            reply_markup=reply_markup
        )

    # بازگشت به دوره‌ها
    elif query.data == "back_courses":

        keyboard = [
            ["📊 دوره آموزش پاور کوئری"],
            ["🔙 بازگشت"]
        ]

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        await query.message.reply_text(
            "🎓 دوره‌های آموزشی\n\n"
            "دوره مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup
        )


# ==========================================
# Handler ها
# ==========================================

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


# دکمه‌های Inline
app.add_handler(
    MessageHandler(
        filters.ALL,
        button_handler
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