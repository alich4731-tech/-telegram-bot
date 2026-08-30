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

# مدلی که برای استخراج و ساخت سؤال استفاده می‌شود (می‌توانید همان
# AI_MODEL اصلی ربات یا مدل ارزان‌تر را از Environment ست کنید)
JOB_AI_MODEL = os.getenv("JOB_AI_MODEL", "gpt-4o-mini")

# چند آگهی از هر سایت به‌ازای هر عنوان شغلی بررسی شود
MAX_LISTINGS_PER_SITE_PER_ROLE = int(
    os.getenv("JOB_MAX_LISTINGS_PER_SITE", "6")
)

TOTAL_QUESTIONS_TARGET = 100
QUIZ_QUESTION_COUNT = 20
MAX_QUESTIONS_PER_TOPIC_IN_QUIZ = 4
PASS_THRESHOLD = 0.8  # ۸۰ درصد

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
  "topics": ["موضوع۱", "موضوع۲"],
  "requirements": ["الزام یا مهارت خواسته‌شده ۱", "الزام یا مهارت خواسته‌شده ۲"]
}}

اگر صفحه آگهی استخدام حسابداری/مالی مرتبط نیست، فقط
{{"is_job_ad": false}}
برگردان.

متن صفحه:
\"\"\"{page_text}\"\"\"
"""


def _call_openai_json(client, prompt, max_tokens=1200):
    try:
        resp = client.responses.create(
            model=JOB_AI_MODEL,
            input=[{"role": "user", "content": prompt}],
            max_output_tokens=max_tokens,
        )
        text = (getattr(resp, "output_text", None) or "").strip()
        text = re.sub(r"^```json", "", text.strip())
        text = re.sub(r"^```", "", text.strip())
        text = re.sub(r"```$", "", text.strip())
        return json.loads(text)
    except Exception as e:
        print(f"JOB AI JSON CALL ERROR [{type(e).__name__}]: {e}")
        return None


def _extract_requirements_from_page(client, page_text, source_url):
    if not page_text or len(page_text) < 80:
        return None

    prompt = EXTRACT_PROMPT.format(page_text=page_text[:4000])
    data = _call_openai_json(client, prompt, max_tokens=800)

    if not data or not isinstance(data, dict):
        return None

    if not data.get("is_job_ad"):
        return None

    requirements = data.get("requirements") or []
    topics = data.get("topics") or []

    if not requirements:
        return None

    return {
        "job_title": data.get("job_title", ""),
        "topics": topics,
        "requirements": requirements,
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

QUESTION_GEN_PROMPT = """
فهرست زیر، الزامات و مهارت‌های واقعی است که از آگهی‌های استخدام واقعی
برای مشاغل حسابدار، حسابدار ارشد، مدیر مالی، رئیس حسابداری و حسابرس در
ایران استخراج شده است (هر خط با موضوع آن مشخص شده):

{requirements_block}

بر اساس فقط و فقط همین فهرست (بدون حدس یا افزودن مطلبی که در فهرست
نیست)، دقیقا {count} سؤال چهارگزینه‌ای حسابداری/مالی/مالیاتی/تامین
اجتماعی/اکسل بساز که هرکدام سطح تسلط داوطلب بر یکی از الزامات فهرست
بالا را بسنجد.

خروجی را فقط به‌صورت یک آرایه JSON با این ساختار دقیق برگردان و هیچ
توضیح اضافه‌ای ننویس:

[
  {{
    "topic": "موضوع کوتاه (مثلا ارزش افزوده، حقوق و دستمزد، اکسل و ...)",
    "question": "متن سؤال",
    "options": ["گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"],
    "correct_index": 0
  }}
]

قوانین مهم:
- سؤال‌ها باید از موضوعات مختلف فهرست بالا باشند، نه فقط یک موضوع.
- هیچ سؤالی درباره شماره ماده قانونی یا مبلغ دقیق نساز مگر این‌که آن
  عدد یا شماره دقیقا در فهرست بالا آمده باشد.
- correct_index باید عددی بین ۰ تا ۳ باشد.
"""


def generate_question_bank(client, extracted_postings, log=print):

    if not extracted_postings:
        log("JOB: no extracted postings, cannot generate questions")
        return []

    lines = []

    for posting in extracted_postings:
        topics = "، ".join(posting.get("topics") or ["عمومی"])
        for req in posting.get("requirements", []):
            lines.append(f"- [{topics}] {req}")

    # حذف موارد تکراری با حفظ ترتیب
    seen = set()
    unique_lines = []
    for line in lines:
        key = line.strip().lower()
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)

    unique_lines = unique_lines[:350]  # کنترل حجم توکن

    requirements_block = "\n".join(unique_lines)

    all_questions = []
    batch_size = 25
    remaining = TOTAL_QUESTIONS_TARGET

    while remaining > 0:

        this_batch = min(batch_size, remaining)

        prompt = QUESTION_GEN_PROMPT.format(
            requirements_block=requirements_block,
            count=this_batch,
        )

        data = _call_openai_json(client, prompt, max_tokens=4000)

        if isinstance(data, list):

            for item in data:

                try:
                    options = item.get("options")
                    correct_index = int(item.get("correct_index"))

                    if (
                        not isinstance(options, list)
                        or len(options) != 4
                        or not (0 <= correct_index <= 3)
                        or not item.get("question")
                        or not item.get("topic")
                    ):
                        continue

                    all_questions.append(
                        {
                            "id": f"q{len(all_questions) + 1}",
                            "topic": item["topic"].strip(),
                            "question": item["question"].strip(),
                            "options": [
                                str(o).strip() for o in options
                            ],
                            "correct_index": correct_index,
                        }
                    )

                except Exception as e:
                    log(f"JOB: skipping malformed question: {e}")

        else:
            log("JOB: question batch generation failed, stopping batches")
            break

        remaining = TOTAL_QUESTIONS_TARGET - len(all_questions)

        if remaining <= 0:
            break

    log(f"JOB: generated {len(all_questions)} valid questions")

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

def refresh_job_bank(client, log=print):

    log("JOB: شروع به‌روزرسانی ماهانه بانک سؤال استخدام‌یاب")

    try:
        postings = collect_real_job_requirements(client, log=log)
        questions = generate_question_bank(client, postings, log=log)

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

def pick_quiz_questions(all_questions, total=QUIZ_QUESTION_COUNT):

    if not all_questions:
        return []

    by_topic = {}
    for q in all_questions:
        by_topic.setdefault(q["topic"], []).append(q)

    for topic in by_topic:
        random.shuffle(by_topic[topic])

    topics = list(by_topic.keys())
    random.shuffle(topics)

    selected = []
    topic_counts = {t: 0 for t in topics}

    # چرخشی از بین موضوعات مختلف انتخاب می‌کنیم تا سؤال‌ها
    # همه از یک مبحث نباشند
    changed = True
    while len(selected) < total and changed:
        changed = False
        for topic in topics:
            if len(selected) >= total:
                break
            if topic_counts[topic] >= MAX_QUESTIONS_PER_TOPIC_IN_QUIZ:
                continue
            pool = by_topic[topic]
            if not pool:
                continue
            selected.append(pool.pop())
            topic_counts[topic] += 1
            changed = True

    random.shuffle(selected)
    return selected[:total]


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
