import os
import re
import json
import random
import time
import traceback
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import job_hunter_headless


# =========================================================
# تنظیمات کلی ماژول استخدام‌یاب هوشمند
# =========================================================
#
# نکته مهم (بخوانید):
# ۱. اسکرپ کردن سایت‌های کاریابی رایگان است، اما بعضی از آن‌ها
#    (مثل دیوار، جاب‌ویژن، کاربوم، ایران‌تلنت) اپلیکیشن‌های
#    جاوااسکریپتی (SPA) هستند و ممکن است با یک درخواست ساده
#    HTTP محتوای کامل را برنگردانند. کد زیر برای هر سایت تلاش
#    می‌کند و اگر سایتی چیزی برنگرداند، بدون توقف کل فرآیند،
#    از آن سایت رد می‌شود. با گذشت زمان ممکن است لازم باشد
#    آدرس‌های جستجو (SITE_SEARCH_BUILDERS) را به‌روزرسانی کنید.
# ۲. تنها هزینه واقعی این بخش، مصرف توکن OpenAI برای «استخراج
#    الزامات از متن آگهی» و «ساخت ۱۰۰ سؤال» است که ماهی یک‌بار
#    انجام می‌شود و هزینه‌ای بسیار کم روی همان حساب OpenAI فعلی
#    شماست. خودِ اسکرپ کردن هیچ هزینه‌ای ندارد.
# ۳. ذخیره‌سازی روی دیسک محلی است. در Render Free، دیسک بین
#    ری‌استارت‌ها/دیپلوی‌های جدید پاک می‌شود؛ پس بعد از هر دیپلوی
#    تازه، یک‌بار دستور /refresh_jobs را دستی بزنید تا بانک سؤال
#    دوباره ساخته شود.
# =========================================================

JOB_DATA_DIR = os.getenv("JOB_DATA_DIR", "job_data")
QUESTIONS_FILE = os.path.join(JOB_DATA_DIR, "job_questions.json")
META_FILE = os.path.join(JOB_DATA_DIR, "job_meta.json")

os.makedirs(JOB_DATA_DIR, exist_ok=True)

# مدلی که فقط برای «استخراج الزامات از متن آگهی» استفاده می‌شود؛
# این مرحله نیاز به جست‌وجوی وب ندارد (فقط همان متن صفحه را
# می‌خواند)، پس یک مدل ارزان کافی است.
JOB_AI_MODEL = os.getenv("JOB_AI_MODEL", "gpt-4o-mini")

# مدلی که برای «ساخت خودِ سؤال‌های تخصصی» استفاده می‌شود. اگر ست
# نشده باشد، مدلی که bot.py صدا می‌زند (معمولاً همان AI_MODEL
# اصلی ربات) استفاده می‌شود که دقیق‌تر ولی گران‌تر است. اگر
# می‌خواهید هزینه این مرحله را کم کنید، این را روی یک مدل ارزان‌تر
# (مثلاً gpt-4o-mini) بگذارید — کیفیت مفهومی سؤال‌ها معمولاً باز هم
# خوب می‌ماند، فقط ممکن است سؤال‌های عددی/نرخ‌محور کمتر ساخته شوند
# چون آن مدل‌ها همیشه از وب‌سرچ پشتیبانی نمی‌کنند.
JOB_QUESTION_MODEL_OVERRIDE = os.getenv("JOB_QUESTION_MODEL", "").strip()

# اگر می‌خواهید هزینه ساخت سؤال را بیشتر کم کنید، وب‌سرچ (که برای
# تایید نرخ‌ها/ارقام قانونی استفاده می‌شود) را با
# JOB_QUESTION_USE_WEB_SEARCH=false خاموش کنید. در این حالت مدل
# طبق دستور پرامپت، به‌جای حدس‌زدن عدد، فقط سؤال مفهومی/رویه‌ای
# می‌سازد (باز هم عدد اشتباه حدس زده نمی‌شود، فقط سؤال عددی کمتری
# خواهید داشت).
JOB_QUESTION_USE_WEB_SEARCH = (
    os.getenv("JOB_QUESTION_USE_WEB_SEARCH", "true").strip().lower() == "true"
)

# چند آگهی از هر سایت به‌ازای هر عنوان شغلی بررسی شود
MAX_LISTINGS_PER_SITE_PER_ROLE = int(
    os.getenv("JOB_MAX_LISTINGS_PER_SITE", "6")
)

# تعداد سؤال ساخته‌شده برای مبحث‌هایی که در آگهی‌های زیادی دیده
# شده‌اند (پرتقاضا) در برابر مبحث‌هایی که کم‌تر دیده شده‌اند.
QUESTIONS_PER_TOPIC_HIGH = 16
QUESTIONS_PER_TOPIC_LOW = 10
HIGH_FREQUENCY_THRESHOLD = 3  # مبحث در حداقل ۳ آگهی جدا دیده شده باشد

# حتی اگر مبحثی این ماه در هیچ آگهی واقعی دیده نشود (مثلاً چون
# اسکرپ آن ماه ضعیف بوده یا کارفرمایان آن حوزه کمتر آگهی داده‌اند)،
# چون می‌دانیم آن مبحث برای طیف کامل مشاغل حسابداری (از کمک‌حسابدار
# تا مدیر مالی) واقعاً لازم است، همچنان این تعداد سؤال حداقلی برایش
# ساخته می‌شود تا پوشش سطوح مختلف همیشه حفظ شود.
QUESTIONS_PER_TOPIC_BASELINE = 8

# به‌جای پخش کم‌عمق سؤال روی همه ۱۸ موضوع (که نمره هر موضوع را
# آماری ضعیف می‌کند)، هر آزمون فقط روی یک زیرمجموعه تصادفی از
# موضوعات متمرکز می‌شود، اما از هر موضوع انتخاب‌شده عمیق‌تر سؤال
# می‌پرسد؛ با ۵ سؤال از هر موضوع، رسیدن به آستانه ۸۰٪ یعنی دقیقاً
# ۴ پاسخ درست از ۵ — یک معیار روشن و معنادار. چون این انتخاب فقط
# از بین سؤال‌های از‌قبل‌ساخته‌شده در بانک است (نه فراخوانی جدید
# هوش مصنوعی)، این افزایش عمق هیچ هزینه اضافه‌ای در لحظه آزمون
# ندارد.
TOPICS_PER_QUIZ = 10
MAX_QUESTIONS_PER_TOPIC_IN_QUIZ = 5
PASS_THRESHOLD = 0.8  # ۸۰ درصد

# =========================================================
# فهرست ثابت مبحث‌های واقعاً فنیِ حسابداری/مالی/مالیاتی که قابل
# آزمون‌گرفتن هستند، دسته‌بندی‌شده بر اساس سطح شغلی که معمولاً آن
# مبحث در آگهی‌هایش خواسته می‌شود (کمک‌حسابدار → حسابدار →
# حسابدار ارشد/رئیس حسابداری → مدیر مالی). این دسته‌بندی فقط برای
# مستندسازی و اطمینان از پوشش کامل طیف مشاغل است؛ مرحله استخراج
# فقط اجازه دارد از میان همین مبحث‌ها انتخاب کند (نه هر عبارت آزاد
# دیگری)، تا مبحث‌های بی‌ربط یا غیرقابل‌آزمون مثل «سابقه کار» یا
# «روحیه کار تیمی» وارد بانک سؤال نشوند. اگر خواستید، می‌توانید
# این فهرست را ویرایش یا تکمیل کنید.
# =========================================================

CANONICAL_TOPICS_BY_LEVEL = {
    "کمک‌حسابدار / سطح مقدماتی": [
        "اسناد و ثبت‌های حسابداری روزانه",
        "اکسل و Power Query در حسابداری",
        "نرم‌افزارهای حسابداری (مانند هلو، سپیدار، همکاران سیستم)",
        "مغایرت‌گیری بانکی",
    ],
    "حسابدار": [
        "ارزش افزوده و سامانه مؤدیان",
        "حقوق و دستمزد و مزایای کارکنان",
        "بیمه تأمین اجتماعی",
        "قانون کار",
        "تراز آزمایشی و بستن حساب‌ها",
        "دارایی ثابت و استهلاک",
    ],
    "حسابدار ارشد / رئیس حسابداری": [
        "مالیات عملکرد و اظهارنامه مالیاتی",
        "استانداردهای حسابداری ایران",
        "حسابداری صنعتی و بهای تمام‌شده",
        "تهیه صورت‌های مالی",
        "حسابرسی",
    ],
    "مدیر مالی": [
        "خزانه‌داری و مدیریت نقدینگی",
        "بودجه‌بندی و گزارش‌های مدیریتی",
        "قراردادها و امور حقوقی مالی",
        "تحلیل صورت‌های مالی و نسبت‌های مالی",
        "مدیریت ریسک مالی و اعتباری",
    ],
}

# فهرست تخت (بدون سطح‌بندی) که بقیه کد از آن استفاده می‌کند، به‌علاوه
# نگاشت هر مبحث به سطح شغلی‌اش (برای لاگ و بررسی پوشش).
CANONICAL_TOPICS = [
    topic
    for topics_in_level in CANONICAL_TOPICS_BY_LEVEL.values()
    for topic in topics_in_level
]

TOPIC_LEVEL_MAP = {
    topic: level
    for level, topics_in_level in CANONICAL_TOPICS_BY_LEVEL.items()
    for topic in topics_in_level
}

ROLE_KEYWORDS = [
    "حسابدار",
    "حسابدار ارشد",
    "مدیر مالی",
    "رئیس حسابداری",
    "حسابرس",
    "کارشناس مالی",
]

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.5",
}

# =========================================================
# آدرس جستجو در هر سایت (best effort - ممکن است نیاز به تنظیم
# دوره‌ای داشته باشد چون ساختار سایت‌ها تغییر می‌کند)
# =========================================================

def _q(text):
    return quote(text)


SITE_SEARCH_BUILDERS = {
    "jobinja": lambda kw: (
        "https://jobinja.ir/jobs?filters%5Bkeywords%5D%5B0%5D=" + _q(kw)
    ),
    "e-estekhdam": lambda kw: (
        "https://www.e-estekhdam.com/search/" + _q("استخدام-" + kw)
    ),
    "iranestekhdam": lambda kw: (
        "https://iranestekhdam.ir/search/?q=" + _q(kw)
    ),
    "jobvision": lambda kw: (
        "https://jobvision.ir/jobs/keyword/" + _q(kw)
    ),
    "karboom": lambda kw: "https://karboom.io/jobs/accounting-auditing",
    "kardix": lambda kw: "https://kardix.com/jobs?q=" + _q(kw),
    "irantalent": lambda kw: (
        "https://www.irantalent.com/jobs?keyword=" + _q(kw)
    ),
    # دیوار یک اپلیکیشن کاملا جاوااسکریپتی است و معمولا با
    # درخواست ساده HTTP چیزی برنمی‌گرداند؛ به همین دلیل با
    # اولویت پایین نگه داشته شده و اگر نتیجه‌ای نداد نادیده
    # گرفته می‌شود.
    "divar": lambda kw: "https://divar.ir/s/iran/jobs?q=" + _q(kw),
}

JOB_LINK_HINTS = [
    "job", "jobs", "career", "careers", "vacancy", "position",
    "استخدام", "فرصت", "شغل", "/p/", "/companies/",
]

# سایت‌هایی که معمولا اپلیکیشن جاوااسکریپتی (SPA) هستند و با
# درخواست ساده HTTP ممکن است فقط یک پوسته خالی برگردانند. برای
# این سایت‌ها، اگر مرورگر headless فعال باشد (JOB_USE_HEADLESS=true)
# به‌عنوان راه دوم تلاش می‌شود.
HEADLESS_CANDIDATE_SITES = {"divar", "jobvision", "karboom", "irantalent"}

# اگر متن قابل‌استخراج از یک صفحه کمتر از این مقدار باشد، به
# احتمال زیاد یک پوسته خالی SPA است نه محتوای واقعی.
JS_SHELL_TEXT_LENGTH_THRESHOLD = 400


def _normalize_fa(text):
    if not text:
        return ""
    replacements = {
        "ي": "ی", "ى": "ی", "ك": "ک", "أ": "ا", "إ": "ا",
        "آ": "ا", "ة": "ه", "ؤ": "و", "ئ": "ی", "ۀ": "ه",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_city_name(name):
    """
    برای مقایسه دو نام شهر (مثلا شهری که کاربر تایپ کرده با شهری
    که از آگهی استخراج شده)، فاصله و نیم‌فاصله و حروف عربی/فارسی
    را یکسان می‌کند. توجه: غلط‌های املایی را تشخیص نمی‌دهد.
    """
    if not name:
        return ""
    text = _normalize_fa(name)
    text = text.replace("\u200c", "").replace(" ", "")
    return text.strip()


# فهرست شهرهای بزرگ و مراکز استان ایران، برای تشخیص شهر آگهی از
# روی متن اطراف لینک آن. مرتب‌شده از طولانی به کوتاه تا نام‌های
# ترکیبی (مثل «شهر ری») زودتر از نام‌های کوتاه‌تر تشخیص داده شوند.
IRAN_CITIES = sorted(
    [
        "تهران", "مشهد", "اصفهان", "کرج", "شیراز", "تبریز", "قم",
        "اهواز", "کرمانشاه", "ارومیه", "رشت", "زاهدان", "همدان",
        "یزد", "اردبیل", "بندرعباس", "اراک", "کرمان", "قزوین",
        "زنجان", "سنندج", "خرم‌آباد", "خرم آباد", "گرگان", "ساری",
        "بجنورد", "بوشهر", "بیرجند", "ایلام", "شهرکرد", "یاسوج",
        "سمنان", "شهریار", "اسلامشهر", "پاکدشت", "ورامین",
        "نجف‌آباد", "خمینی‌شهر", "کاشان", "سبزوار", "نیشابور",
        "قائم‌شهر", "بابل", "آمل", "دزفول", "بروجرد", "خرمشهر",
        "آبادان", "ماهشهر", "نوشهر", "چالوس", "رامسر", "لاهیجان",
        "بندر انزلی", "انزلی", "میاندوآب", "مراغه", "خوی", "مرند",
        "سقز", "بانه", "مهاباد", "ایرانشهر", "چابهار", "جهرم",
        "کازرون", "مرودشت", "لار", "فسا", "نی‌ریز", "رفسنجان",
        "سیرجان", "جیرفت", "بم", "زابل", "شاهرود", "دامغان",
        "گناباد", "تربت حیدریه", "تربت جام", "قوچان", "کرج",
        "پرند", "ملارد", "رباط کریم", "قدس", "شهر ری", "ری",
        "پردیس", "دماوند", "فیروزکوه",
    ],
    key=len,
    reverse=True,
)


def _detect_city_in_text(text):
    """
    اگر یکی از نام‌های فهرست IRAN_CITIES داخل متن باشد، همان را
    برمی‌گرداند. برای شهرهایی که در فهرست نیستند، None برمی‌گرداند
    (این تشخیص کامل نیست، فقط برای شهرهای بزرگ و پرکاربرد است).
    """
    if not text:
        return None

    normalized = _normalize_fa(text)

    for city in IRAN_CITIES:
        if _normalize_fa(city) in normalized:
            return city

    return None


# =========================================================
# ابزارهای کمکی HTTP
# =========================================================

def _safe_get(url, timeout=15):
    try:
        resp = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return resp.text
        print(f"JOB SCRAPER: status={resp.status_code} for {url}")
    except Exception as e:
        print(f"JOB SCRAPER FETCH ERROR [{type(e).__name__}]: {url} -> {e}")
    return None


def _extract_text(html_content, limit=4000):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:limit]
    except Exception as e:
        print(f"JOB SCRAPER TEXT EXTRACTION ERROR: {e}")
        return ""


def _looks_like_js_shell(html_content):
    """
    تشخیص ابتدایی این‌که آیا HTML دریافت‌شده یک پوسته خالی SPA است
    (متن واقعی خیلی کم) یا محتوای واقعی صفحه.
    """

    if not html_content:
        return True

    text = _extract_text(html_content, limit=5000)

    return len(text) < JS_SHELL_TEXT_LENGTH_THRESHOLD


def _fetch_html_with_fallback(site_name, url, headless_session=None):
    """
    ابتدا با یک درخواست ساده و سریع HTTP تلاش می‌کند (رایگان و
    کم‌هزینه). اگر سایت جزو سایت‌های جاوااسکریپتی شناخته‌شده باشد
    و نتیجه شبیه یک پوسته خالی SPA باشد، و مرورگر headless در
    دسترس باشد، به‌عنوان راه دوم از مرورگر واقعی استفاده می‌کند.
    """

    html_content = _safe_get(url)

    needs_headless = (
        site_name in HEADLESS_CANDIDATE_SITES
        and _looks_like_js_shell(html_content)
        and headless_session is not None
        and headless_session.available
    )

    if needs_headless:

        rendered = headless_session.fetch(url)

        if rendered:
            print(f"JOB: از مرورگر headless برای {url} استفاده شد")
            return rendered

    return html_content


def _discover_candidate_links_with_context(html_content, base_url, limit=10):
    """
    مثل _discover_candidate_links اما به‌ازای هر لینک، کمی از متن
    اطراف آن (والدش در HTML) را هم برمی‌گرداند تا بشود از روی آن
    نام شهر آگهی را حدس زد (خیلی از سایت‌ها نام شهر را همان کنار
    عنوان آگهی می‌نویسند، مثلا «استخدام حسابدار (تبریز)»).
    """
    results = []
    seen = set()

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").strip()

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc and domain not in parsed.netloc:
                continue

            haystack = (full_url + " " + text).lower()

            if not any(hint in haystack for hint in JOB_LINK_HINTS):
                continue

            if full_url in seen:
                continue

            seen.add(full_url)

            context_text = text

            try:
                parent = a.find_parent(["li", "div", "article"])
                if parent:
                    parent_text = parent.get_text(separator=" ", strip=True)
                    if parent_text:
                        context_text = parent_text[:300]
            except Exception:
                pass

            results.append({"url": full_url, "context": context_text})

            if len(results) >= limit:
                break

    except Exception as e:
        print(f"JOB SCRAPER LINK DISCOVERY ERROR: {e}")

    return results


def _discover_candidate_links(html_content, base_url, limit=10):
    """
    نسخه ساده که فقط URLها را برمی‌گرداند (برای جاهایی که نیازی
    به متن اطراف لینک نیست).
    """
    return [
        item["url"]
        for item in _discover_candidate_links_with_context(
            html_content, base_url, limit
        )
    ]


# =========================================================
# استخراج الزامات آگهی با کمک هوش مصنوعی (بدون حدس، فقط از متن)
# =========================================================

EXTRACT_PROMPT = """
متن زیر محتوای یک صفحه وب است که ممکن است یک آگهی استخدام باشد.

اگر این صفحه واقعا یک آگهی استخدام برای یکی از این عناوین شغلی است:
حسابدار، حسابدار ارشد، مدیر مالی، رئیس حسابداری، حسابرس، کارشناس مالی

فقط بر اساس متن زیر (بدون حدس و بدون افزودن اطلاعات از خودت)، خروجی را
دقیقا به‌صورت یک JSON با این ساختار برگردان و هیچ متن اضافه‌ای قبل یا
بعد از JSON ننویس:

{{
  "is_job_ad": true یا false,
  "job_title": "عنوان شغلی آگهی",
  "technical_topics": ["مبحث۱", "مبحث۲"]
}}

برای technical_topics: فقط از میان مبحث‌های زیر انتخاب کن (دقیقاً همان
عبارت را کپی کن) و فقط مبحث‌هایی را بگذار که واقعاً در متن آگهی به‌عنوان
یکی از الزامات یا مهارت‌های مورد نیاز ذکر شده باشند:

{canonical_topics_list}

نکته مهم: مواردی مثل «سابقه کار»، «مدرک تحصیلی»، «روحیه کار تیمی»،
«مهارت ارتباطی»، «حقوق توافقی»، «فرصت رشد شغلی» یا هر چیز دیگری که در
فهرست بالا نیست را در technical_topics قرار نده، چون این‌ها مبحث دانش
فنی قابل‌آزمون نیستند.

اگر صفحه آگهی استخدام حسابداری/مالی مرتبط نیست، فقط
{{"is_job_ad": false}}
برگردان.

متن صفحه:
\"\"\"{page_text}\"\"\"
"""


def _extract_output_text_fallback(resp):
    """
    output_text گاهی خالی برمی‌گردد حتی اگر مدل چیزی تولید کرده
    باشد (مثلا وقتی پاسخ در میانه یک تکه متن قطع شده). این تابع
    به‌جای تکیه فقط بر output_text، مستقیم از داخل resp.output هم
    متن را جمع می‌کند.
    """
    collected = []
    try:
        for item in (getattr(resp, "output", []) or []):
            if getattr(item, "type", None) != "message":
                continue
            for content in (getattr(item, "content", []) or []):
                t = getattr(content, "text", None)
                if t:
                    collected.append(t)
    except Exception:
        pass
    return "".join(collected).strip()


def _call_openai_json(client, model, prompt, max_tokens=1200, use_search=False):

    try:

        args = {
            "model": model,
            "input": [{"role": "user", "content": prompt}],
            "max_output_tokens": max_tokens,
        }

        if use_search:
            args["tools"] = [
                {"type": "web_search", "search_context_size": "low"}
            ]

        resp = client.responses.create(**args)

        status = getattr(resp, "status", None)
        incomplete_details = getattr(resp, "incomplete_details", None)
        incomplete_reason = (
            getattr(incomplete_details, "reason", None)
            if incomplete_details else None
        )

        text = (getattr(resp, "output_text", None) or "").strip()

        if not text:
            text = _extract_output_text_fallback(resp)

        if status == "incomplete":
            print(
                f"JOB AI JSON WARNING: پاسخ ناقص برگشت "
                f"(reason={incomplete_reason}, "
                f"max_tokens={max_tokens}, "
                f"طول متن دریافتی={len(text)} کاراکتر). "
                "احتمالا سقف توکن این تماس کافی نبوده؛ اگر این پیام "
                "زیاد تکرار شد، max_tokens مربوطه را در کد بالا "
                "ببرید یا JOB_QUESTION_USE_WEB_SEARCH را false کنید."
            )

        if not text:
            print(
                "JOB AI JSON WARNING: هیچ متنی از مدل دریافت نشد "
                f"(status={status})."
            )
            return None

        cleaned = re.sub(r"^```json", "", text.strip())
        cleaned = re.sub(r"^```", "", cleaned.strip())
        cleaned = re.sub(r"```$", "", cleaned.strip())

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(
                f"JOB AI JSON PARSE ERROR: {e} | "
                f"ابتدای متن دریافتی: {cleaned[:300]!r}"
            )
            return None

    except Exception as e:
        print(f"JOB AI JSON CALL ERROR [{type(e).__name__}]: {e}")
        return None


_CANONICAL_TOPICS_PROMPT_BLOCK = "\n".join(
    f"- {t}" for t in CANONICAL_TOPICS
)


def _extract_requirements_from_page(client, page_text, source_url):

    if not page_text or len(page_text) < 80:
        return None

    prompt = EXTRACT_PROMPT.format(
        page_text=page_text[:4000],
        canonical_topics_list=_CANONICAL_TOPICS_PROMPT_BLOCK,
    )

    data = _call_openai_json(client, JOB_AI_MODEL, prompt, max_tokens=900)

    if not data or not isinstance(data, dict):
        return None

    if not data.get("is_job_ad"):
        return None

    raw_topics = data.get("technical_topics") or []

    # فیلتر ایمنی: فقط مبحث‌هایی که واقعاً در فهرست ثابت هستند قبول
    # می‌شوند؛ اگر مدل چیزی خارج از فهرست برگرداند، نادیده گرفته
    # می‌شود (نه اضافه).
    technical_topics = [t for t in raw_topics if t in CANONICAL_TOPICS]

    if not technical_topics:
        return None

    return {
        "job_title": data.get("job_title", ""),
        "technical_topics": technical_topics,
        "source_url": source_url,
    }


# =========================================================
# مرحله ۱: جمع‌آوری آگهی‌های واقعی از سایت‌های کاریابی
# =========================================================

def collect_real_job_requirements(client, log=print):
    """
    برای هر سایت و هر عنوان شغلی، صفحه جستجو را می‌گیرد، لینک‌های
    محتمل آگهی را پیدا می‌کند، هر آگهی را باز می‌کند و با کمک
    هوش مصنوعی الزامات واقعی آن را استخراج می‌کند.
    """

    all_extracted = []

    with job_hunter_headless.HeadlessSession() as headless_session:

        if job_hunter_headless.JOB_USE_HEADLESS:
            log(
                "JOB: حالت مرورگر headless "
                + ("فعال و آماده است" if headless_session.available
                   else "درخواست شده اما در دسترس نیست؛ فقط از HTTP ساده استفاده می‌شود")
            )

        for site_name, url_builder in SITE_SEARCH_BUILDERS.items():

            for role in ROLE_KEYWORDS:

                try:
                    search_url = url_builder(role)
                except Exception as e:
                    log(f"JOB: site url build error {site_name}/{role}: {e}")
                    continue

                search_html = _fetch_html_with_fallback(
                    site_name, search_url, headless_session
                )

                if not search_html:
                    log(f"JOB: no response from {site_name} for '{role}'")
                    continue

                links = _discover_candidate_links(
                    search_html,
                    search_url,
                    limit=MAX_LISTINGS_PER_SITE_PER_ROLE,
                )

                if not links:
                    log(f"JOB: no candidate links on {site_name} for '{role}'")
                    continue

                for link in links:

                    detail_html = _fetch_html_with_fallback(
                        site_name, link, headless_session
                    )

                    if not detail_html:
                        continue

                    page_text = _extract_text(detail_html)

                    extracted = _extract_requirements_from_page(
                        client, page_text, link
                    )

                    if extracted:
                        extracted["site"] = site_name
                        extracted["role_query"] = role
                        all_extracted.append(extracted)

                    # کمی مکث برای رعایت ادب در برابر سرورهای سایت‌ها
                    time.sleep(0.5)

    log(f"JOB: total extracted job postings = {len(all_extracted)}")

    return all_extracted


# =========================================================
# مرحله ۲: ساخت ۱۰۰ سؤال فقط بر اساس الزامات واقعی جمع‌آوری‌شده
# =========================================================

# =========================================================
# مرحله ۲: ساخت سؤال‌های تخصصی واقعی، به‌ازای هر مبحث
# =========================================================
#
# طراحی این مرحله عمداً فرق دارد با مرحله استخراج: مرحله استخراج
# فقط تعیین می‌کند «کدام مبحث‌ها واقعاً در آگهی‌های استخدام خواسته
# شده‌اند» (یعنی مبحث‌ها را از واقعیت بازار کار می‌گیریم). اما خودِ
# محتوای سؤال‌ها را از تخصص هوش مصنوعی در همان مبحث می‌سازیم، نه
# صرفاً از جمله‌های سطحی آگهی («۲ سال سابقه لازم است») — چون آن
# جمله‌ها عمق کافی برای طراحی سؤال تخصصی ندارند. برای هر رقم یا
# نرخ قانونی، از ابزار جست‌وجوی وب استفاده می‌شود تا رقم غلط یا
# قدیمی حدس زده نشود.
# =========================================================

TOPIC_QUESTION_PROMPT = """
تو داری برای داوطلبان مشاغل حسابدار، حسابدار ارشد، مدیر مالی، رئیس
حسابداری و حسابرس در ایران، یک بخش از آزمون تخصصی طراحی می‌کنی.

مبحث این بخش از آزمون: «{topic}»

این مبحث را کارفرمایان واقعی در آگهی‌های استخدام حسابداری در ایران
به‌عنوان یکی از الزامات یا مهارت‌های مورد نیاز ذکر کرده‌اند؛ یعنی تسلط
بر آن واقعاً برای گرفتن این مشاغل مفید است.

دقیقاً {count} سؤال چهارگزینه‌ای تخصصی و کاربردی در همین مبحث بساز که
سطح واقعی دانش حرفه‌ای داوطلب را بسنجد — نه سؤال کلی یا تعریف لغوی
(مثلا نپرس «فلان مبحث چیست»)، بلکه سؤالی که یک حسابدار حرفه‌ای واقعاً
باید بتواند جواب بدهد: محاسبه صحیح، تشخیص ثبت درست، رویه صحیح کار،
تشخیص خطا، یا اعمال درست یک قاعده/نرخ/قانون.

قانون بسیار مهم درباره اعداد، نرخ‌ها و احکام قانونی:
اگر سؤالی به یک رقم، نرخ، یا حکم قانونیِ به‌روز نیاز دارد (مثل نرخ
اضافه‌کاری، حق اولاد، حداقل دستمزد، سقف معافیت مالیاتی، نرخ حق بیمه)،
حتما قبل از نوشتن سؤال آن را با جست‌وجوی وب تایید کن. اگر نتوانستی با
اطمینان یک رقم دقیق و به‌روز را تایید کنی، به‌جای سؤال عددی، یک سؤال
مفهومی یا رویه‌ای در همان مبحث بساز (بدون ذکر رقم قطعی) — هرگز رقم یا
نرخ را حدس نزن.

خروجی را فقط به‌صورت یک آرایه JSON با این ساختار دقیق برگردان، بدون
هیچ توضیح اضافه قبل یا بعد از آن:

[
  {{
    "question": "متن سؤال",
    "options": ["گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"],
    "correct_index": 0
  }}
]

correct_index باید عددی بین ۰ تا ۳ باشد.
"""


def generate_question_bank(client, extracted_postings, question_model, log=print):
    """
    برای هر مبحث از CANONICAL_TOPICS (که کل طیف کمک‌حسابدار تا مدیر
    مالی را پوشش می‌دهد)، سؤال می‌سازد. مبحث‌هایی که این ماه واقعاً
    در آگهی‌های زیادی دیده شده‌اند، سؤال بیشتری می‌گیرند (چون بازار
    کار الان بیشتر آن‌ها را می‌خواهد)؛ اما حتی مبحثی که این ماه در
    هیچ آگهی واقعی دیده نشود، چون می‌دانیم برای پوشش کامل سطوح شغلی
    لازم است، همچنان یک تعداد سؤال حداقلی (QUESTIONS_PER_TOPIC_BASELINE)
    برایش ساخته می‌شود تا هیچ سطحی کاملاً از بانک سؤال حذف نشود.
    question_model باید مدلی باشد که از ابزار جست‌وجوی وب پشتیبانی
    می‌کند (همان مدل اصلی ربات، AI_MODEL، پیشنهاد می‌شود).
    """

    topic_counts = {t: 0 for t in CANONICAL_TOPICS}

    for posting in extracted_postings:
        for topic in posting.get("technical_topics", []):
            if topic in topic_counts:
                topic_counts[topic] += 1

    if not extracted_postings:
        log(
            "JOB: این دور هیچ آگهی واقعی استخراج نشد (مثلا اسکرپ "
            "همه سایت‌ها ناموفق بود)؛ بانک سؤال فقط با سطح حداقلی "
            "(QUESTIONS_PER_TOPIC_BASELINE) برای هر مبحث ساخته "
            "می‌شود تا حداقل پوشش سطوح حفظ شود."
        )

    # برخلاف نسخه قبلی، دیگر مبحث‌هایی که این ماه در هیچ آگهی دیده
    # نشده‌اند را از بانک حذف نمی‌کنیم — همه CANONICAL_TOPICS همیشه
    # فعال هستند، فقط تعداد سؤالشان بر اساس تقاضای واقعی فرق دارد.
    active_topics = CANONICAL_TOPICS

    log(
        "JOB: تعداد آگهی‌های واقعی که هر مبحث را خواسته‌اند: "
        + "، ".join(f"{t} ({topic_counts[t]})" for t in active_topics)
    )

    all_questions = []

    for topic in active_topics:

        freq = topic_counts[topic]

        if freq >= HIGH_FREQUENCY_THRESHOLD:
            count = QUESTIONS_PER_TOPIC_HIGH
        elif freq > 0:
            count = QUESTIONS_PER_TOPIC_LOW
        else:
            count = QUESTIONS_PER_TOPIC_BASELINE

        prompt = TOPIC_QUESTION_PROMPT.format(topic=topic, count=count)

        data = _call_openai_json(
            client,
            question_model,
            prompt,
            max_tokens=8000,
            use_search=JOB_QUESTION_USE_WEB_SEARCH,
        )

        if not isinstance(data, list):
            log(f"JOB: ساخت سؤال برای مبحث «{topic}» ناموفق بود")
            continue

        added = 0

        for item in data:

            try:
                options = item.get("options")
                correct_index = int(item.get("correct_index"))

                if (
                    not isinstance(options, list)
                    or len(options) != 4
                    or not (0 <= correct_index <= 3)
                    or not item.get("question")
                ):
                    continue

                all_questions.append(
                    {
                        "id": f"q{len(all_questions) + 1}",
                        "topic": topic,
                        "question": str(item["question"]).strip(),
                        "options": [str(o).strip() for o in options],
                        "correct_index": correct_index,
                    }
                )

                added += 1

            except Exception as e:
                log(f"JOB: skipping malformed question in '{topic}': {e}")

        log(f"JOB: مبحث «{topic}»: {added} سؤال معتبر ساخته شد")

    log(f"JOB: مجموع سؤال‌های ساخته‌شده = {len(all_questions)}")

    return all_questions


# =========================================================
# ذخیره / بارگذاری بانک سؤال
# =========================================================

def save_question_bank(questions):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": time.time(), "count": len(questions)},
            f,
            ensure_ascii=False,
        )


def load_question_bank():
    if not os.path.exists(QUESTIONS_FILE):
        return []

    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"JOB: error loading question bank: {e}")
        return []


def get_bank_meta():
    if not os.path.exists(META_FILE):
        return None

    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# =========================================================
# فرآیند کامل ماهانه (اسکرپ + ساخت سؤال + ذخیره)
# =========================================================

def refresh_job_bank(client, question_model=None, log=print):

    log("JOB: شروع به‌روزرسانی ماهانه بانک سؤال استخدام‌یاب")

    # اگر متغیر محیطی JOB_QUESTION_MODEL ست شده باشد، همیشه همان
    # اولویت دارد (یعنی صراحتاً خواسته‌اید مدل ارزان‌تری استفاده
    # شود، حتی اگر bot.py مدل اصلی و گران‌تر را پاس داده باشد).
    # در غیر این صورت، اگر مدل جداگانه‌ای داده نشده، از همان مدل
    # ارزان استخراج استفاده می‌شود؛ اما توجه: آن مدل ممکن است از
    # ابزار جست‌وجوی وب پشتیبانی نکند و سؤال‌های عددی/قانونی را
    # مفهومی بسازد. برای بهترین دقت (و بیشترین هزینه)، مدل اصلی
    # ربات (AI_MODEL) را از bot.py پاس بدهید.
    effective_model = (
        JOB_QUESTION_MODEL_OVERRIDE
        or question_model
        or JOB_AI_MODEL
    )

    try:
        postings = collect_real_job_requirements(client, log=log)
        questions = generate_question_bank(
            client, postings, effective_model, log=log
        )

        if questions:
            save_question_bank(questions)
            log(f"JOB: بانک سؤال با {len(questions)} سؤال ذخیره شد")
        else:
            log("JOB: هیچ سؤالی تولید نشد؛ بانک قبلی حفظ می‌شود")

        return len(questions)

    except Exception:
        log("JOB: خطای غیرمنتظره در refresh_job_bank:")
        log(traceback.format_exc())
        return 0


# =========================================================
# انتخاب تصادفی و متنوع ۲۰ سؤال از بانک برای یک آزمون
# =========================================================

def pick_quiz_questions(
    all_questions,
    topics_per_quiz=TOPICS_PER_QUIZ,
    max_per_topic=MAX_QUESTIONS_PER_TOPIC_IN_QUIZ,
):
    """
    به‌جای پخش کم‌عمق روی همه موضوعات، ابتدا یک زیرمجموعه تصادفی از
    موضوعات (به تعداد topics_per_quiz) انتخاب می‌شود، سپس از هر
    موضوع انتخاب‌شده حداکثر max_per_topic سؤال (به تصادف، از بین
    سؤال‌های موجود همان موضوع در بانک) برداشته می‌شود. اگر موضوعات
    بانک کمتر از topics_per_quiz باشند، همه موضوعات موجود انتخاب
    می‌شوند.
    """

    if not all_questions:
        return []

    by_topic = {}
    for q in all_questions:
        by_topic.setdefault(q["topic"], []).append(q)

    topics = list(by_topic.keys())
    random.shuffle(topics)

    selected_topics = topics[:topics_per_quiz]

    selected = []

    for topic in selected_topics:

        pool = by_topic[topic][:]
        random.shuffle(pool)

        selected.extend(pool[:max_per_topic])

    random.shuffle(selected)
    return selected


# =========================================================
# جست‌وجوی زنده آگهی متناسب با توانایی کاربر (بدون فراخوانی AI)
# =========================================================

def find_live_jobs_grouped_by_city(topics, per_topic_limit=6, log=print):
    """
    برای موضوعاتی که کاربر در آن‌ها موفق بوده، به‌صورت زنده در
    چند سایت اصلی جست‌وجو می‌کند، برای هر آگهی پیدا‌شده تلاش
    می‌کند نام شهر آن را از روی متن اطراف لینک تشخیص دهد، و در
    نهایت یک لیست از آگهی‌ها را برمی‌گرداند که هرکدام شامل
    {url, city, topic} است. این تابع هیچ فراخوانی هوش مصنوعی
    ندارد و هزینه‌ای ندارد؛ فقط از HTTP ساده (و در صورت فعال بودن،
    مرورگر headless) استفاده می‌کند.

    گروه‌بندی بر اساس شهر خود این تابع را انجام نمی‌دهد؛ از تابع
    group_pool_by_city برای آن استفاده کنید.
    """

    quick_sites = [
        "jobinja", "e-estekhdam", "iranestekhdam",
        "divar", "jobvision", "karboom", "irantalent",
    ]

    pool = []
    seen_urls = set()

    with job_hunter_headless.HeadlessSession() as headless_session:

        for topic in topics:

            count_for_topic = 0

            for site_name in quick_sites:

                if count_for_topic >= per_topic_limit:
                    break

                builder = SITE_SEARCH_BUILDERS.get(site_name)
                if not builder:
                    continue

                try:
                    search_url = builder(topic)
                except Exception:
                    continue

                html_content = _fetch_html_with_fallback(
                    site_name, search_url, headless_session
                )

                if not html_content:
                    continue

                candidates = _discover_candidate_links_with_context(
                    html_content, search_url, limit=per_topic_limit
                )

                for item in candidates:

                    url = item["url"]

                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    city = _detect_city_in_text(item["context"]) or "سایر شهرها"

                    pool.append(
                        {"url": url, "city": city, "topic": topic}
                    )

                    count_for_topic += 1

                    if count_for_topic >= per_topic_limit:
                        break

    log(f"JOB: live search found {len(pool)} postings across {len(topics)} topics")

    return pool


def group_pool_by_city(pool):
    """
    فهرست تخت آگهی‌ها را به دیکشنری {نام شهر: [آگهی‌ها]} تبدیل
    می‌کند تا بشود اول شهر خود کاربر و بعد سایر شهرها را نشان داد.
    """

    by_city = {}

    for item in pool:
        by_city.setdefault(item["city"], []).append(item)

    return by_city
