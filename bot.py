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

AI_MODEL = os.getenv("AI_MODEL", "gpt-5.6-luna")

AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "2200"))
AI_MAX_OUTPUT_TOKENS_LEGAL = int(
    os.getenv("AI_MAX_OUTPUT_TOKENS_LEGAL", "3600")
)
AI_MAX_OUTPUT_TOKENS_HARD_CAP = int(
    os.getenv("AI_MAX_OUTPUT_TOKENS_HARD_CAP", "5200")
)

AI_HISTORY_MESSAGES = int(os.getenv("AI_HISTORY_MESSAGES", "4"))
AI_HISTORY_CHAR_LIMIT = int(os.getenv("AI_HISTORY_CHAR_LIMIT", "1200"))
AI_IMAGE_MAX_BYTES = int(os.getenv("AI_IMAGE_MAX_BYTES", "10000000"))
AI_WEB_SEARCH_CONTEXT = os.getenv("AI_WEB_SEARCH_CONTEXT", "high")


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
    client = OpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# تنظیمات هوش مصنوعی
# =========================================================

AI_SYSTEM_PROMPT = """
نقش: دستیار هوشمند حسابداری ACN.

تو یک دستیار تخصصی برای حسابداری و مالی ایران هستی و باید قبل از پاسخ، سؤال را
از نظر موضوع، مفروضات، ابهام‌ها، روش حسابداری و به‌روز بودن اطلاعات تحلیل کنی.

=========================================================
حوزه‌های مجاز
=========================================================
به پرسش‌های مرتبط با موارد زیر پاسخ بده:
• 🧾 حسابداری و مالی
• 🔍 حسابرسی
• 💰 مالیات
• 🏛 تأمین اجتماعی
• 📊 اکسل و Power Query در حسابداری
• 💼 سایر موضوعات مرتبط با حسابداری

اگر سؤال کاملاً خارج از این حوزه‌ها بود، فقط بگو:
«این دستیار برای پاسخ‌گویی به پرسش‌های حسابداری، مالی، حسابرسی، مالیات، تأمین اجتماعی و اکسل/Power Query مرتبط با حسابداری طراحی شده است.»

=========================================================
تحلیل قبل از پاسخ
=========================================================
قبل از تولید پاسخ، این موارد را بررسی کن:
1) منظور دقیق کاربر چیست؟
2) آیا سؤال یک یا چند فرض مؤثر و نامشخص دارد؟
3) آیا نوع معامله، روش حسابداری، نقدی/نسیه، دائمی/ادواری، مالیات و عوارض، دوره یا
   وضعیت قانونی روی جواب اثر دارد؟
4) آیا موضوع به قانون یا اطلاعات روز وابسته است و باید وب جست‌وجو شود؟

اگر یک ابهام اساسی باعث می‌شود چند پاسخ متفاوت ممکن باشد، خودسرانه فرض نساز؛
یک سؤال روشن‌کننده کوتاه بپرس.

مثال: «ثبت حسابداری خرید کالا چیست؟»
اگر دائمی یا ادواری مشخص نشده، ابتدا بپرس:
«منظورتان سیستم موجودی دائمی است یا ادواری؟»
سپس بعد از مشخص شدن روش، ثبت دقیق همان روش را ارائه کن.

در سؤال‌های مشخص، سؤال اضافه نپرس.

=========================================================
ثبت‌های حسابداری
=========================================================
در ثبت‌ها از «بدهکار» و «بستانکار» استفاده کن و همه مفروضات مؤثر را بررسی کن.
در خرید و فروش کالا، دائمی و ادواری را با هم اشتباه نکن.
اگر ثبت به شرایط مختلف وابسته است، همان شرایط را صریح و کوتاه بیان کن.
در صورت وجود مالیات و عوارض ارزش افزوده، وضعیت آن را با مقررات جاری تطبیق بده.

=========================================================
قوانین، بخشنامه‌ها و مقررات ایران
=========================================================
هرگاه سؤال درباره قانون، ماده، تبصره، بند، بخشنامه، دستورالعمل، آیین‌نامه، رأی،
سامانه مؤدیان، مالیات، ارزش افزوده، تأمین اجتماعی، بودجه سالانه، حق تأهل،
حق اولاد، حداقل دستمزد، حق مسکن، بن کارگری، حق بیمه، معافیت، نرخ مالیات،
یا هر مقرره جاری باشد، باید Web Search را استفاده کنی و پاسخ را صرفاً بر
اساس حافظه مدل ارائه ندهی. این موضوع شامل سؤالات ادامه‌دار در همان مکالمه
هم می‌شود.

برای پژوهش قانونی، منابع رسمی ایران را در اولویت قرار بده؛ از جمله:
• regulation.tax.gov.ir
• qavanin.ir
• dotic.ir
• rrk.ir
• adliran.ir
• tamin.ir
• tax.gov.ir
• intamedia.ir
• mefa.ir
• مجلس و سامانه‌های رسمی دولت و دستگاه صادرکننده مقرره
• acco.ir برای استانداردها و اسناد سازمان حسابرسی در صورت ارتباط

اگر رقم یا حکم موردنیاز مستقیماً در منابع رسمی پیدا نشد، جست‌وجو را به منابع
تخصصی معتبر حسابداری و مالیاتی ایران گسترش بده.

برای هر مقرره مهم، تا حد امکان نسخه جاری را با اصلاحات بعدی، الحاقیه‌ها،
ابطال‌ها و مقررات جایگزین بررسی کن.
اگر مقرره‌ای منسوخ، ابطال، اصلاح یا جایگزین شده است، آن را مبنای پاسخ نهایی قرار نده.
اگر بین منابع تعارض وجود داشت، آخرین و معتبرترین متن رسمی را مبنا قرار بده.

هرگز URL، نام دامنه یا آدرس سایت را داخل متن پاسخ ننویس.
اگر منبع وب استفاده شده، منبع را فقط به شکل توصیفی در انتهای پاسخ ذکر کن.

=========================================================
موضوعاتی که همیشه نیاز به Web Search دارند
=========================================================
برای پاسخ به پرسش درباره موارد زیر بدون جست‌وجوی وب پاسخ نده:

• حق تأهل، حق اولاد و کمک‌هزینه عائله‌مندی
• حداقل دستمزد و حداقل حقوق
• حق مسکن، بن کارگری و حق شغل
• نرخ‌های حق بیمه
• مزایای بازنشستگی
• معافیت حقوق
• نرخ‌های مالیاتی
• سقف معافیت‌ها و سقف مشمولیت
• بخشنامه‌های جاری سازمان امور مالیاتی
• مقررات سامانه مؤدیان و صورت‌حساب الکترونیکی
• قانون بودجه سالانه
• مصوبات شورای عالی کار
• بخشنامه‌های سازمان تأمین اجتماعی

اگر کاربر از «مبلغ»، «چقدر»، «نرخ»، «درصد»، «رقم»، «سقف» یا «ماهانه» درباره
موضوعات بالا پرسید، حتماً Web Search انجام شود.

اگر در سؤال به سال شمسی مانند ۱۴۰۳، ۱۴۰۴ یا ۱۴۰۵ اشاره شد، جست‌وجوی وب انجام شود.

=========================================================
دقت در ارقام قانونی
=========================================================
هرگز رقم، درصد، سقف معافیت، مبلغ، مهلت یا هر عدد قانونی/مالیاتی را از حافظه یا
حدس نگو.

اگر جست‌وجو نتیجه قطعی و به‌روز نداد، صریحاً بگو که رقم دقیق و قطعی از منبع رسمی
به‌دست نیامده یا هنوز ابلاغ نشده است.

=========================================================
ایموجی
=========================================================
محدودیت عددی ثابت برای ایموجی وجود ندارد.
از ایموجی‌های مرتبط، طبیعی و حرفه‌ای در نقاط مناسب استفاده کن؛ نه افراطی و نه کم.

=========================================================
فرمت خروجی تلگرام
=========================================================
پاسخ را برای تلگرام مناسب بنویس.
از Markdown پررنگ/کج و ستاره‌های * و ** استفاده نکن.
از URL خام استفاده نکن.
برای تیترها از متن ساده و در صورت نیاز ایموجی استفاده کن.
بولت‌ها را با «•» شروع کن.
اگر ثبت حسابداری می‌دهی، خوانا و مرتب بنویس.

اگر منبع وب استفاده شده، فقط یک خط در انتهای پاسخ با این قالب بنویس:
«📚 منبع: <توصیف کوتاه و کلمه‌ای منبع>»

=========================================================
پاسخ‌های تصویری
=========================================================
اگر تصویر سند، فاکتور، جدول، رسید یا هر مدرک حسابداری دریافت کردی:
1) تصویر را دقیق بخوان.
2) اعداد، تاریخ‌ها، نام‌ها و مبالغ را فقط وقتی قطعی هستند نقل کن.
3) اگر بخشی ناخوانا است، حدس نزن.
4) نوع سند و اطلاعات مؤثر در ثبت را تشخیص بده.
5) اگر اطلاعات مؤثر برای ثبت مشخص نیست، سؤال روشن‌کننده بپرس.
6) اگر تصویر به قانون یا مقررات جاری مربوط است، Web Search را نیز انجام بده.

=========================================================
سبک پاسخ
=========================================================
فارسی، دقیق، حرفه‌ای، مستقیم و قابل فهم بنویس.
سؤال ساده → پاسخ کوتاه.
سؤال تخصصی → پاسخ کامل و منظم.
سؤال آموزشی → مرحله‌به‌مرحله در حد نیاز.
اطلاعات جانبی نامرتبط اضافه نکن.
در پایان پاسخ پیشنهاد ادامه گفتگو نده.
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "ai"
    context.user_data["ai_mode"] = True
    context.user_data["ai_history"] = []

    keyboard = [["🔙 بازگشت"]]

    await update.message.reply_text(
        "🤖✨ به دستیار هوشمند حسابداری ACN خوش آمدید\n\n"
        "📚 سؤال خود را درباره یکی از موضوعات زیر ارسال کنید:\n\n"
        "• 🧾 حسابداری و مالی\n"
        "• 🔍 حسابرسی\n"
        "• 💰 مالیات\n"
        "• 🏛 تأمین اجتماعی\n"
        "• 📊 اکسل و Power Query در حسابداری\n"
        "• 💼 سایر موضوعات مرتبط با حسابداری\n\n"
        "🖼️ امکان ارسال عکس سند، فاکتور یا مدرک حسابداری نیز فعال است.\n\n"
        "🔙 برای خروج از این بخش، گزینه «بازگشت» را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard),
    )


# =========================================================
# نرمال‌سازی متن فارسی
# =========================================================

def _normalize_persian(text: str) -> str:
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


def _normalize_for_match(text: str) -> str:
    text = _normalize_persian(text)
    text = text.replace("\u200c", "")
    text = text.replace(" ", "")
    return text


# =========================================================
# تشخیص سؤال قانونی
# =========================================================

def _is_legal_question(text: str) -> bool:
    normalized = _normalize_persian(text)
    normalized_compact = _normalize_for_match(text)

    keywords = [
        "قانون", "ماده", "تبصره", "بند", "بخشنامه", "دستورالعمل",
        "آیین نامه", "آیین‌نامه", "رأی", "رای", "ابطال",
        "اصلاحیه", "اصلاح", "مقررات", "مقرره",
        "سامانه مؤدیان", "سامانه مودیان", "صورتحساب الکترونیکی",
        "صورت‌حساب الکترونیکی",
        "مالیات", "ارزش افزوده", "معافیت", "جرائم", "جریمه",
        "نرخ مالیات", "مالیات بر درآمد", "مالیات بر ارزش",
        "مالیات علی الحساب", "مالیات علی‌الحساب",
        "تأمین اجتماعی", "تامین اجتماعی", "بیمه", "حق بیمه",
        "بیمه بیکاری", "بیمه حوادث", "بیمه درمان",
        "حداقل دستمزد", "حداقل حقوق", "دستمزد",
        "تاهل", "تأهل", "حق تاهل", "حق تأهل",
        "اولاد", "حق اولاد",
        "عائله", "عائله مندی", "عائله‌مندی",
        "حق مسکن", "مسکن",
        "بن کارگری", "بن",
        "حق شغل", "شغل",
        "مزایای رفاهی", "رفاهی",
        "کمک هزینه", "کمک‌هزینه",
        "ایثارگر", "جانباز", "رزمنده",
        "مأموریت", "ماموریت",
        "بازنشسته", "بازنشستگی", "بازنشست",
        "پایانه", "عیدی", "سنوات",
        "مرخصی", "استعلاجی",
        "بودجه", "لایحه بودجه", "لایحه",
        "مصوبه", "تصویب", "تصویب‌نامه", "تصویب نامه",
        "سقف", "نصاب", "حد مجاز",
        "شورای عالی کار", "شوراي عالي كار",
        "صادرات", "واردات", "گمرک", "ترانزیت",
        "قرارداد کار", "قرارداد پاره", "پیمان",
        "سهمیه", "بهره", "استهلاک",
        "سرمایه‌گذاری", "سرمایه گذاری",
    ]

    for kw in keywords:
        kw_norm = _normalize_for_match(kw)
        if kw_norm and kw_norm in normalized_compact:
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

    # جلوگیری از هشدار unused variable در صورت تغییرات بعدی
    _ = normalized
    return False


# =========================================================
# استخراج متن پاسخ
# =========================================================

def _extract_output_text(response) -> str:
    text = (getattr(response, "output_text", None) or "").strip()

    if text:
        return text

    collected = []

    try:
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "message":
                continue

            for content in getattr(item, "content", []) or []:
                content_text = getattr(content, "text", None)

                if content_text:
                    collected.append(content_text)

    except Exception as e:
        print(f"OUTPUT TEXT EXTRACTION WARNING: {e}")

    return "".join(collected).strip()


# =========================================================
# استخراج لینک منابع
# =========================================================

def _collect_source_urls(response):
    citations = []
    seen = set()

    try:
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                for ann in getattr(content, "annotations", []) or []:
                    url = getattr(ann, "url", None)

                    if not url or url in seen:
                        continue

                    seen.add(url)

                    citations.append(
                        {
                            "url": url,
                            "start": getattr(ann, "start_index", None),
                            "end": getattr(ann, "end_index", None),
                            "title": getattr(ann, "title", None),
                        }
                    )

    except Exception as e:
        print(f"SOURCE EXTRACTION WARNING: {e}")

    return citations[:6]


# =========================================================
# پاک‌سازی متن برای تلگرام
# =========================================================

def _clean_ai_text(text: str) -> str:
    text = text.replace("```", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.S)
    text = re.sub(r"\*(.*?)\*", r"\1", text, flags=re.S)
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "• ", text)
    text = re.sub(r"\[(.*?)\]\((https?://[^)]+)\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    return text.strip()


# =========================================================
# قالب‌بندی منابع برای تلگرام
# =========================================================

def _telegram_html_with_sources(text: str, citations):
    safe = html.escape(text, quote=False)

    if not citations:
        return safe

    links = []

    for citation in citations:
        url = citation.get("url")

        if url:
            links.append(
                f'<a href="{html.escape(url, quote=True)}">🔗</a>'
            )

    if links:
        safe += "\n\n📚 منابع: " + " ".join(links)

    return safe


# =========================================================
# ارسال پاسخ به تلگرام
# =========================================================

async def _send_ai_answer(
    message,
    answer,
    source_citations=None,
    edit_message=None,
):
    answer = _clean_ai_text(answer)
    source_citations = source_citations or []
    max_text_length = 3500

    chunks = [
        answer[i:i + max_text_length]
        for i in range(0, len(answer), max_text_length)
    ] or [""]

    if len(chunks) == 1:
        rendered = _telegram_html_with_sources(
            answer,
            source_citations,
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
            html.escape(chunks[0], quote=False),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        for chunk in chunks[1:-1]:
            await message.reply_text(
                html.escape(chunk, quote=False),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

        await message.reply_text(
            _telegram_html_with_sources(
                chunks[-1],
                source_citations,
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    else:
        for index, chunk in enumerate(chunks):
            rendered = (
                _telegram_html_with_sources(
                    chunk,
                    source_citations,
                )
                if index == len(chunks) - 1
                else html.escape(chunk, quote=False)
            )

            await message.reply_text(
                rendered,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )


# =========================================================
# درخواست از هوش مصنوعی
# =========================================================

async def _request_ai(
    input_parts,
    question_for_history,
    context,
    image_mode=False,
):
    history = context.user_data.setdefault("ai_history", [])
    recent_history = history[-AI_HISTORY_MESSAGES:]

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
        if isinstance(item.get("content"), str)
    )

    legal_from_question = _is_legal_question(question_for_history)
    legal_from_history = _is_legal_question(history_text)
    legal = legal_from_question or legal_from_history

    force_search = legal
    base_tokens = (
        AI_MAX_OUTPUT_TOKENS_LEGAL
        if legal
        else AI_MAX_OUTPUT_TOKENS
    )

    def build_request(max_tokens, with_tools, force_tool=False):
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
                    "search_context_size": AI_WEB_SEARCH_CONTEXT,
                }
            ]

        if force_tool:
            args["tool_choice"] = "required"

        return args

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

    for index, attempt in enumerate(attempts):
        try:
            attempt_response = client.responses.create(
                **build_request(
                    attempt["tokens"],
                    attempt["with_tools"],
                    attempt["force_tool"],
                )
            )

        except Exception as call_error:
            print(
                f"OPENAI CALL ERROR (attempt {index + 1}) "
                f"[{type(call_error).__name__}]: {call_error}"
            )
            continue

        attempt_answer = _extract_output_text(attempt_response)
        status = getattr(attempt_response, "status", None)

        incomplete_details = getattr(
            attempt_response,
            "incomplete_details",
            None,
        )

        incomplete_reason = (
            getattr(incomplete_details, "reason", None)
            if incomplete_details
            else None
        )

        cut_off = (
            status == "incomplete"
            and incomplete_reason == "max_output_tokens"
        )

        if attempt_answer and not answer:
            response = attempt_response
            answer = attempt_answer
            used_fallback_without_search = not attempt["with_tools"]

        if attempt_answer and not cut_off:
            break

        print(
            f"AI ATTEMPT {index + 1} INSUFFICIENT: "
            f"status={status}, "
            f"incomplete_reason={incomplete_reason}, "
            f"empty={not attempt_answer}"
        )

    if not answer:
        return (
            "⚠️ پاسخی از سرویس هوش مصنوعی دریافت نشد. "
            "لطفاً سؤال را کمی کوتاه‌تر/ساده‌تر مطرح کنید "
            "یا دوباره تلاش کنید.",
            [],
        )

    if used_fallback_without_search and legal:
        answer = (
            "⚠️ این پاسخ بدون تأیید مستقیم از جست‌وجوی وب ارائه شده "
            "و ممکن است دقیق نباشد؛ لطفاً رقم/حکم نهایی را از منبع "
            "رسمی مربوطه نیز بررسی کنید.\n\n"
            + answer
        )

    history.append(
        {
            "role": "user",
            "content": question_for_history[:AI_HISTORY_CHAR_LIMIT],
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": answer[:AI_HISTORY_CHAR_LIMIT],
        }
    )

    del history[:-AI_HISTORY_MESSAGES]

    return (
        answer,
        _collect_source_urls(response) if response is not None else [],
    )


# =========================================================
# پردازش سؤال متنی
# =========================================================

async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode", False):
        return

    user_question = (update.message.text or "").strip()[:3000]

    if not user_question:
        return

    if not OPENAI_API_KEY or client is None:
        await update.message.reply_text(
            "⚠️ اتصال دستیار هوشمند تنظیم نشده است.\n"
            "OPENAI_API_KEY را در Environment Variables بررسی کنید."
        )
        return

    thinking_message = await update.message.reply_text(
        "🤖 در حال بررسی سؤال شما..."
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
            f"OPENAI TEXT ERROR [{type(e).__name__}]: {e}"
        )

        await thinking_message.edit_text(
            "⚠️ در پردازش سؤال مشکلی ایجاد شد.\n"
            "لطفاً چند لحظه بعد دوباره تلاش کنید."
        )


# =========================================================
# پردازش تصویر
# =========================================================

async def ask_ai_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode", False):
        return

    if not OPENAI_API_KEY or client is None:
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
        telegram_file = await context.bot.get_file(
            largest_photo.file_id
        )

        image_bytes = await telegram_file.download_as_bytearray()

        if len(image_bytes) > AI_IMAGE_MAX_BYTES:
            await update.message.reply_text(
                "⚠️ حجم تصویر برای پردازش زیاد است. "
                "لطفاً تصویر را با حجم کمتر ارسال کنید."
            )
            return

        image_b64 = base64.b64encode(
            bytes(image_bytes)
        ).decode("ascii")

        image_data_url = (
            f"data:image/jpeg;base64,{image_b64}"
        )

        caption = (
            update.message.caption or ""
        ).strip()[:2000]

        if not caption:
            caption = (
                "این تصویر را با دقت بررسی کن. اگر سند، فاکتور، رسید "
                "یا مدرک حسابداری است، اطلاعات قابل خواندن را استخراج "
                "کن و قبل از ارائه ثبت حسابداری، تمام مفروضات مؤثر "
                "مانند دائمی/ادواری و نقدی/نسیه را بررسی کن. اگر "
                "اطلاعاتی برای پاسخ قطعی کافی نیست، ابتدا سؤال "
                "روشن‌کننده بپرس."
            )

        thinking_message = await update.message.reply_text(
            "🖼️ در حال بررسی تصویر شما..."
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
            f"OPENAI IMAGE ERROR [{type(e).__name__}]: {e}"
        )

        try:
            await update.message.reply_text(
                "⚠️ در پردازش تصویر مشکلی ایجاد شد.\n"
                "لطفاً تصویر واضح‌تری ارسال کنید یا چند لحظه بعد "
                "دوباره تلاش کنید."
            )
        except Exception:
            pass


# =========================================================
# دوره‌های آموزشی
# =========================================================

async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "courses"

    keyboard = [
        ["🏫 دوره‌های آموزشی حضوری"],
        ["💻 دوره‌های آموزشی آنلاین"],
        ["🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🎓 دوره‌های آموزشی\n\n"
        "نوع دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def in_person_courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "in_person_courses"

    keyboard = [
        ["📊 دوره آموزش پاور کوئری"],
        ["📑 دوره سامانه مودیان"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🏫 دوره‌های آموزشی حضوری\n\n"
        "دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def online_courses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "online_courses"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "💻 دوره‌های آموزشی آنلاین\n\n"
        "در حال حاضر دوره‌ای در این بخش قرار نگرفته است.",
        reply_markup=create_keyboard(keyboard),
    )


async def tax_system(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "tax_system"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📑 دوره آموزش سامانه مودیان\n\n"
        "اطلاعات این دوره به‌زودی در ربات قرار خواهد گرفت.",
        reply_markup=create_keyboard(keyboard),
    )


async def power_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "power_query"

    keyboard = [
        ["📊 مشاهده و ثبت‌نام دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات دوره و ثبت‌نام، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def power_query_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "power_query_link"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات و ثبت‌نام دوره، "
        "روی لینک زیر کلیک کنید:\n\n"
        "https://maliplusco.ir/product/%d9%85%d9%88%d8%b1%d8%b3%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
        reply_markup=create_keyboard(keyboard),
    )


# =========================================================
# ارتباط با ما
# =========================================================

async def contact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "contact"

    keyboard = [
        ["📸 اینستاگرام"],
        ["📢 کانال تلگرام"],
        ["🟠 کانال روبیکا"],
        ["🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def instagram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "instagram"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📸 اینستاگرام:\n\n"
        "https://instagram.com/ali_chavoshi.official",
        reply_markup=create_keyboard(keyboard),
    )


async def telegram_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "telegram"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📢 کانال تلگرام:\n\n"
        "https://t.me/Alichavoshiaccounting",
        reply_markup=create_keyboard(keyboard),
    )


async def rubika(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "rubika"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🟠 کانال روبیکا:\n\n"
        "https://rubika.ir/Alichavoshiaccounting",
        reply_markup=create_keyboard(keyboard),
    )


# =========================================================
# ویدئوهای آموزشی
# =========================================================

async def educational_videos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "educational_videos"

    keyboard = [
        ["📗 ویدئوهای آموزشی مقدماتی اکسل"],
        ["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"],
        ["🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "🎬 ویدئوهای آموزشی\n\n"
        "سطح آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def excel_beginner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "excel_beginner"

    keyboard = [
        ["📥 لینک‌های دانلود دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📗 ویدئوهای آموزشی مقدماتی اکسل\n\n"
        "برای دریافت لینک دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def excel_beginner_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "excel_beginner_download"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی مقدماتی اکسل:\n\n"
        "https://my.uupload.ir/d/pVZXk",
        reply_markup=create_keyboard(keyboard),
    )


async def excel_intermediate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "excel_intermediate"

    keyboard = [
        ["📥 لینک‌های دانلود دوره"],
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\n"
        "برای دریافت لینک دانلود ویدئوهای آموزشی، "
        "گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard(keyboard),
    )


async def excel_intermediate_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["menu_level"] = "excel_intermediate_download"

    keyboard = [
        ["🔙 بازگشت", "🏠 منوی اصلی"],
    ]

    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی سطح نیمه پیشرفته:\n\n"
        "https://my.uupload.ir/d/YL2XN",
        reply_markup=create_keyboard(keyboard),
    )


# =========================================================
# بازگشت
# =========================================================

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data.get("menu_level")

    if level == "ai":
        context.user_data["ai_mode"] = False
        await start(update, context)

    elif level in ["in_person_courses", "online_courses"]:
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
    context: ContextTypes.DEFAULT_TYPE,
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
        start,
    )
)


# =========================================================
# هوش مصنوعی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🤖 دستیار هوش مصنوعی"]),
        ai_assistant,
    )
)


# =========================================================
# منوی اصلی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🎓 دوره‌های آموزشی"]),
        courses,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["🎬 ویدئوهای آموزشی"]),
        educational_videos,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📱 ارتباط با ما"]),
        contact,
    )
)


# =========================================================
# دوره‌های آموزشی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🏫 دوره‌های آموزشی حضوری"]),
        in_person_courses,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["💻 دوره‌های آموزشی آنلاین"]),
        online_courses,
    )
)


# =========================================================
# دوره‌های حضوری
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📊 دوره آموزش پاور کوئری"]),
        power_query,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📑 دوره سامانه مودیان"]),
        tax_system,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📊 مشاهده و ثبت‌نام دوره"]),
        power_query_link,
    )
)


# =========================================================
# ارتباط با ما
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📸 اینستاگرام"]),
        instagram,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📢 کانال تلگرام"]),
        telegram_channel,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["🟠 کانال روبیکا"]),
        rubika,
    )
)


# =========================================================
# ویدئوهای آموزشی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📗 ویدئوهای آموزشی مقدماتی اکسل"]),
        excel_beginner,
    )
)

app.add_handler(
    MessageHandler(
        filters.Text(["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"]),
        excel_intermediate,
    )
)


# =========================================================
# لینک دانلود
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["📥 لینک‌های دانلود دوره"]),
        download_links,
    )
)


# =========================================================
# بازگشت
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🔙 بازگشت"]),
        back,
    )
)


# =========================================================
# منوی اصلی
# =========================================================

app.add_handler(
    MessageHandler(
        filters.Text(["🏠 منوی اصلی"]),
        start,
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
    "🏠 منوی اصلی",
]


app.add_handler(
    MessageHandler(
        filters.PHOTO,
        ask_ai_image,
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT
        & ~filters.COMMAND
        & ~filters.Text(MENU_BUTTONS),
        ask_ai,
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
    webhook_url=f"{URL}/telegram",
)
