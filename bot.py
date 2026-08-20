import os

from openai import OpenAI

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# =========================================================
# تنظیمات اصلی
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
URL = os.getenv("RENDER_EXTERNAL_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

AI_MODEL = os.getenv("AI_MODEL", "gpt-5.6-luna")
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "500"))
AI_HISTORY_MESSAGES = int(os.getenv("AI_HISTORY_MESSAGES", "4"))
AI_HISTORY_CHAR_LIMIT = int(os.getenv("AI_HISTORY_CHAR_LIMIT", "1200"))


# =========================================================
# بررسی تنظیمات
# =========================================================

if not TOKEN:
    raise ValueError("BOT_TOKEN در Environment Variables تنظیم نشده است.")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY تنظیم نشده است.")


# =========================================================
# اتصال به OpenAI
# =========================================================

client = None

if OPENAI_API_KEY:
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )


# =========================================================
# تنظیمات هوش مصنوعی
# =========================================================

AI_SYSTEM_PROMPT = """
نقش: دستیار هوشمند حسابداری ACN.

فقط به موضوعات مرتبط با حسابداری و مالی، حسابرسی، مالیات، اکسل و Power Query مرتبط با حسابداری پاسخ بده.

قواعد:
- فارسی، دقیق، حرفه‌ای و مستقیم بنویس.
- در هر پاسخ حتماً بین ۱ تا ۳ ایموجی مرتبط و طبیعی استفاده کن.
- از استفاده بیش از ۳ ایموجی در یک پاسخ خودداری کن.
- اول منظور سؤال را تشخیص بده و به عبارت کلیدی و زمینه توجه کن.
- فقط همان چیزی را پاسخ بده که کاربر خواسته است؛ اطلاعات جانبی اضافه نکن.
- سؤال ساده: پاسخ کوتاه و مستقیم.
- سؤال آموزشی: فقط به اندازه لازم توضیح بده.
- مثال، جدول، ثبت بدهکار/بستانکار یا مراحل را فقط وقتی لازم است یا کاربر خواسته ارائه کن.
- مقدمه، جمع‌بندی، تکرار سؤال و توضیحات تشریفاتی اضافه نکن.
- در پایان پاسخ «اگر خواستی...»، «در صورت نیاز...»، «بگو تا...» یا پیشنهاد ادامه گفتگو اضافه نکن.
- اگر سؤال مبهم است و بدون ابهام نمی‌توان پاسخ دقیق داد، فقط یک سؤال کوتاه برای روشن شدن منظور بپرس.
- اگر سؤال کوتاه و مشخصی مثل «فرمول اساسی حسابداری چیست؟» پرسیده شد، فقط همان پاسخ را بده و سراغ مباحث دیگر نرو.
- در ثبت‌های حسابداری از «بدهکار» و «بستانکار» استفاده کن.
- درباره قوانین و مقررات مالیاتی ایران، اگر از به‌روز بودن اطلاعات مطمئن نیستی، آن را قطعی بیان نکن.
- برای سؤال کاملاً خارج از حوزه، فقط بگو:
«این دستیار برای پاسخ‌گویی به پرسش‌های حسابداری، مالی، حسابرسی، مالیات و اکسل/Power Query مرتبط با حسابداری طراحی شده است.»
"""


# =========================================================
# ساخت کیبورد
# =========================================================

def create_keyboard(buttons):

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )


# =========================================================
# منوی اصلی
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "main"
    context.user_data["ai_mode"] = False

    keyboard = [
        ["🎓 دوره‌های آموزشی", "🎬 ویدئوهای آموزشی"],
        ["🤖 دستیار هوش مصنوعی"],
        ["📱 ارتباط با ما"]
    ]

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات ما خوش آمدید 🌱\n\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# ورود به هوش مصنوعی
# =========================================================

async def ai_assistant(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "ai"
    context.user_data["ai_mode"] = True
    context.user_data["ai_history"] = []

    keyboard = [
        ["🔙 بازگشت"]
    ]

    await update.message.reply_text(
        "🤖✨ به دستیار هوشمند حسابداری ACN خوش آمدید\n\n"
        "📚 سؤال خود را درباره یکی از موضوعات زیر ارسال کنید:\n\n"
        "• 🧾 حسابداری و مالی\n"
        "• 🔍 حسابرسی\n"
        "• 💰 مالیات\n"
        "• 📊 اکسل و Power Query در حسابداری\n\n"
        "🔙 برای خروج از این بخش، گزینه «بازگشت» را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard)
    )


# =========================================================
# خروج از هوش مصنوعی
# =========================================================

# =========================================================
# سوال از هوش مصنوعی
# =========================================================

async def ask_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """ارسال سؤال به OpenAI با پاسخ کوتاه و تاریخچه محدود."""

    if not context.user_data.get("ai_mode", False):
        return

    user_question = update.message.text.strip()

    if not user_question:
        return

    # سقف ورودی برای جلوگیری از ارسال متن‌های بسیار بزرگ
    user_question = user_question[:3000]

    if not OPENAI_API_KEY or client is None:
        await update.message.reply_text(
            "⚠️ اتصال دستیار هوشمند تنظیم نشده است.\n"
            "OPENAI_API_KEY را در Environment Variables رندر بررسی کنید."
        )
        return

    # فقط چند پیام اخیر برای دنبال کردن سؤال‌های وابسته.
    # این کار از ارسال کل مکالمه و افزایش بی‌دلیل مصرف توکن جلوگیری می‌کند.
    history = context.user_data.setdefault("ai_history", [])
    recent_history = history[-AI_HISTORY_MESSAGES:]

    input_parts = []

    for item in recent_history:
        input_parts.append({
            "role": item["role"],
            "content": item["content"]
        })

    input_parts.append({
        "role": "user",
        "content": user_question
    })

    thinking_message = await update.message.reply_text(
        "🤖 در حال بررسی سؤال شما..."
    )

    try:
        response = client.responses.create(
            model=AI_MODEL,
            instructions=AI_SYSTEM_PROMPT,
            input=input_parts,
            max_output_tokens=AI_MAX_OUTPUT_TOKENS
        )

        answer = (response.output_text or "").strip()

        if not answer:
            answer = "⚠️ پاسخی از سرویس هوش مصنوعی دریافت نشد."

        # ذخیره تاریخچه با سقف طول
        history.append({
            "role": "user",
            "content": user_question[:AI_HISTORY_CHAR_LIMIT]
        })

        history.append({
            "role": "assistant",
            "content": answer[:AI_HISTORY_CHAR_LIMIT]
        })

        del history[:-AI_HISTORY_MESSAGES]

        # تقسیم پیام‌های طولانی برای محدودیت تلگرام
        max_length = 4000

        if len(answer) <= max_length:
            await thinking_message.edit_text(answer)

        else:
            await thinking_message.edit_text(answer[:max_length])

            remaining_text = answer[max_length:]

            while remaining_text:
                chunk = remaining_text[:max_length]
                await update.message.reply_text(chunk)
                remaining_text = remaining_text[max_length:]

    except Exception as e:
        print(f"OPENAI ERROR [{type(e).__name__}]: {e}")

        await thinking_message.edit_text(
            "⚠️ در پردازش سؤال مشکلی ایجاد شد.\n"
            "لطفاً چند لحظه بعد دوباره تلاش کنید."
        )


# =========================================================
# دوره‌های آموزشی
# =========================================================

async def courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
# دوره‌های حضوری
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
# دوره‌های آنلاین
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
# دوره پاور کوئری
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
        "https://maliplusco.ir/product/%d9%85%d9%88%d8%b1%d8%b3%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
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
        "https://t.me/Alichavavoshiaccounting",
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
# اکسل مقدماتی
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
# دانلود اکسل مقدماتی
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
# اکسل نیمه پیشرفته
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
# دانلود اکسل نیمه پیشرفته
# =========================================================

async def excel_intermediate_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["menu_level"] = "excel_intermediate_download"

    # دکمه‌های لینک مستقیم هر قسمت
    keyboard = [

        [
            InlineKeyboardButton(
                "قسمت اول - کلیپ آموزشی تابع Concatenate در اکسل",
                url="https://my.uupload.ir/p/0jka5XvR"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت دوم - کلیپ آموزشی تابع Textjoin در نرم افزار اکسل",
                url="https://my.uupload.ir/p/2KDmGQDB"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت سوم - کلیپ آموزشی تابع If و ترکیب آن با تابع Textjoin در نرم افزار اکسل",
                url="https://my.uupload.ir/p/n2JGpEwK"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت چهارم - کلیپ آموزشی تابع And و ترکیب آن با تابع If در نرم افزار اکسل",
                url="https://my.uupload.ir/p/BvxABejW"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت پنجم - کلیپ آموزشی تابع Or و ترکیب آن با تابع If در نرم افزار اکسل",
                url="https://my.uupload.ir/p/JgwO5yWN"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت ششم - کلیپ آموزشی تابع Xlookup در نرم افزار اکسل",
                url="https://my.uupload.ir/p/ODwN9w42"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت هفتم - کلیپ آموزشی تابع Sumifs در نرم افزار اکسل",
                url="https://my.uupload.ir/p/1LdxaM00"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت هشتم - کلیپ آموزشی تابع Vlookup و تفاوت آن با تابع Xlookup در نرم افزار اکسل",
                url="https://my.uupload.ir/p/aG5a79xw"
            )
        ],

        [
            InlineKeyboardButton(
                "قسمت نهم (قسمت آخر) - کلیپ آموزشی تابع Hlookup و تفاوت آن با تابع Xlookup در نرم افزار اکسل",
                url="https://my.uupload.ir/p/eyJLaKYX"
            )
        ]

    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📘 لینک دانلود ویدئوهای آموزشی نیمه پیشرفته اکسل:\n\n"
        "قسمت مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )


# =========================================================
# بازگشت
# =========================================================

async def back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    level = context.user_data.get("menu_level")

    if level in ["in_person_courses", "online_courses"]:
        await courses(update, context)

    elif level in ["tax_system", "power_query"]:
        await in_person_courses(update, context)

    elif level == "power_query_link":
        await power_query(update, context)

    elif level in ["instagram", "telegram", "rubika"]:
        await contact(update, context)

    elif level == "excel_beginner":
        await educational_videos(update, context)

    elif level == "excel_beginner_download":
        await excel_beginner(update, context)

    elif level == "excel_intermediate":
        await educational_videos(update, context)

    elif level == "excel_intermediate_download":
        await excel_intermediate(update, context)

    else:
        await start(update, context)


# =========================================================
# لینک‌های دانلود
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
# ساخت Application
# =========================================================

app = Application.builder().token(TOKEN).build()


# =========================================================
# /start
# =========================================================

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


# =========================================================
# هوش مصنوعی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🤖 دستیار هوش مصنوعی"]),
        ai_assistant
    )
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
# لینک دانلود
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
        start
    )
)


# =========================================================
# پیام‌های متنی AI
# =========================================================

MENU_BUTTONS = [
    "🤖 دستیار هوش مصنوعی",
    "🎓 دوره‌های آموزشی",
    "🎬 ویدئوهای آموزشی",
    "📱 ارتباط با ما",
    "🏫 دوره‌های آموزشی حضوری",
    "💻 دوره‌های آموزشی آنلاین",
    "📊 دوره آموزش پاور کوئری",
    "📑 دوره سامانه مودیان",
    "📊 مشاهده و ثبت‌نام دوره",
    "📸 اینستاگرام",
    "📢 کانال تلگرام",
    "🟠 کانال روبیکا",
    "📗 ویدئوهای آموزشی مقدماتی اکسل",
    "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل",
    "📥 لینک‌های دانلود دوره",
    "🔙 بازگشت",
    "🏠 منوی اصلی"
]


app.add_handler(
    MessageHandler(
        filters.TEXT
        & ~filters.COMMAND
        & ~filters.Text(MENU_BUTTONS),
        ask_ai
    )
)


# =========================================================
# اجرای Webhook روی Render
# =========================================================

if not URL:
    raise ValueError(
        "RENDER_EXTERNAL_URL در Environment Variables تنظیم نشده است."
    )


app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram"
)
