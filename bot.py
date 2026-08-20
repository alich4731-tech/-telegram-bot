import os
import re
import html
import base64

from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================================================
# تنظیمات
# =========================================================
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
URL = os.getenv("RENDER_EXTERNAL_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# اگر در Environment Variables مقدار AI_MODEL داری، همان استفاده می‌شود.
# مقدار پیش‌فرض را روی یک مدل API رسمی و عمومی گذاشته‌ایم.
AI_MODEL = os.getenv("AI_MODEL", "gpt-5.1")
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "2400"))
AI_MAX_OUTPUT_TOKENS_LEGAL = int(os.getenv("AI_MAX_OUTPUT_TOKENS_LEGAL", "4200"))
AI_MAX_OUTPUT_TOKENS_HARD_CAP = int(os.getenv("AI_MAX_OUTPUT_TOKENS_HARD_CAP", "6000"))
AI_HISTORY_MESSAGES = int(os.getenv("AI_HISTORY_MESSAGES", "6"))
AI_HISTORY_CHAR_LIMIT = int(os.getenv("AI_HISTORY_CHAR_LIMIT", "1800"))
AI_IMAGE_MAX_BYTES = int(os.getenv("AI_IMAGE_MAX_BYTES", "10000000"))
AI_WEB_SEARCH_CONTEXT = os.getenv("AI_WEB_SEARCH_CONTEXT", "high")

if not TOKEN:
    raise ValueError("BOT_TOKEN در Environment Variables تنظیم نشده است.")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY تنظیم نشده است.")
if not URL:
    raise ValueError("RENDER_EXTERNAL_URL در Environment Variables تنظیم نشده است.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =========================================================
# پرامپت اصلی هوش مصنوعی
# =========================================================
AI_SYSTEM_PROMPT = """
نقش: دستیار هوشمند حسابداری ACN برای ایران.

اصل اول: دقت از سرعت مهم‌تر است. هرگز عدد، مبلغ، نرخ، درصد، مهلت، سقف معافیت،
مزایا، حکم قانونی یا اطلاعات جاری را از حافظه یا حدس اعلام نکن.

حوزه‌های مجاز:
• حسابداری و مالی
• حسابرسی
• مالیات و ارزش افزوده
• تأمین اجتماعی و بیمه
• حقوق و دستمزد و مزایای کارگران/کارکنان در ایران
• سامانه مؤدیان و صورتحساب الکترونیکی
• اکسل و Power Query مرتبط با حسابداری

اگر سؤال کاملاً خارج از حوزه است، کوتاه بگو این دستیار برای موضوعات حسابداری،
مالی، حسابرسی، مالیات، تأمین اجتماعی و اکسل/Power Query مرتبط با حسابداری طراحی شده است.

=========================================================
وب‌گردی اجباری برای اطلاعات جاری و قانونی
=========================================================
هرگاه سؤال به قانون، مقررات یا اطلاعات روز وابسته است، حتماً از Web Search استفاده کن.
این قانون شامل موارد زیر است:
• قانون، ماده، تبصره، بند، بخشنامه، دستورالعمل، آیین‌نامه، رأی، مصوبه
• مالیات، ارزش افزوده، سامانه مؤدیان، تأمین اجتماعی و بیمه
• حقوق و دستمزد، حداقل مزد، حق مسکن، بن، حق تأهل، حق اولاد، پایه سنوات و مزایا
• هر رقم مربوط به سال مشخص، مخصوصاً ۱۴۰۵
• امسال، سال جاری، فعلی، جدیدترین، آخرین، به‌روز، الان و موارد مشابه
• ادامه مکالمه‌ای که موضوع آن قانونی یا وابسته به اطلاعات جاری بوده است

حتی اگر سؤال خیلی کوتاه باشد، مثل «مبلغش چقدره؟» یا «عددش رو بگو»، اگر تاریخچه
نشان دهد موضوع قانونی/حقوقی/مالیاتی است، دوباره Web Search انجام بده.

اگر کاربر URL یا نام یک مقاله را داده است، آن منبع را هم بررسی کن. اگر صفحه قابل
دسترسی بود، محتوای آن را با منابع معتبر دیگر تطبیق بده.

اولویت منابع:
1. متن رسمی مقرره و دستگاه صادرکننده
2. دولت، وزارت تعاون، کار و رفاه اجتماعی، سازمان تأمین اجتماعی، سازمان امور مالیاتی،
مجلس، روزنامه رسمی و سایر مراجع رسمی
3. منابع تخصصی معتبر حسابداری و مالیاتی ایران

اگر منبع رسمی پیدا نشد ولی چند منبع تخصصی معتبر مستقل رقم واحدی را تأیید کردند،
رقم را اعلام کن و بگو «طبق منابع تخصصی». هرگز فقط به دلیل نبود صفحه رسمی، رقم را
بی‌دلیل رد نکن.

اگر منابع با هم تعارض دارند، تعارض را کوتاه توضیح بده و آخرین/معتبرترین منبع را مبنا قرار بده.
اگر هیچ منبع قابل اتکایی رقم را تأیید نکرد، عدد نساز و صریح بگو «منبع قابل اتکای کافی
برای تأیید رقم پیدا نشد».

=========================================================
دقت عددی
=========================================================
• ریال و تومان را هرگز جابه‌جا نکن.
• در ارقام حقوقی، سال را دقیق بررسی کن.
• رقم را با متن منبع تطبیق بده.
• اگر رقم روزانه و ماهانه متفاوت است، واحد را مشخص کن.
• اگر کاربر یک رقم یا ادعای نادرست گفت، آن را حقیقت قطعی فرض نکن؛ دوباره بررسی کن.

=========================================================
تحلیل سؤال
=========================================================
قبل از پاسخ مشخص کن منظور دقیق کاربر چیست.
اگر ابهام واقعاً نتیجه را تغییر می‌دهد، یک سؤال روشن‌کننده کوتاه بپرس.
اگر پاسخ را می‌توان با فرض معقول داد، فرض را کوتاه و شفاف بیان کن.

برای ثبت حسابداری، دائمی/ادواری، نقدی/نسیه، مالیات و عوارض و سایر مفروضات مؤثر را بررسی کن.

=========================================================
فرمت تلگرام
=========================================================
فارسی، دقیق، حرفه‌ای و مستقیم بنویس.
از Markdown ستاره‌ای استفاده نکن.
بولت‌ها با «•» باشند.
ایموجی طبیعی و متوسط استفاده کن.
سؤال ساده → کوتاه.
سؤال تخصصی → منظم و کامل.
در پایان پیشنهاد ادامه گفتگو نده.

URL خام در متن پاسخ ننویس.
اگر Web Search استفاده شد، فقط در انتهای پاسخ یک خط متنی با این قالب بیاور:
📚 منبع: <توصیف کوتاه منابع بررسی‌شده>

خودت URL، دامنه یا Markdown link در متن پاسخ تولید نکن؛ سیستم تلگرام لینک منابع را جداگانه اضافه می‌کند.
"""

# =========================================================
# ابزارهای کمکی
# =========================================================
def create_keyboard(buttons):
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def normalize_fa(text: str) -> str:
    return (
        (text or "")
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ۀ", "ه")
        .replace("ة", "ه")
        .strip()
    )


LEGAL_KEYWORDS = [
    "قانون", "ماده", "تبصره", "بند", "بخشنامه", "دستورالعمل", "آیین نامه", "آیین‌نامه",
    "رأی", "رای", "ابطال", "اصلاحیه", "سامانه مؤدیان", "سامانه مودیان", "مالیات",
    "ارزش افزوده", "تأمین اجتماعی", "تامین اجتماعی", "حق بیمه", "بیمه", "مصوبه",
    "تصویب نامه", "تصویب‌نامه", "بودجه", "لایحه بودجه", "حداقل دستمزد", "حداقل حقوق",
    "حقوق و دستمزد", "حق تأهل", "حق تاهل", "حق اولاد", "حق مسکن", "بن کارگری",
    "پایه سنوات", "جرائم", "جریمه"
]

CURRENT_KEYWORDS = [
    "امسال", "سال جاری", "سال جدید", "فعلی", "جدیدترین", "آخرین", "به روز", "به‌روز",
    "در حال حاضر", "الان", "۱۴۰۵", "1405", "۱۴۰۴", "1404", "۱۴۰۳", "1403", "۲۰۲۶", "2026"
]

PAYROLL_TERMS = [
    "حق تأهل", "حق تاهل", "حق اولاد", "حق مسکن", "بن کارگری", "بن کارگر", "سنوات",
    "پایه سنوات", "مزد", "دستمزد", "حقوق کارگر", "حقوق کارگران"
]

NUMERIC_TERMS = ["چقدر", "مبلغ", "نرخ", "درصد", "چند", "محاسبه", "عدد"]


def is_legal_or_current(text: str) -> bool:
    t = normalize_fa(text)
    if any(k in t for k in LEGAL_KEYWORDS):
        return True
    if any(k in t for k in CURRENT_KEYWORDS):
        return True
    return any(k in t for k in PAYROLL_TERMS) and any(k in t for k in NUMERIC_TERMS)


def extract_output_text(response) -> str:
    text = (getattr(response, "output_text", None) or "").strip()
    if text:
        return text

    collected = []
    try:
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []) or []:
                value = getattr(content, "text", None)
                if value:
                    collected.append(value)
    except Exception as e:
        print(f"OUTPUT EXTRACTION WARNING: {e}")

    return "".join(collected).strip()


def collect_source_urls(response):
    citations = []
    seen = set()
    try:
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                for ann in getattr(content, "annotations", []) or []:
                    url = getattr(ann, "url", None)
                    if url and url not in seen:
                        seen.add(url)
                        citations.append({
                            "url": url,
                            "title": getattr(ann, "title", None),
                        })
    except Exception as e:
        print(f"SOURCE EXTRACTION WARNING: {e}")
    return citations[:8]


def clean_ai_text(text: str) -> str:
    text = (text or "").replace("```", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.S)
    text = re.sub(r"\*(.*?)\*", r"\1", text, flags=re.S)
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[\*-]\s+", "• ", text)
    text = re.sub(r"\[([^]]+)\]\(https?://[^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    return text.strip()


def telegram_html_with_sources(text, citations):
    safe = html.escape(text, quote=False)
    if not citations:
        return safe

    links = []
    for citation in citations:
        url = citation.get("url")
        if url:
            links.append(f'<a href="{html.escape(url, quote=True)}">🔗</a>')

    return safe + ("\n\n📚 منابع: " + " ".join(links) if links else "")


async def send_ai_answer(message, answer, source_citations=None, edit_message=None):
    answer = clean_ai_text(answer)
    source_citations = source_citations or []
    max_text_length = 3500
    chunks = [answer[i:i + max_text_length] for i in range(0, len(answer), max_text_length)] or [""]

    for index, chunk in enumerate(chunks):
        rendered = (
            telegram_html_with_sources(chunk, source_citations)
            if index == len(chunks) - 1
            else html.escape(chunk, quote=False)
        )

        if index == 0 and edit_message is not None:
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

# =========================================================
# هسته درخواست AI
# =========================================================
def build_input(history, input_parts):
    result = []
    for item in history:
        result.append({
            "role": item["role"],
            "content": item["content"],
        })
    result.append({"role": "user", "content": input_parts})
    return result


async def request_ai(input_parts, question_for_history, context, image_mode=False):
    history = context.user_data.setdefault("ai_history", [])
    recent_history = history[-AI_HISTORY_MESSAGES:]

    history_text = " ".join(
        str(item.get("content", ""))
        for item in recent_history
        if isinstance(item, dict)
    )

    # نکته کلیدی: سؤال فعلی + تاریخچه هر دو بررسی می‌شوند.
    # بنابراین «عددش رو بگو» هم اگر ادامه یک سؤال قانونی باشد، Web Search اجباری دارد.
    needs_search = (
        is_legal_or_current(question_for_history)
        or is_legal_or_current(history_text)
    )

    combined_input = build_input(recent_history, input_parts)

    # اگر کاربر URL داده، URL را به عنوان منبع پیشنهادی صریحاً به مدل معرفی می‌کنیم.
    user_urls = re.findall(r"https?://\S+", question_for_history)
    if user_urls:
        combined_input.insert(0, {
            "role": "developer",
            "content": (
                "کاربر منبع زیر را پیشنهاد کرده است. اگر قابل دسترسی است، خود صفحه را بررسی کن "
                "و اطلاعات آن را با منابع معتبر دیگر تطبیق بده: " + " ".join(user_urls)
            ),
        })

    base_tokens = AI_MAX_OUTPUT_TOKENS_LEGAL if needs_search else AI_MAX_OUTPUT_TOKENS

    def build_request(max_tokens):
        request = {
            "model": AI_MODEL,
            "instructions": AI_SYSTEM_PROMPT,
            "input": combined_input,
            "max_output_tokens": max_tokens,
        }

        if needs_search:
            request["tools"] = [{
                "type": "web_search",
                "search_context_size": AI_WEB_SEARCH_CONTEXT,
            }]

            # مهم‌ترین اصلاح نسبت به کد قبلی:
            # در سؤالات قانونی/جاری، ابزار جست‌وجو فقط در اختیار مدل نیست؛ اجباری است.
            request["tool_choice"] = "required"

        return request

    attempts = [
        base_tokens,
        min(AI_MAX_OUTPUT_TOKENS_HARD_CAP, base_tokens * 2),
    ]

    response = None
    answer = ""

    for attempt_index, token_budget in enumerate(attempts, 1):
        try:
            current_response = client.responses.create(
                **build_request(token_budget)
            )
        except Exception as e:
            print(
                f"OPENAI CALL ERROR attempt={attempt_index} "
                f"type={type(e).__name__}: {e}"
            )
            continue

        response = current_response
        candidate = extract_output_text(current_response)
        answer = candidate or answer

        status = getattr(current_response, "status", None)
        details = getattr(current_response, "incomplete_details", None)
        reason = getattr(details, "reason", None) if details else None

        print(
            f"AI ATTEMPT {attempt_index}: status={status}, "
            f"incomplete_reason={reason}, chars={len(candidate)}, "
            f"web_required={needs_search}"
        )

        if candidate and not (
            status == "incomplete" and reason == "max_output_tokens"
        ):
            break

    if not answer:
        if needs_search:
            return (
                "⚠️ این سؤال به اطلاعات قانونی یا جاری وابسته است و باید با جست‌وجوی وب تأیید شود، "
                "اما در این درخواست نتیجه قابل استفاده‌ای از جست‌وجو دریافت نشد. برای جلوگیری از "
                "اعلام رقم یا حکم اشتباه، پاسخ قطعی ارائه نمی‌کنم.",
                [],
            )
        return (
            "⚠️ پاسخی از سرویس هوش مصنوعی دریافت نشد. لطفاً دوباره تلاش کنید.",
            [],
        )

    history.append({
        "role": "user",
        "content": question_for_history[:AI_HISTORY_CHAR_LIMIT],
    })
    history.append({
        "role": "assistant",
        "content": answer[:AI_HISTORY_CHAR_LIMIT],
    })
    del history[:-AI_HISTORY_MESSAGES]

    return answer, collect_source_urls(response) if response else []

# =========================================================
# هوش مصنوعی
# =========================================================
async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "ai"
    context.user_data["ai_mode"] = True
    context.user_data["ai_history"] = []

    await update.message.reply_text(
        "🤖✨ به دستیار هوشمند حسابداری ACN خوش آمدید\n\n"
        "📚 سؤال خود را درباره حسابداری، مالی، حسابرسی، مالیات، تأمین اجتماعی، "
        "حقوق و دستمزد یا اکسل/Power Query مرتبط با حسابداری ارسال کنید.\n\n"
        "🖼️ امکان ارسال تصویر سند و فاکتور نیز فعال است.\n\n"
        "🔙 برای خروج، گزینه «بازگشت» را بزنید.",
        reply_markup=create_keyboard([["🔙 بازگشت"]]),
    )


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode", False):
        return

    question = (update.message.text or "").strip()[:3000]
    if not question:
        return

    if not client:
        await update.message.reply_text(
            "⚠️ اتصال دستیار هوشمند تنظیم نشده است.\n"
            "OPENAI_API_KEY را در Environment Variables بررسی کنید."
        )
        return

    thinking = await update.message.reply_text(
        "🔍 در حال بررسی و تطبیق اطلاعات با منابع به‌روز..."
        if is_legal_or_current(question)
        else "🤖 در حال بررسی سؤال شما..."
    )

    try:
        input_parts = [{
            "type": "input_text",
            "text": question,
        }]

        answer, source_urls = await request_ai(
            input_parts,
            question,
            context,
            image_mode=False,
        )

        await send_ai_answer(
            update.message,
            answer,
            source_urls,
            edit_message=thinking,
        )

    except Exception as e:
        print(f"OPENAI TEXT ERROR [{type(e).__name__}]: {e}")
        await thinking.edit_text(
            "⚠️ در پردازش سؤال مشکلی ایجاد شد.\n"
            "لطفاً چند لحظه بعد دوباره تلاش کنید."
        )


async def ask_ai_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode", False):
        return

    if not client:
        await update.message.reply_text(
            "⚠️ اتصال دستیار هوشمند تنظیم نشده است. OPENAI_API_KEY را بررسی کنید."
        )
        return

    photo = update.message.photo
    if not photo:
        return

    largest_photo = photo[-1]
    telegram_file = await context.bot.get_file(largest_photo.file_id)
    image_bytes = await telegram_file.download_as_bytearray()

    if len(image_bytes) > AI_IMAGE_MAX_BYTES:
        await update.message.reply_text(
            "⚠️ حجم تصویر برای پردازش زیاد است. لطفاً تصویر کم‌حجم‌تری ارسال کنید."
        )
        return

    image_b64 = base64.b64encode(bytes(image_bytes)).decode("ascii")
    image_data_url = f"data:image/jpeg;base64,{image_b64}"

    caption = (update.message.caption or "").strip()[:2000]
    if not caption:
        caption = (
            "این تصویر را دقیق بررسی کن. اگر سند، فاکتور، رسید یا مدرک حسابداری است، "
            "اطلاعات خوانا را استخراج کن. اعداد و تاریخ‌های ناخوانا را حدس نزن. "
            "قبل از ثبت حسابداری، مفروضات مؤثر مانند دائمی/ادواری و نقدی/نسیه را بررسی کن."
        )

    thinking = await update.message.reply_text("🖼️ در حال بررسی تصویر شما...")

    try:
        input_parts = [
            {"type": "input_text", "text": caption},
            {
                "type": "input_image",
                "image_url": image_data_url,
                "detail": "high",
            },
        ]

        answer, source_urls = await request_ai(
            input_parts,
            caption,
            context,
            image_mode=True,
        )

        await send_ai_answer(
            update.message,
            answer,
            source_urls,
            edit_message=thinking,
        )

    except Exception as e:
        print(f"OPENAI IMAGE ERROR [{type(e).__name__}]: {e}")
        await thinking.edit_text(
            "⚠️ در پردازش تصویر مشکلی ایجاد شد.\n"
            "لطفاً تصویر واضح‌تری ارسال کنید."
        )

# =========================================================
# منوها
# =========================================================
async def start(update, context):
    context.user_data["menu_level"] = "main"
    context.user_data["ai_mode"] = False
    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات ما خوش آمدید 🌱\n\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=create_keyboard([
            ["🎓 دوره‌های آموزشی", "🎬 ویدئوهای آموزشی"],
            ["🤖 دستیار هوش مصنوعی"],
            ["📱 ارتباط با ما"],
        ]),
    )


async def courses(update, context):
    context.user_data["menu_level"] = "courses"
    await update.message.reply_text(
        "🎓 دوره‌های آموزشی\n\nنوع دوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard([
            ["🏫 دوره‌های آموزشی حضوری"],
            ["💻 دوره‌های آموزشی آنلاین"],
            ["🏠 منوی اصلی"],
        ]),
    )


async def in_person_courses(update, context):
    context.user_data["menu_level"] = "in_person_courses"
    await update.message.reply_text(
        "🏫 دوره‌های آموزشی حضوری\n\nدوره مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard([
            ["📊 دوره آموزش پاور کوئری"],
            ["📑 دوره سامانه مودیان"],
            ["🔙 بازگشت", "🏠 منوی اصلی"],
        ]),
    )


async def online_courses(update, context):
    context.user_data["menu_level"] = "online_courses"
    await update.message.reply_text(
        "💻 دوره‌های آموزشی آنلاین\n\nدر حال حاضر دوره‌ای در این بخش قرار نگرفته است.",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def tax_system(update, context):
    context.user_data["menu_level"] = "tax_system"
    await update.message.reply_text(
        "📑 دوره آموزش سامانه مودیان\n\nاطلاعات این دوره به‌زودی در ربات قرار خواهد گرفت.",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def power_query(update, context):
    context.user_data["menu_level"] = "power_query"
    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\nبرای مشاهده جزئیات و ثبت‌نام، گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard([
            ["📊 مشاهده و ثبت‌نام دوره"],
            ["🔙 بازگشت", "🏠 منوی اصلی"],
        ]),
    )


async def power_query_link(update, context):
    context.user_data["menu_level"] = "power_query_link"
    await update.message.reply_text(
        "📊 دوره آموزش پاور کوئری\n\n"
        "برای مشاهده جزئیات و ثبت‌نام دوره، روی لینک زیر کلیک کنید:\n\n"
        "https://maliplusco.ir/product/%d9%85%d9%88%d8%b1%d8%b3%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def contact(update, context):
    context.user_data["menu_level"] = "contact"
    await update.message.reply_text(
        "📱 راه‌های ارتباط با ما:\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=create_keyboard([
            ["📸 اینستاگرام"],
            ["📢 کانال تلگرام"],
            ["🟠 کانال روبیکا"],
            ["🏠 منوی اصلی"],
        ]),
    )


async def instagram(update, context):
    context.user_data["menu_level"] = "instagram"
    await update.message.reply_text(
        "📸 اینستاگرام:\n\nhttps://instagram.com/ali_chavoshi.official",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def telegram_channel(update, context):
    context.user_data["menu_level"] = "telegram"
    await update.message.reply_text(
        "📢 کانال تلگرام:\n\nhttps://t.me/Alichavoshiaccounting",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def rubika(update, context):
    context.user_data["menu_level"] = "rubika"
    await update.message.reply_text(
        "🟠 کانال روبیکا:\n\nhttps://rubika.ir/Alichavoshiaccounting",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def educational_videos(update, context):
    context.user_data["menu_level"] = "educational_videos"
    await update.message.reply_text(
        "🎬 ویدئوهای آموزشی\n\nسطح آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=create_keyboard([
            ["📗 ویدئوهای آموزشی مقدماتی اکسل"],
            ["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"],
            ["🏠 منوی اصلی"],
        ]),
    )


async def excel_beginner(update, context):
    context.user_data["menu_level"] = "excel_beginner"
    await update.message.reply_text(
        "📗 ویدئوهای آموزشی مقدماتی اکسل\n\nبرای دریافت لینک دانلود، گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard([["📥 لینک‌های دانلود دوره"], ["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def excel_beginner_download(update, context):
    context.user_data["menu_level"] = "excel_beginner_download"
    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی مقدماتی اکسل:\n\nhttps://my.uupload.ir/d/pVZXk",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def excel_intermediate(update, context):
    context.user_data["menu_level"] = "excel_intermediate"
    await update.message.reply_text(
        "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\nبرای دریافت لینک دانلود، گزینه زیر را انتخاب کنید:",
        reply_markup=create_keyboard([["📥 لینک‌های دانلود دوره"], ["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def excel_intermediate_download(update, context):
    context.user_data["menu_level"] = "excel_intermediate_download"
    await update.message.reply_text(
        "📥 لینک دانلود ویدئوهای آموزشی سطح نیمه پیشرفته:\n\nhttps://my.uupload.ir/d/YL2XN",
        reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]),
    )


async def back(update, context):
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


async def download_links(update, context):
    level = context.user_data.get("menu_level")
    if level == "excel_beginner":
        await excel_beginner_download(update, context)
    elif level == "excel_intermediate":
        await excel_intermediate_download(update, context)

# =========================================================
# ثبت Handlerها
# =========================================================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(MessageHandler(filters.Text(["🤖 دستیار هوش مصنوعی"]), ai_assistant))
app.add_handler(MessageHandler(filters.Text(["🎓 دوره‌های آموزشی"]), courses))
app.add_handler(MessageHandler(filters.Text(["🎬 ویدئوهای آموزشی"]), educational_videos))
app.add_handler(MessageHandler(filters.Text(["📱 ارتباط با ما"]), contact))

app.add_handler(MessageHandler(filters.Text(["🏫 دوره‌های آموزشی حضوری"]), in_person_courses))
app.add_handler(MessageHandler(filters.Text(["💻 دوره‌های آموزشی آنلاین"]), online_courses))
app.add_handler(MessageHandler(filters.Text(["📊 دوره آموزش پاور کوئری"]), power_query))
app.add_handler(MessageHandler(filters.Text(["📑 دوره سامانه مودیان"]), tax_system))
app.add_handler(MessageHandler(filters.Text(["📊 مشاهده و ثبت‌نام دوره"]), power_query_link))

app.add_handler(MessageHandler(filters.Text(["📸 اینستاگرام"]), instagram))
app.add_handler(MessageHandler(filters.Text(["📢 کانال تلگرام"]), telegram_channel))
app.add_handler(MessageHandler(filters.Text(["🟠 کانال روبیکا"]), rubika))

app.add_handler(MessageHandler(filters.Text(["📗 ویدئوهای آموزشی مقدماتی اکسل"]), excel_beginner))
app.add_handler(MessageHandler(filters.Text(["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"]), excel_intermediate))
app.add_handler(MessageHandler(filters.Text(["📥 لینک‌های دانلود دوره"]), download_links))

app.add_handler(MessageHandler(filters.Text(["🔙 بازگشت"]), back))
app.add_handler(MessageHandler(filters.Text(["🏠 منوی اصلی"]), start))

MENU_BUTTONS = [
    "🤖 دستیار هوش مصنوعی", "🎓 دوره‌های آموزشی", "🎬 ویدئوهای آموزشی", "📱 ارتباط با ما",
    "🏫 دوره‌های آموزشی حضوری", "💻 دوره‌های آموزشی آنلاین", "📊 دوره آموزش پاور کوئری",
    "📑 دوره سامانه مودیان", "📊 مشاهده و ثبت‌نام دوره", "📸 اینستاگرام", "📢 کانال تلگرام",
    "🟠 کانال روبیکا", "📗 ویدئوهای آموزشی مقدماتی اکسل", "📘 ویدئوهای آموزشی نیمه پیشرفته اکسل",
    "📥 لینک‌های دانلود دوره", "🔙 بازگشت", "🏠 منوی اصلی"
]

# عکس قبل از پیام متنی بررسی می‌شود.
app.add_handler(MessageHandler(filters.PHOTO, ask_ai_image))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Text(MENU_BUTTONS),
        ask_ai,
    )
)

# =========================================================
# اجرای Webhook روی Render
# =========================================================
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="telegram",
    webhook_url=f"{URL}/telegram",
)
