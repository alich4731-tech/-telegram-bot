import os
import asyncio
import base64
import html
import re
import time

from openai import OpenAI

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from ai_usage import (
    AI_QUESTION_LIMIT,
    can_ask_ai,
    consume_ai_question,
    get_ai_questions_remaining,
)


TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
URL = os.getenv("RENDER_EXTERNAL_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-5.6-luna")
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "5200"))
AI_MAX_OUTPUT_TOKENS_LEGAL = int(os.getenv("AI_MAX_OUTPUT_TOKENS_LEGAL", "5200"))
AI_MAX_OUTPUT_TOKENS_HARD_CAP = int(os.getenv("AI_MAX_OUTPUT_TOKENS_HARD_CAP", "5200"))
AI_HISTORY_MESSAGES = int(os.getenv("AI_HISTORY_MESSAGES", "6"))
AI_HISTORY_CHAR_LIMIT = int(os.getenv("AI_HISTORY_CHAR_LIMIT", "1600"))
AI_IMAGE_MAX_BYTES = int(os.getenv("AI_IMAGE_MAX_BYTES", "10000000"))
AI_WEB_SEARCH_CONTEXT = os.getenv("AI_WEB_SEARCH_CONTEXT", "high")
AI_LEGAL_RETRY_ENABLED = os.getenv("AI_LEGAL_RETRY_ENABLED", "true").strip().lower() == "true"

CHANNEL_USERNAME = "@Alichavoshiaccounting"
CHANNEL_NAME = "Alichavoshiaccounting"

if not TOKEN:
    raise ValueError("BOT_TOKEN در Environment Variables تنظیم نشده است.")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY تنظیم نشده است.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

AI_SYSTEM_PROMPT = """
نقش:
تو دستیار هوشمند حسابداری ACN هستی.

حوزه تخصصی تو:
• حسابداری
• حسابرسی
• امور مالی
• مالیات ایران
• تأمین اجتماعی
• حقوق و دستمزد
• سامانه مؤدیان
• ارزش افزوده
• اکسل
• Power Query در حوزه حسابداری
• سایر موضوعات مستقیم و مرتبط با حسابداری و مالی

قانون اصلی پاسخ‌گویی:
• سؤال ساده → پاسخ ساده و کوتاه
• سؤال مشخص → پاسخ مستقیم
• سؤال تخصصی → پاسخ کامل و منظم
• سؤال چندحالتی و مبهم → ابتدا سؤال روشن‌کننده کوتاه
• سؤال قانونی و به‌روز → تحقیق و تطبیق چندمنبعی
• سؤال آموزشی → مرحله‌به‌مرحله و به اندازه نیاز

در پاسخ‌های قانونی، مالیاتی، بیمه‌ای، حقوق و دستمزد و مقررات ایران، Web Search انجام بده و هیچ شماره ماده، تبصره، بند، جزء، ردیف، بخشنامه، آیین‌نامه، تاریخ، مبلغ یا درصد قانونی را حدس نزن. منبع رسمی و منابع معتبر دیگر را بررسی کن. URL و لینک را در پاسخ نهایی نمایش نده. اگر سؤال قانونی است، در انتهای پاسخ فقط بخش کوتاه «📌 مبنای قانونی» را اضافه کن.

این دستیار فقط برای موضوعات حسابداری، حسابرسی، امور مالی، مالیات ایران، تأمین اجتماعی، حقوق و دستمزد، سامانه مؤدیان، ارزش افزوده و اکسل/Power Query مرتبط با حسابداری است. اگر سؤال کاملاً خارج از این حوزه‌هاست، فقط بگو:
«این دستیار فقط برای پاسخ‌گویی به پرسش‌های حسابداری، مالی، حسابرسی، مالیات، تأمین اجتماعی و اکسل/Power Query مرتبط با حسابداری طراحی شده است.»

در فرمت تلگرام از Markdown پررنگ/کج و URL خام استفاده نکن. بولت‌ها را با «•» شروع کن.
"""

LEGAL_RESEARCH_INSTRUCTION = """
این سؤال قانونی/مالیاتی/مقرراتی است. قبل از پاسخ، منبع رسمی و منابع معتبر دیگر را بررسی کن. شماره ماده، تبصره، بند، جزء، ردیف، جدول، تاریخ، مبلغ یا عنوان مقرره را حدس نزن. اگر مشخصات دقیق قابل احراز نیست، صریحاً اعلام کن. URLها را نمایش نده و «📌 مبنای قانونی» را آخرین بخش پاسخ قرار بده.
"""


def create_keyboard(buttons):
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return False
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user.id)
        status = getattr(member, "status", None)
        if status in ("creator", "administrator", "member"):
            return True
        if status == "restricted":
            return bool(getattr(member, "is_member", False))
        return False
    except Exception as e:
        print(f"CHANNEL MEMBERSHIP CHECK ERROR [{type(e).__name__}]: {e}")
        return False


async def show_channel_membership_required(update: Update, context: ContextTypes.DEFAULT_TYPE, return_to_main=False):
    context.user_data["ai_mode"] = False
    context.user_data["menu_level"] = "main"
    keyboard = [["🏠 منوی اصلی"]]
    if return_to_main:
        text = (
            "⚠️ دسترسی به دستیار هوشمند قطع شد.\n\n"
            f"برای استفاده از دستیار هوشمند باید عضو کانال @{CHANNEL_NAME} باشید.\n\n"
            "پس از عضویت، ابتدا به «🏠 منوی اصلی» بروید و سپس دوباره گزینه «🤖 دستیار هوش مصنوعی» را انتخاب کنید."
        )
    else:
        text = (
            "🔒 دسترسی به دستیار هوشمند\n\n"
            f"این هوش مصنوعی مخصوص اعضای کانال @{CHANNEL_NAME} است.\n\n"
            "برای استفاده از دستیار ابتدا عضو کانال شوید."
        )
    await update.effective_message.reply_text(text, reply_markup=create_keyboard(keyboard))


async def ensure_ai_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_channel_membership(update, context):
        return True
    await show_channel_membership_required(update, context, return_to_main=True)
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "main"
    context.user_data["ai_mode"] = False
    keyboard = [
        ["🎓 دوره‌های آموزشی", "🎬 ویدئوهای آموزشی"],
        ["🤖 دستیار هوش مصنوعی"],
        ["📱 ارتباط با ما"],
    ]
    await update.message.reply_text(
        "سلام 👋\n\nبه ربات ما خوش آمدید 🌱\n\nاز منوی زیر گزینه مورد نظر خود را انتخاب کنید.",
        reply_markup=create_keyboard(keyboard),
    )


async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_channel_membership(update, context):
        await show_channel_membership_required(update, context, return_to_main=False)
        return

    user = update.effective_user
    remaining = get_ai_questions_remaining(user.id)
    context.user_data["menu_level"] = "ai"
    context.user_data["ai_mode"] = True
    context.user_data["ai_history"] = []

    keyboard = [["🔙 بازگشت"]]
    if remaining <= 0:
        text = (
            "🤖✨ دستیار هوشمند حسابداری ACN\n\n"
            "هر کاربر در مجموع فقط ۳ سؤال می‌تواند از دستیار هوش مصنوعی بپرسد.\n\n"
            "سهمیه ۳ سؤال شما قبلاً استفاده شده است."
        )
    else:
        text = (
            "🤖✨ به دستیار هوشمند حسابداری ACN خوش آمدید\n\n"
            f"این هوش مصنوعی مخصوص اعضای کانال @{CHANNEL_NAME} است.\n\n"
            "⚠️ هر کاربر در مجموع فقط ۳ سؤال می‌تواند از دستیار هوش مصنوعی بپرسد.\n"
            f"تعداد سؤال باقی‌مانده شما: {remaining}\n\n"
            "📚 سؤال خود را درباره یکی از موضوعات زیر ارسال کنید:\n\n"
            "• 🧾 حسابداری و مالی\n"
            "• 🔍 حسابرسی\n"
            "• 💰 مالیات\n"
            "• 🏛 تأمین اجتماعی\n"
            "• 📊 اکسل و Power Query در حسابداری\n"
            "• 💼 سایر موضوعات مرتبط با حسابداری\n\n"
            "🖼️ امکان ارسال عکس سند، فاکتور یا مدرک حسابداری نیز فعال است.\n\n"
            "🔙 برای خروج از این بخش، گزینه «بازگشت» را انتخاب کنید."
        )
    await update.message.reply_text(text, reply_markup=create_keyboard(keyboard))


def _normalize_persian(text: str) -> str:
    replacements = {"ي":"ی","ى":"ی","ك":"ک","أ":"ا","إ":"ا","آ":"ا","ة":"ه","ؤ":"و","ئ":"ی","ۀ":"ه"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _normalize_for_match(text: str) -> str:
    return _normalize_persian(text).replace("\u200c", "").replace(" ", "")


def _is_legal_question(text: str) -> bool:
    normalized = _normalize_for_match(text)
    keywords = [
        "قانون","ماده","تبصره","بند","جزء","ردیف","جدول","بخشنامه","دستورالعمل","آیین نامه","آیین‌نامه","رأی","رای","ابطال","اصلاحیه","مقررات",
        "سامانه مؤدیان","سامانه مودیان","صورتحساب الکترونیکی","صورت‌حساب الکترونیکی","مالیات","ارزش افزوده","معافیت","جریمه","تأمین اجتماعی","تامین اجتماعی","بیمه","حق بیمه","حداقل دستمزد","حداقل حقوق","حقوق و دستمزد","عیدی","سنوات","بودجه","مصوبه","سقف","نصاب","شورای عالی کار"
    ]
    for keyword in keywords:
        if _normalize_for_match(keyword) in normalized:
            return True
    return bool(re.search(r"(?:۱۴۰|۱۴۱|140|141)[۰-۹0-9]", text))


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


def _collect_source_urls(response):
    citations, seen = [], set()
    try:
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                for annotation in getattr(content, "annotations", []) or []:
                    url = getattr(annotation, "url", None)
                    if url and url not in seen:
                        seen.add(url)
                        citations.append({"url": url, "title": getattr(annotation, "title", None)})
    except Exception as e:
        print(f"SOURCE EXTRACTION WARNING: {e}")
    return citations[:10]


def _clean_ai_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("```", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.S)
    text = re.sub(r"\*(.*?)\*", r"\1", text, flags=re.S)
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "• ", text)
    text = re.sub(r"\[(.*?)\]\(https?://[^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def _send_ai_answer(message, answer, source_citations=None, edit_message=None):
    answer = _clean_ai_text(answer)
    chunks = [answer[i:i+3500] for i in range(0, len(answer), 3500)] or [""]
    if edit_message is not None:
        await edit_message.edit_text(html.escape(chunks[0], quote=False), parse_mode="HTML", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await message.reply_text(html.escape(chunk, quote=False), parse_mode="HTML", disable_web_page_preview=True)
    else:
        for chunk in chunks:
            await message.reply_text(html.escape(chunk, quote=False), parse_mode="HTML", disable_web_page_preview=True)


async def _request_ai(input_parts, question_for_history, context, image_mode=False):
    history = context.user_data.setdefault("ai_history", [])
    recent_history = history[-AI_HISTORY_MESSAGES:]
    combined_input = [{"role": item["role"], "content": item["content"]} for item in recent_history]
    combined_input.append({"role":"user","content":input_parts})

    history_text = " ".join(item.get("content", "") for item in recent_history if isinstance(item.get("content"), str))
    legal = _is_legal_question(question_for_history) or _is_legal_question(history_text)
    if legal:
        combined_input.append({"role":"user","content":[{"type":"input_text","text":LEGAL_RESEARCH_INSTRUCTION}]})

    base_tokens = max(AI_MAX_OUTPUT_TOKENS_LEGAL, AI_MAX_OUTPUT_TOKENS) if legal else AI_MAX_OUTPUT_TOKENS
    base_tokens = min(base_tokens, AI_MAX_OUTPUT_TOKENS_HARD_CAP)

    attempts = [{"tokens":base_tokens,"search":legal,"required":legal}]
    if legal and AI_LEGAL_RETRY_ENABLED:
        attempts.append({"tokens":AI_MAX_OUTPUT_TOKENS_HARD_CAP,"search":True,"required":True})

    response = None
    answer = ""
    for attempt in attempts:
        args = {"model":AI_MODEL,"instructions":AI_SYSTEM_PROMPT,"input":combined_input,"max_output_tokens":attempt["tokens"]}
        if attempt["search"]:
            args["tools"] = [{"type":"web_search","search_context_size":AI_WEB_SEARCH_CONTEXT}]
        if attempt["required"]:
            args["tool_choice"] = "required"
        try:
            attempt_response = client.responses.create(**args)
        except Exception as e:
            print(f"OPENAI CALL ERROR [{type(e).__name__}]: {e}")
            continue
        attempt_answer = _extract_output_text(attempt_response)
        if attempt_answer:
            response, answer = attempt_response, attempt_answer
            incomplete_details = getattr(attempt_response, "incomplete_details", None)
            incomplete_reason = getattr(incomplete_details, "reason", None) if incomplete_details else None
            if not (getattr(attempt_response, "status", None) == "incomplete" and incomplete_reason == "max_output_tokens"):
                break

    if not answer:
        return ("⚠️ پاسخی از سرویس هوش مصنوعی دریافت نشد. لطفاً دوباره تلاش کنید.", [])

    source_urls = _collect_source_urls(response) if response is not None else []
    history.append({"role":"user","content":question_for_history[:AI_HISTORY_CHAR_LIMIT]})
    history.append({"role":"assistant","content":answer[:AI_HISTORY_CHAR_LIMIT]})
    if len(history) > AI_HISTORY_MESSAGES:
        del history[:-AI_HISTORY_MESSAGES]
    return answer, source_urls


async def _check_and_consume_ai_quota(update: Update):
    user = update.effective_user
    if not user:
        return False
    if not can_ask_ai(user.id):
        await update.effective_message.reply_text(
            "⛔ سهمیه استفاده شما از دستیار هوش مصنوعی تمام شده است.\n\nهر کاربر در مجموع فقط ۳ سؤال می‌تواند بپرسد."
        )
        return False
    return True


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode", False):
        return
    if not await ensure_ai_membership(update, context):
        return
    if not await _check_and_consume_ai_quota(update):
        return

    user_question = (update.message.text or "").strip()[:3000]
    if not user_question:
        return
    if not OPENAI_API_KEY or client is None:
        await update.message.reply_text("⚠️ اتصال دستیار هوشمند تنظیم نشده است.")
        return

    thinking_message = await update.message.reply_text("🤖 در حال بررسی سؤال شما...")
    try:
        answer, source_urls = await _request_ai([{"type":"input_text","text":user_question}], user_question, context, image_mode=False)
        remaining = consume_ai_question(update.effective_user.id)
        await _send_ai_answer(update.message, answer, source_urls, edit_message=thinking_message)
        await update.message.reply_text(f"📌 تعداد سؤال باقی‌مانده شما: {remaining}")
    except Exception as e:
        print(f"OPENAI TEXT ERROR [{type(e).__name__}]: {e}")
        try:
            await thinking_message.edit_text("⚠️ در پردازش سؤال مشکلی ایجاد شد. لطفاً دوباره تلاش کنید.")
        except Exception:
            pass


async def ask_ai_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode", False):
        return
    if not await ensure_ai_membership(update, context):
        return
    if not await _check_and_consume_ai_quota(update):
        return
    if not OPENAI_API_KEY or client is None:
        await update.message.reply_text("⚠️ اتصال دستیار هوشمند تنظیم نشده است.")
        return
    photo = update.message.photo
    if not photo:
        return

    try:
        largest_photo = photo[-1]
        telegram_file = await context.bot.get_file(largest_photo.file_id)
        image_bytes = await telegram_file.download_as_bytearray()
        if len(image_bytes) > AI_IMAGE_MAX_BYTES:
            await update.message.reply_text("⚠️ حجم تصویر برای پردازش زیاد است. لطفاً تصویر را با حجم کمتر ارسال کنید.")
            return

        image_b64 = base64.b64encode(bytes(image_bytes)).decode("ascii")
        caption = (update.message.caption or "").strip()[:2000] or "این تصویر حسابداری را با دقت بررسی کن و فقط در حوزه تخصصی دستیار پاسخ بده."
        thinking_message = await update.message.reply_text("🖼️ در حال بررسی تصویر شما...")
        input_parts = [
            {"type":"input_text","text":caption},
            {"type":"input_image","image_url":f"data:image/jpeg;base64,{image_b64}","detail":"auto"},
        ]
        answer, source_urls = await _request_ai(input_parts, caption, context, image_mode=True)
        remaining = consume_ai_question(update.effective_user.id)
        await _send_ai_answer(update.message, answer, source_urls, edit_message=thinking_message)
        await update.message.reply_text(f"📌 تعداد سؤال باقی‌مانده شما: {remaining}")
    except Exception as e:
        print(f"OPENAI IMAGE ERROR [{type(e).__name__}]: {e}")
        await update.message.reply_text("⚠️ در پردازش تصویر مشکلی ایجاد شد. لطفاً دوباره تلاش کنید.")


async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "courses"
    keyboard = [["🏫 دوره‌های آموزشی حضوری"],["💻 دوره‌های آموزشی آنلاین"],["🏠 منوی اصلی"]]
    await update.message.reply_text("🎓 دوره‌های آموزشی\n\nنوع دوره مورد نظر خود را انتخاب کنید:", reply_markup=create_keyboard(keyboard))


async def in_person_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "in_person_courses"
    keyboard = [["📊 دوره آموزش پاور کوئری"],["📑 دوره سامانه مودیان"],["🔙 بازگشت", "🏠 منوی اصلی"]]
    await update.message.reply_text("🏫 دوره‌های آموزشی حضوری\n\nدوره مورد نظر خود را انتخاب کنید:", reply_markup=create_keyboard(keyboard))


async def online_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "online_courses"
    await update.message.reply_text("💻 دوره‌های آموزشی آنلاین\n\nدر حال حاضر دوره‌ای در این بخش قرار نگرفته است.", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def tax_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "tax_system"
    await update.message.reply_text("📑 دوره آموزش سامانه مودیان\n\nاطلاعات این دوره به‌زودی در ربات قرار خواهد گرفت.", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def power_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "power_query"
    keyboard = [["📊 مشاهده و ثبت‌نام دوره"],["🔙 بازگشت", "🏠 منوی اصلی"]]
    await update.message.reply_text("📊 دوره آموزش پاور کوئری\n\nبرای مشاهده جزئیات دوره و ثبت‌نام، گزینه زیر را انتخاب کنید:", reply_markup=create_keyboard(keyboard))


async def power_query_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "power_query_link"
    await update.message.reply_text("📊 دوره آموزش پاور کوئری\n\nhttps://maliplusco.ir/product/%d9%85%d9%88%d8%b1%d8%b3%d9%87-%d8%a2%d9%85%d9%88%d8%b2%d8%b4-%d9%be%d8%a7%d9%88%d8%b1-%da%a9%d9%88%d8%a6%d8%b1%db%8c/", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "contact"
    keyboard = [["📸 اینستاگرام"],["📢 کانال تلگرام"],["🟠 کانال روبیکا"],["🏠 منوی اصلی"]]
    await update.message.reply_text("📱 راه‌های ارتباط با ما:\n\nیکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=create_keyboard(keyboard))


async def instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "instagram"
    await update.message.reply_text("📸 اینستاگرام:\n\nhttps://instagram.com/ali_chavoshi.official", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def telegram_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "telegram"
    await update.message.reply_text("📢 کانال تلگرام:\n\nhttps://t.me/Alichavoshiaccounting", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def rubika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "rubika"
    await update.message.reply_text("🟠 کانال روبیکا:\n\nhttps://rubika.ir/Alichavoshiaccounting", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def educational_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "educational_videos"
    keyboard = [["📗 ویدئوهای آموزشی مقدماتی اکسل"],["📘 ویدئوهای آموزشی نیمه پیشرفته اکسل"],["🏠 منوی اصلی"]]
    await update.message.reply_text("🎬 ویدئوهای آموزشی\n\nسطح آموزشی مورد نظر خود را انتخاب کنید:", reply_markup=create_keyboard(keyboard))


async def excel_beginner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "excel_beginner"
    await update.message.reply_text("📗 ویدئوهای آموزشی مقدماتی اکسل\n\nبرای دریافت لینک دانلود ویدئوهای آموزشی، گزینه زیر را انتخاب کنید:", reply_markup=create_keyboard([["📥 لینک‌های دانلود دوره"],["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def excel_beginner_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "excel_beginner_download"
    await update.message.reply_text("📥 لینک دانلود ویدئوهای آموزشی مقدماتی اکسل:\n\nhttps://my.uupload.ir/d/pVZXk", reply_markup=create_keyboard([["🔙 بازگشت", "🏠 منوی اصلی"]]))


async def excel_intermediate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "excel_intermediate"
    await update.message.reply_text("📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\nبرای مشاهده قسمت‌های دوره، گزینه زیر را انتخاب کنید:", reply_markup=create_keyboard([["📥 لینک‌های دانلود دوره"],["🔙 بازگشت", "🏠 منوی اصلی"]]))


INTERMEDIATE_LESSONS = [
    ("۱. Concatenate", "https://my.uupload.ir/p/0jka5XvR"),
    ("۲. TEXTJOIN", "https://my.uupload.ir/p/2KDmGQDB"),
    ("۳. IF + TEXTJOIN", "https://my.uupload.ir/p/n2JGpEwK"),
    ("۴. AND + IF", "https://my.uupload.ir/p/BvxABejW"),
    ("۵. OR + IF", "https://my.uupload.ir/p/JgwO5yWN"),
    ("۶. XLOOKUP", "https://my.uupload.ir/p/ODwN9w42"),
    ("۷. SUMIFS", "https://my.uupload.ir/p/1LdxaM00"),
    ("۸. VLOOKUP / XLOOKUP", "https://my.uupload.ir/p/aG5a79xw"),
    ("۹. HLOOKUP / XLOOKUP", "https://my.uupload.ir/p/eyJLaKYX"),
]


async def excel_intermediate_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu_level"] = "excel_intermediate_download"
    inline_keyboard = [[InlineKeyboardButton(text=title, url=url)] for title, url in INTERMEDIATE_LESSONS]
    await update.message.reply_text("📘 ویدئوهای آموزشی نیمه پیشرفته اکسل\n\nبرای مشاهده هر قسمت، موضوع مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(inline_keyboard))


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


async def download_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data.get("menu_level")
    if level == "excel_beginner":
        await excel_beginner_download(update, context)
    elif level == "excel_intermediate":
        await excel_intermediate_download(update, context)


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
    "🤖 دستیار هوش مصنوعی","🎓 دوره‌های آموزشی","🎬 ویدئوهای آموزشی","📱 ارتباط با ما",
    "🏫 دوره‌های آموزشی حضوری","💻 دوره‌های آموزشی آنلاین","📊 دوره آموزش پاور کوئری","📑 دوره سامانه مودیان",
    "📊 مشاهده و ثبت‌نام دوره","📸 اینستاگرام","📢 کانال تلگرام","🟠 کانال روبیکا",
    "📗 ویدئوهای آموزشی مقدماتی اکسل","📘 ویدئوهای آموزشی نیمه پیشرفته اکسل","📥 لینک‌های دانلود دوره",
    "🔙 بازگشت","🏠 منوی اصلی",
]

app.add_handler(MessageHandler(filters.PHOTO, ask_ai_image))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Text(MENU_BUTTONS), ask_ai))

if not URL:
    raise ValueError("RENDER_EXTERNAL_URL در Environment Variables تنظیم نشده است.")

app.run_webhook(listen="0.0.0.0", port=PORT, url_path="telegram", webhook_url=f"{URL}/telegram")
