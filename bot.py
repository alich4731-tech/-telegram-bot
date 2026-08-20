import os
import base64
import html
import re

from openai import OpenAI

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# تنظیمات اصلی
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
URL = os.getenv("RENDER_EXTERNAL_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

AI_MODEL = os.getenv(
    "AI_MODEL",
    "gpt-5.6-luna"
)

AI_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "AI_MAX_OUTPUT_TOKENS",
        "2200"
    )
)

AI_MAX_OUTPUT_TOKENS_LEGAL = int(
    os.getenv(
        "AI_MAX_OUTPUT_TOKENS_LEGAL",
        "3600"
    )
)

AI_MAX_OUTPUT_TOKENS_HARD_CAP = int(
    os.getenv(
        "AI_MAX_OUTPUT_TOKENS_HARD_CAP",
        "5200"
    )
)

AI_HISTORY_MESSAGES = int(
    os.getenv(
        "AI_HISTORY_MESSAGES",
        "4"
    )
)

AI_HISTORY_CHAR_LIMIT = int(
    os.getenv(
        "AI_HISTORY_CHAR_LIMIT",
        "1200"
    )
)

AI_IMAGE_MAX_BYTES = int(
    os.getenv(
        "AI_IMAGE_MAX_BYTES",
        "10000000"
    )
)

AI_WEB_SEARCH_CONTEXT = os.getenv(
    "AI_WEB_SEARCH_CONTEXT",
    "high"
)


# =========================================================
# بررسی Environment Variables
# =========================================================

if not TOKEN:
    raise ValueError(
        "BOT_TOKEN در Environment Variables تنظیم نشده است."
    )

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY تنظیم نشده است."
    )

if not URL:
    raise ValueError(
        "RENDER_EXTERNAL_URL در Environment Variables تنظیم نشده است."
    )


# =========================================================
# اتصال به OpenAI
# =========================================================

client = None

if OPENAI_API_KEY:
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )


# =========================================================
# پرامپت اصلی هوش مصنوعی
# =========================================================

AI_SYSTEM_PROMPT = """
نقش تو:
دستیار هوشمند حسابداری ACN.

تو یک دستیار تخصصی برای حسابداری، مالی، حسابرسی، مالیات، تامین اجتماعی
و اکسل و Power Query مرتبط با حسابداری در ایران هستی.

پاسخ‌ها باید فارسی، دقیق، حرفه‌ای، مستقیم و قابل فهم باشند.


========================
حوزه‌های مجاز
========================

به پرسش‌های مرتبط با این موضوعات پاسخ بده:

• حسابداری و مالی
• حسابرسی
• مالیات
• تامین اجتماعی
• حقوق و دستمزد
• اکسل و Power Query مرتبط با حسابداری
• سایر موضوعات مستقیم مرتبط با حسابداری

اگر سؤال کاملاً خارج از این حوزه‌ها بود، فقط بگو:

«این دستیار برای پاسخ‌گویی به پرسش‌های حسابداری، مالی، حسابرسی، مالیات، تامین اجتماعی و اکسل/Power Query مرتبط با حسابداری طراحی شده است.»


========================
تحلیل سؤال
========================

قبل از پاسخ، سؤال را از نظر موارد زیر بررسی کن:

1. منظور دقیق کاربر چیست؟
2. آیا سؤال ابهام اساسی دارد؟
3. آیا سال یا دوره زمانی روی پاسخ اثر دارد؟
4. آیا نوع معامله روی پاسخ اثر دارد؟
5. آیا سیستم موجودی دائمی یا ادواری مهم است؟
6. آیا نقدی یا نسیه بودن معامله مهم است؟
7. آیا مالیات و عوارض ارزش افزوده مهم است؟
8. آیا موضوع به قانون یا مقررات جاری وابسته است؟
9. آیا اطلاعات موردنظر ممکن است اخیراً تغییر کرده باشد؟

اگر ابهام اساسی وجود دارد و بدون رفع آن چند پاسخ متفاوت ممکن است،
یک سؤال روشن‌کننده کوتاه بپرس.

اگر سؤال به اندازه کافی مشخص است، سؤال اضافی نپرس.


========================
ثبت‌های حسابداری
========================

در ثبت‌های حسابداری:

• از بدهکار و بستانکار استفاده کن.
• مفروضات مؤثر را مشخص کن.
• سیستم دائمی و ادواری را با هم اشتباه نکن.
• در صورت وابستگی ثبت به شرایط مختلف، شرایط را صریح بیان کن.
• مالیات و عوارض ارزش افزوده را در صورت ارتباط بررسی کن.
• اگر مبلغ یا اطلاعات معامله مشخص نیست، عدد را حدس نزن.
• در مثال آموزشی، فرضیات را واضح اعلام کن.


========================
قوانین و مقررات ایران
========================

هرگاه سؤال درباره موارد زیر باشد، Web Search الزامی است:

• قانون
• ماده
• تبصره
• بند
• بخشنامه
• دستورالعمل
• آیین‌نامه
• رأی
• مصوبه
• سامانه مودیان
• صورت‌حساب الکترونیکی
• مالیات
• مالیات بر ارزش افزوده
• مالیات حقوق
• معافیت مالیاتی
• نرخ مالیاتی
• حق بیمه
• تامین اجتماعی
• حقوق و دستمزد
• حداقل حقوق
• حداقل مزد
• حق مسکن
• بن کارگری
• حق تاهل
• حق اولاد
• پایه سنوات
• عیدی
• سنوات
• مزایای بازنشستگی
• قانون بودجه
• شورای عالی کار
• مقررات جاری


========================
صحت‌سنجی چندمنبعی
========================

در موضوعات قانونی، مالیاتی، بیمه‌ای، حقوق و دستمزد و موضوعاتی که
شامل عدد یا حکم جاری قانونی هستند، فقط به یک سایت اعتماد نکن.

پس از فعال شدن Web Search:

1. ابتدا منابع رسمی و اولیه را بررسی کن.
2. سپس حداقل دو منبع مستقل دیگر را بررسی کن.
3. در صورت امکان، حداقل سه منبع مستقل را با یکدیگر مقایسه کن.
4. ارقام و احکام متناقض را شناسایی کن.
5. آخرین مقرره معتبر و لازم‌الاجرا را مبنا قرار بده.
6. مقررات اصلاح‌شده، منسوخ یا ابطال‌شده را مبنای پاسخ قرار نده.
7. اگر چند منبع معتبر یک رقم را تایید کردند، می‌توان آن رقم را با
   اطمینان بیشتری اعلام کرد.
8. اگر منابع معتبر اختلاف دارند، اختلاف را صریحاً اعلام کن.
9. یک سایت تخصصی به تنهایی برای قطعی اعلام کردن یک رقم قانونی کافی نیست.
10. اگر منبع رسمی پیدا نشد، این موضوع را صریحاً در پاسخ اعلام کن.


========================
اولویت منابع
========================

در پژوهش قانونی اولویت با منابع زیر است:

اول:
• منابع رسمی دولت
• مجلس
• وزارت امور اقتصادی و دارایی
• سازمان امور مالیاتی
• سازمان تامین اجتماعی
• وزارت تعاون، کار و رفاه اجتماعی
• شورای عالی کار
• مرجع رسمی صادرکننده مقرره

دوم:
• منابع معتبر تخصصی حسابداری
• منابع معتبر مالیاتی
• منابع معتبر حقوق کار
• منابع معتبر تامین اجتماعی

سوم:
• سایر منابع وب برای تکمیل و مقایسه


========================
موضوعات همیشه نیازمند جست‌وجوی وب
========================

برای این موارد بدون Web Search پاسخ نده:

• حق تاهل
• حق اولاد
• کمک هزینه عائله‌مندی
• حداقل دستمزد
• حداقل حقوق
• حق مسکن
• بن کارگری
• پایه سنوات
• عیدی
• سنوات
• نرخ حق بیمه
• مزایای بازنشستگی
• معافیت حقوق
• نرخ مالیات
• سقف معافیت
• سقف مشمولیت
• بخشنامه‌های سازمان امور مالیاتی
• سامانه مودیان
• صورت‌حساب الکترونیکی
• قانون بودجه
• مصوبات شورای عالی کار
• بخشنامه‌های سازمان تامین اجتماعی

اگر سؤال شامل سال شمسی مانند ۱۴۰۳، ۱۴۰۴، ۱۴۰۵ یا سال‌های بعد باشد،
Web Search انجام بده.


========================
ارقام قانونی
========================

هرگز این موارد را از حافظه یا حدس اعلام نکن:

• مبلغ
• نرخ
• درصد
• سقف
• حداقل
• حداکثر
• مهلت
• جریمه
• حق بیمه
• حقوق
• دستمزد
• مزایا
• معافیت

اگر نتیجه جست‌وجو قطعی نیست، صریحاً بگو که رقم قطعی قابل تایید نیست.

اگر منابع اختلاف دارند:

• اختلاف را بیان کن.
• منابع معتبرتر را در نظر بگیر.
• از ادعای قطعیت بدون پشتوانه خودداری کن.


========================
حقوق و دستمزد
========================

اگر کاربر درباره حقوق یک سال مشخص سؤال کرد، اقلام را جداگانه بررسی کن.

مثلاً برای سال ۱۴۰۵:

• حداقل مزد روزانه
• حداقل مزد ماهانه
• حق مسکن
• بن کارگری
• حق تاهل
• حق اولاد
• پایه سنوات
• مزایای رفاهی
• حداقل دریافتی
• بیمه
• مالیات حقوق

هر عدد باید تا حد امکان با منابع مستقل تطبیق داده شود.

اگر یک سایت عددی را اعلام کرده ولی منابع رسمی یا معتبر دیگر آن را
تایید نمی‌کنند، آن عدد را قطعی اعلام نکن.


========================
سال و تاریخ
========================

سال مورد سؤال را دقیق رعایت کن.

برای مثال اگر کاربر درباره ۱۴۰۵ سؤال کرده است، اطلاعات سال ۱۴۰۴ را
به عنوان اطلاعات قطعی سال ۱۴۰۵ ارائه نکن.

اگر اطلاعات سال جدید هنوز به صورت رسمی ابلاغ نشده است، این موضوع را
واضح اعلام کن.


========================
ایموجی
========================

محدودیت عددی ثابت برای ایموجی وجود ندارد.

از ایموجی مرتبط، طبیعی و حرفه‌ای استفاده کن.

نه بیش از حد و نه کمتر از حد لازم.


========================
فرمت تلگرام
========================

پاسخ مناسب تلگرام باشد.

از Markdown استفاده نکن.

از ستاره‌های * و ** استفاده نکن.

از URL خام استفاده نکن.

از لینک Markdown استفاده نکن.

برای بولت‌ها از علامت «•» استفاده کن.

تیترها را ساده و خوانا بنویس.


========================
قانون بسیار مهم درباره منابع
========================

اگر از Web Search استفاده کردی، هرگز URL یا لینک سایت را در پاسخ
نمایش نده.

این موارد را هرگز در پاسخ نهایی ننویس:

URL
آدرس سایت
دامنه سایت
لینک قابل کلیک
Markdown Link
[🔗]
(pishdadacc.com)
(website.com)

به جای آن فقط یک خط توصیفی کوتاه در پایان پاسخ قرار بده.

نمونه:

📚 منبع: مصوبات و ابلاغیه‌های رسمی شورای عالی کار و منابع تخصصی حقوق و دستمزد

یا:

📚 منبع: مقررات رسمی سازمان امور مالیاتی و منابع تخصصی مالیاتی

یا:

📚 منبع: منابع رسمی تامین اجتماعی و منابع تخصصی بیمه

منبع باید توصیفی باشد و لینک نداشته باشد.


========================
تصاویر
========================

اگر تصویر سند، فاکتور، رسید یا مدرک حسابداری دریافت کردی:

1. تصویر را دقیق بررسی کن.
2. اعداد را فقط در صورت خوانا بودن نقل کن.
3. تاریخ‌ها را بررسی کن.
4. نام‌ها و مبالغ را حدس نزن.
5. بخش ناخوانا را صریحاً اعلام کن.
6. نوع سند را تشخیص بده.
7. اطلاعات مؤثر برای ثبت را استخراج کن.
8. اگر اطلاعات برای پاسخ قطعی کافی نیست، سؤال روشن‌کننده بپرس.
9. اگر موضوع تصویر مربوط به قانون یا مقررات جاری است، Web Search انجام بده.
10. اطلاعات قانونی را در صورت امکان با چند منبع تطبیق بده.


========================
سبک پاسخ
========================

سؤال ساده:
کوتاه پاسخ بده.

سؤال تخصصی:
کامل و منظم پاسخ بده.

سؤال آموزشی:
مرحله‌به‌مرحله توضیح بده.

از اطلاعات غیرمرتبط خودداری کن.

در پایان پاسخ پیشنهاد ادامه گفتگو نده.

دقت اطلاعات مهم‌تر از سرعت پاسخ است.
"""


# =========================================================
# ساخت کیبورد
# =========================================================

def create_keyboard(buttons):
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
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
        ["📱 ارتباط با ما"],
    ]

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات ما خوش آمدید 🌱\n\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard),
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
        "• 🏛 تامین اجتماعی\n"
        "• 📊 اکسل و Power Query در حسابداری\n"
        "• 💼 سایر موضوعات مرتبط با حسابداری\n\n"
        "🖼️ امکان ارسال عکس سند، فاکتور یا مدرک حسابداری نیز فعال است.\n\n"
        "🔙 برای خروج از این بخش، گزینه «بازگشت» را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard),
    )


# =========================================================
# نرمال‌سازی فارسی
# =========================================================

def _normalize_persian(text):
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ی",
        "ۀ": "ه",
        "\u0649": "ی",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def _normalize_for_match(text):
    text = _normalize_persian(text)
    text = text.replace("\u200c", "")
    text = text.replace(" ", "")
    return text


# =========================================================
# تشخیص سؤال قانونی
# =========================================================

def _is_legal_question(text):
    normalized = _normalize_for_match(text)

    keywords = [
        "قانون",
        "ماده",
        "تبصره",
        "بند",
        "بخشنامه",
        "دستورالعمل",
        "آیین نامه",
        "آیین‌نامه",
        "رای",
        "رأی",
        "ابطال",
        "اصلاحیه",
        "اصلاح",
        "مقررات",
        "مقرره",

        "سامانه مودیان",
        "سامانه مؤدیان",
        "صورتحساب الکترونیکی",
        "صورت‌حساب الکترونیکی",

        "مالیات",
        "ارزش افزوده",
        "معافیت",
        "جریمه",
        "جرائم",

        "نرخ مالیات",
        "مالیات بر درآمد",
        "مالیات بر ارزش",

        "تامین اجتماعی",
        "تأمین اجتماعی",
        "بیمه",
        "حق بیمه",
        "بیمه بیکاری",
        "بیمه درمان",
        "بیمه حوادث",

        "حداقل دستمزد",
        "حداقل حقوق",
        "دستمزد",

        "تاهل",
        "تأهل",
        "حق تاهل",
        "حق تأهل",

        "اولاد",
        "حق اولاد",

        "عائله",
        "عائله مندی",
        "عائله‌مندی",

        "حق مسکن",
        "بن کارگری",
        "بن",
        "حق شغل",
        "مزایای رفاهی",
        "کمک هزینه",
        "کمک‌هزینه",

        "بازنشسته",
        "بازنشستگی",

        "عیدی",
        "سنوات",
        "پایه سنوات",

        "مرخصی",
        "استعلاجی",

        "بودجه",
        "لایحه بودجه",
        "مصوبه",
        "تصویب",
        "تصویب‌نامه",

        "سقف",
        "نصاب",
        "حد مجاز",

        "شورای عالی کار",

        "صادرات",
        "واردات",
        "گمرک",
        "ترانزیت",

        "قرارداد کار",
        "پیمان",

        "استهلاک",
        "سرمایه گذاری",
        "سرمایه‌گذاری",
    ]

    for keyword in keywords:
        if _normalize_for_match(keyword) in normalized:
            return True

    year_patterns = [
        r"۱۴۰[۱-۹]",
        r"۱۴۱[۰-۹]",
        r"140[1-9]",
        r"141[0-9]",
    ]

    for pattern in year_patterns:
        if re.search(pattern, text):
            return True

    return False


# =========================================================
# استخراج متن پاسخ
# =========================================================

def _extract_output_text(response):
    text = (
        getattr(
            response,
            "output_text",
            None
        )
        or ""
    ).strip()

    if text:
        return text

    collected = []

    try:
        for item in getattr(
            response,
            "output",
            []
        ) or []:

            if getattr(
                item,
                "type",
                None
            ) != "message":
                continue

            for content in getattr(
                item,
                "content",
                []
            ) or []:

                content_text = getattr(
                    content,
                    "text",
                    None
                )

                if content_text:
                    collected.append(
                        content_text
                    )

    except Exception as e:
        print(
            f"OUTPUT TEXT EXTRACTION WARNING: {e}"
        )

    return "".join(
        collected
    ).strip()


# =========================================================
# حذف URL و منابع لینک‌دار
# =========================================================

def _remove_links_and_domains(text):

    # Markdown links
    text = re.sub(
        r"\[[^\]]*\]\(\s*https?://[^)]+\)",
        "",
        text,
        flags=re.I,
    )

    # URL
    text = re.sub(
        r"https?://\S+",
        "",
        text,
        flags=re.I,
    )

    # www
    text = re.sub(
        r"\bwww\.[^\s<>()]+",
        "",
        text,
        flags=re.I,
    )

    # دامنه داخل پرانتز
    text = re.sub(
        r"\(\s*(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\)]*)?\s*\)",
        "",
        text,
    )

    # دامنه بدون پرانتز
    text = re.sub(
        r"\b[a-zA-Z0-9-]+\.(?:com|ir|org|net|gov|edu)(?:/[^\s]*)?",
        "",
        text,
        flags=re.I,
    )

    # لینک‌های HTML
    text = re.sub(
        r"<a\b[^>]*>.*?</a>",
        "",
        text,
        flags=re.I | re.S,
    )

    # خطوط مربوط به منابع لینک‌دار
    lines = text.splitlines()
    result = []

    for line in lines:

        stripped = line.strip()

        if (
            stripped.startswith("📚 منابع:")
            or stripped.startswith("📚 منابع :")
        ):
            continue

        if (
            stripped.startswith("منابع:")
            or stripped.startswith("منابع :")
        ):
            if re.search(
                r"https?://|www\.|\.com|\.ir|\.org|\.gov",
                stripped,
                flags=re.I,
            ):
                continue

        result.append(line)

    text = "\n".join(result)

    # فاصله‌های اضافی
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# =========================================================
# پاک‌سازی متن AI
# =========================================================

def _clean_ai_text(text):

    text = text.replace(
        "```python",
        ""
    )

    text = text.replace(
        "```",
        ""
    )

    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        text,
        flags=re.S,
    )

    text = re.sub(
        r"\*(.*?)\*",
        r"\1",
        text,
        flags=re.S,
    )

    text = re.sub(
        r"(?m)^\s*#{1,6}\s*",
        "",
        text,
    )

    text = re.sub(
        r"(?m)^\s*[-*]\s+",
        "• ",
        text,
    )

    text = _remove_links_and_domains(
        text
    )

    return text.strip()


# =========================================================
# ارسال پاسخ
# =========================================================

async def _send_ai_answer(
    message,
    answer,
    source_citations=None,
    edit_message=None,
):

    answer = _clean_ai_text(
        answer
    )

    max_text_length = 3500

    chunks = [
        answer[i:i + max_text_length]
        for i in range(
            0,
            len(answer),
            max_text_length
        )
    ] or [""]

    if len(chunks) == 1:

        rendered = html.escape(
            answer,
            quote=False
        )

        if edit_message is not None:

            await edit_message.edit_text(
                rendered,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

        else:

            await message.reply_text(
                rendered,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

        return

    if edit_message is not None:

        await edit_message.edit_text(
            html.escape(
                chunks[0],
                quote=False
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        for chunk in chunks[1:]:

            await message.reply_text(
                html.escape(
                    chunk,
                    quote=False
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

    else:

        for chunk in chunks:

            await message.reply_text(
                html.escape(
                    chunk,
                    quote=False
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )


# =========================================================
# درخواست AI
# =========================================================

async def _request_ai(
    input_parts,
    question_for_history,
    context,
    image_mode=False,
):

    history = context.user_data.setdefault(
        "ai_history",
        []
    )

    recent_history = history[
        -AI_HISTORY_MESSAGES:
    ]

    combined_input = []

    for item in recent_history:

        combined_input.append(
            {
                "role": item["role"],
                "content": item["content"],
            }
        )

    combined_input.append(
        {
            "role": "user",
            "content": input_parts,
        }
    )

    history_text = " ".join(
        item.get("content", "")
        for item in recent_history
        if isinstance(
            item.get("content"),
            str
        )
    )

    legal_from_question = _is_legal_question(
        question_for_history
    )

    legal_from_history = _is_legal_question(
        history_text
    )

    legal = (
        legal_from_question
        or legal_from_history
    )

    force_search = legal

    base_tokens = (
        AI_MAX_OUTPUT_TOKENS_LEGAL
        if legal
        else AI_MAX_OUTPUT_TOKENS
    )

    # -----------------------------------------------------
    # ساخت درخواست
    # -----------------------------------------------------

    def build_request(
        max_tokens,
        with_tools,
        force_tool=False,
    ):

        args = {
            "model": AI_MODEL,
            "instructions": AI_SYSTEM_PROMPT,
            "input": combined_input,
            "max_output_tokens": max_tokens,
        }

        if with_tools:

            args["tools"] = [
                {
                    "type": "web_search",
                    "search_context_size":
                        AI_WEB_SEARCH_CONTEXT,
                }
            ]

        if force_tool:

            args["tool_choice"] = "required"

        return args

    # -----------------------------------------------------
    # تلاش‌ها
    # -----------------------------------------------------

    attempts = [
        {
            "tokens": base_tokens,
            "with_tools": True,
            "force_tool": force_search,
        },
        {
            "tokens": min(
                AI_MAX_OUTPUT_TOKENS_HARD_CAP,
                base_tokens * 2,
            ),
            "with_tools": True,
            "force_tool": force_search,
        },
        {
            "tokens": min(
                AI_MAX_OUTPUT_TOKENS_HARD_CAP,
                base_tokens * 2,
            ),
            "with_tools": False,
            "force_tool": False,
        },
    ]

    response = None
    answer = ""

    used_fallback_without_search = False

    for index, attempt in enumerate(
        attempts
    ):

        try:

            attempt_response = (
                client.responses.create(
                    **build_request(
                        attempt["tokens"],
                        attempt["with_tools"],
                        attempt["force_tool"],
                    )
                )
            )

        except Exception as call_error:

            print(
                f"OPENAI CALL ERROR "
                f"(attempt {index + 1}) "
                f"[{type(call_error).__name__}]: "
                f"{call_error}"
            )

            continue

        attempt_answer = (
            _extract_output_text(
                attempt_response
            )
        )

        status = getattr(
            attempt_response,
            "status",
            None
        )

        incomplete_details = getattr(
            attempt_response,
            "incomplete_details",
            None
        )

        incomplete_reason = (
            getattr(
                incomplete_details,
                "reason",
                None
            )
            if incomplete_details
            else None
        )

        cut_off = (
            status == "incomplete"
            and incomplete_reason
            == "max_output_tokens"
        )

        if attempt_answer and not answer:

            response = attempt_response
            answer = attempt_answer

            used_fallback_without_search = (
                not attempt["with_tools"]
            )

        if attempt_answer and not cut_off:
            break

        print(
            f"AI ATTEMPT {index + 1} "
            f"INSUFFICIENT: "
            f"status={status}, "
            f"incomplete_reason="
            f"{incomplete_reason}, "
            f"empty={not attempt_answer}"
        )

    if not answer:

        return (
            "⚠️ پاسخی از سرویس هوش مصنوعی دریافت نشد.\n\n"
            "لطفاً سؤال را کمی کوتاه‌تر و ساده‌تر مطرح کنید "
            "یا دوباره تلاش کنید.",
            [],
        )

    # -----------------------------------------------------
    # هشدار در صورت شکست Web Search
    # -----------------------------------------------------

    if (
        used_fallback_without_search
        and legal
    ):

        answer = (
            "⚠️ این پاسخ بدون تأیید کامل از جست‌وجوی وب ارائه شده "
            "و ممکن است برای مقررات جاری دقیق نباشد.\n\n"
            + answer
        )

    # -----------------------------------------------------
    # ذخیره تاریخچه
    # -----------------------------------------------------

    clean_answer = _clean_ai_text(
        answer
    )

    history.append(
        {
            "role": "user",
            "content": question_for_history[
                :AI_HISTORY_CHAR_LIMIT
            ],
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": clean_answer[
                :AI_HISTORY_CHAR_LIMIT
            ],
        }
    )

    del history[
        :-AI_HISTORY_MESSAGES
    ]

    # منابع عمداً به کاربر ارسال نمی‌شوند.
    return (
        answer,
        [],
    )


# =========================================================
# سؤال متنی
# =========================================================

async def ask_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "ai_mode",
        False
    ):
        return

    user_question = (
        update.message.text or ""
    ).strip()[:3000]

    if not user_question:
        return

    if (
        not OPENAI_API_KEY
        or client is None
    ):

        await update.message.reply_text(
            "⚠️ اتصال دستیار هوشمند تنظیم نشده است.\n"
            "OPENAI_API_KEY را در Environment Variables بررسی کنید."
        )

        return

    thinking_message = (
        await update.message.reply_text(
            "🤖 در حال بررسی سؤال شما..."
        )
    )

    try:

        input_parts = [
            {
                "type": "input_text",
                "text": user_question,
            }
        ]

        answer, source_urls = await _request_ai(
            input_parts,
            user_question,
            context,
            image_mode=False,
        )

        await _send_ai_answer(
            update.message,
            answer,
            source_urls,
            edit_message=thinking_message,
        )

    except Exception as e:

        print(
            f"OPENAI TEXT ERROR "
            f"[{type(e).__name__}]: {e}"
        )

        try:

            await thinking_message.edit_text(
                "⚠️ در پردازش سؤال مشکلی ایجاد شد.\n"
                "لطفاً چند لحظه بعد دوباره تلاش کنید."
            )

        except Exception:
            pass


# =========================================================
# سؤال تصویری
# =========================================================

async def ask_ai_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "ai_mode",
        False
    ):
        return

    if (
        not OPENAI_API_KEY
        or client is None
    ):

        await update.message.reply_text(
            "⚠️ اتصال دستیار هوشمند تنظیم نشده است.\n"
            "OPENAI_API_KEY را در Environment Variables بررسی کنید."
        )

        return

    photo = update.message.photo

    if not photo:
        return

    try:

        largest_photo = photo[-1]

        telegram_file = (
            await context.bot.get_file(
                largest_photo.file_id
            )
        )

        image_bytes = (
            await telegram_file.download_as_bytearray()
        )

        if (
            len(image_bytes)
            > AI_IMAGE_MAX_BYTES
        ):

            await update.message.reply_text(
                "⚠️ حجم تصویر برای پردازش زیاد است. "
                "لطفاً تصویر را با حجم کمتر ارسال کنید."
            )

            return

        image_b64 = base64.b64encode(
            bytes(image_bytes)
        ).decode("ascii")

        image_data_url = (
            "data:image/jpeg;base64,"
            + image_b64
        )

        caption = (
            update.message.caption or ""
        ).strip()[:2000]

        if not caption:

            caption = (
                "این تصویر را با دقت بررسی کن. "
                "اگر سند، فاکتور، رسید یا مدرک حسابداری است، "
                "اطلاعات قابل خواندن را استخراج کن. "
                "قبل از ارائه ثبت حسابداری، مفروضات مؤثر "
                "مانند دائمی یا ادواری و نقدی یا نسیه بودن را "
                "بررسی کن. اگر اطلاعات کافی نیست، سؤال "
                "روشن‌کننده بپرس."
            )

        thinking_message = (
            await update.message.reply_text(
                "🖼️ در حال بررسی تصویر شما..."
            )
        )

        input_parts = [
            {
                "type": "input_text",
                "text": caption,
            },
            {
                "type": "input_image",
                "image_url": image_data_url,
                "detail": "auto",
            },
        ]

        answer, source_urls = await _request_ai(
            input_parts,
            caption,
            context,
            image_mode=True,
        )

        await _send_ai_answer(
            update.message,
            answer,
            source_urls,
            edit_message=thinking_message,
        )

    except Exception as e:

        print(
            f"OPENAI IMAGE ERROR "
            f"[{type(e).__name__}]: {e}"
        )

        try:

            await update.message.reply_text(
                "⚠️ در پردازش تصویر مشکلی ایجاد شد.\n"
                "لطفاً تصویر واضح‌تری ارسال کنید یا "
                "چند لحظه بعد دوباره تلاش کنید."
            )

        except Exception:
            pass


# =========================================================
# دوره‌های آموزشی
# =========================================================

async def courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "courses"

    keyboard = [
        ["🏫 دوره‌های آموزشی حضوری"],
        ["💻 دوره‌های آموزشی آنلاین"],
        ["🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🎓 دوره‌های آموزشی\n\n"
        "نوع دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def in_person_courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "in_person_courses"

    keyboard = [
        ["📊 دوره آموزش پاور کوئری"],
        ["📑 دوره سامانه مودیان"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🏫 دوره‌های آموزشی حضوری\n\n"
        "دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def online_courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "online_courses"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "💻 دوره‌های آموزشی آنلاین\n\n"
        "در حال حاضر دوره‌ای در این بخش قرار نگرفته است.",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def tax_system(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "tax_system"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📑 دوره آموزش سامانه مودیان\n\n"
        "اطلاعات این دوره به‌زودی در ربات قرار خواهد گرفت.",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def power_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "power_query"

    keyboard = [
        ["📊 مشاهده و ثبت‌نام دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات دوره و ثبت‌نام، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def power_query_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "power_query_link"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات و ثبت‌نام دوره، "
        "روی لینک زیر کلیک کنید:\n\n"
        "https://maliplusco.ir/product/%d9%85%d9%88%d8%b1%d8%b3%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


# =========================================================
# ارتباط با ما
# =========================================================

async def contact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "contact"

    keyboard = [
        ["📸 اینستاگرام"],
        ["📢 کانال تلگرام"],
        ["🟠 کانال روبیکا"],
        ["🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def instagram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "instagram"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📸 اینستاگرام:\n\n"
        "https://instagram.com/ali_chavoshi.official",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def telegram_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "telegram"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📢 کانال تلگرام:\n\n"
        "https://t.me/Alichavoshiaccounting",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def rubika(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "rubika"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🟠 کانال روبیکا:\n\n"
        "https://rubika.ir/Alichavoshiaccounting",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


# =========================================================
# ویدئوهای آموزشی
# =========================================================

async def educational_videos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "educational_videos"

    keyboard = [
        ["📗 ویدئوهای آموزشی مقدماتی اکسل"],
        ["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"],
        ["🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🎬 ویدئوهای آموزشی\n\n"
        "سطح آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def excel_beginner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "excel_beginner"

    keyboard = [
        ["📥 لینک‌های دانلود دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📗 ویدئوهای آموزشی مقدماتی اکسل\n\n"
        "برای دریافت لینک دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def excel_beginner_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "excel_beginner_download"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی مقدماتی اکسل:\n\n"
        "https://my.uupload.ir/d/pVZXk",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def excel_intermediate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "excel_intermediate"

    keyboard = [
        ["📥 لینک‌های دانلود دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\n"
        "برای دریافت لینک دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


async def excel_intermediate_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "menu_level"
    ] = "excel_intermediate_download"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی سطح نیمه پیشرفته:\n\n"
        "https://my.uupload.ir/d/YL2XN",
        reply_markup=create_keyboard(
            keyboard
        ),
    )


# =========================================================
# بازگشت
# =========================================================

async def back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    level = context.user_data.get(
        "menu_level"
    )

    if level == "ai":

        context.user_data[
            "ai_mode"
        ] = False

        await start(
            update,
            context
        )

    elif level in [
        "in_person_courses",
        "online_courses",
    ]:

        await courses(
            update,
            context
        )

    elif level in [
        "tax_system",
        "power_query",
    ]:

        await in_person_courses(
            update,
            context
        )

    elif level == "power_query_link":

        await power_query(
            update,
            context
        )

    elif level in [
        "instagram",
        "telegram",
        "rubika",
    ]:

        await contact(
            update,
            context
        )

    elif level == "excel_beginner":

        await educational_videos(
            update,
            context
        )

    elif level == "excel_beginner_download":

        await excel_beginner(
            update,
            context
        )

    elif level == "excel_intermediate":

        await educational_videos(
            update,
            context
        )

    elif level == "excel_intermediate_download":

        await excel_intermediate(
            update,
            context
        )

    else:

        await start(
            update,
            context
        )


# =========================================================
# لینک دانلود
# =========================================================

async def download_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    level = context.user_data.get(
        "menu_level"
    )

    if level == "excel_beginner":

        await excel_beginner_download(
            update,
            context
        )

    elif level == "excel_intermediate":

        await excel_intermediate_download(
            update,
            context
        )


# =========================================================
# ساخت Application
# =========================================================

app = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)


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
# ورود به AI
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🤖 دستیار هوش مصنوعی"]
        ),
        ai_assistant
    )
)


# =========================================================
# منوی اصلی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🎓 دوره‌های آموزشی"]
        ),
        courses
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🎬 ویدئوهای آموزشی"]
        ),
        educational_videos
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📱 ارتباط با ما"]
        ),
        contact
    )
)


# =========================================================
# دوره‌ها
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🏫 دوره‌های آموزشی حضوری"]
        ),
        in_person_courses
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["💻 دوره‌های آموزشی آنلاین"]
        ),
        online_courses
    )
)


# =========================================================
# دوره‌های حضوری
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📊 دوره آموزش پاور کوئری"]
        ),
        power_query
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📑 دوره سامانه مودیان"]
        ),
        tax_system
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📊 مشاهده و ثبت‌نام دوره"]
        ),
        power_query_link
    )
)


# =========================================================
# ارتباط با ما
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📸 اینستاگرام"]
        ),
        instagram
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📢 کانال تلگرام"]
        ),
        telegram_channel
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🟠 کانال روبیکا"]
        ),
        rubika
    )
)


# =========================================================
# ویدئوها
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📗 ویدئوهای آموزشی مقدماتی اکسل"]
        ),
        excel_beginner
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"]
        ),
        excel_intermediate
    )
)


# =========================================================
# دانلود
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["📥 لینک‌های دانلود دوره"]
        ),
        download_links
    )
)


# =========================================================
# بازگشت
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🔙 بازگشت"]
        ),
        back
    )
)


# =========================================================
# منوی اصلی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(
            ["🏠 منوی اصلی"]
        ),
        start
    )
)


# =========================================================
# دکمه‌های منو
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
    "🏠 منوی اصلی",
]


# =========================================================
# تصاویر
# =========================================================

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        ask_ai_image
    )
)


# =========================================================
# پیام‌های متنی AI
# =========================================================

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

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram"
)
