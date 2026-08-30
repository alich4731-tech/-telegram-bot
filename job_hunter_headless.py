import os


# =========================================================
# پشتیبانی اختیاری از مرورگر Headless (Playwright)
# =========================================================
#
# چرا این فایل جدا است؟
# سایت‌هایی مثل دیوار، جاب‌ویژن، کاربوم و ایران‌تلنت اغلب
# اپلیکیشن‌های جاوااسکریپتی (SPA) هستند؛ یک درخواست ساده HTTP
# فقط یک "پوسته" خالی HTML برمی‌گرداند و محتوای واقعی بعدا با
# جاوااسکریپت در مرورگر ساخته می‌شود. برای خواندن محتوای واقعی
# این سایت‌ها، باید صفحه را در یک مرورگر واقعی (بدون رابط
# گرافیکی) باز کرد تا جاوااسکریپتش اجرا شود؛ این کار را کتابخانه
# رایگان Playwright انجام می‌دهد.
#
# نکته بسیار مهم دربارهٔ هزینه و منابع:
# Playwright به خودی خود رایگان است، اما اجرای مرورگر Chromium
# معمولا به ۳۰۰ تا ۵۰۰ مگابایت RAM نیاز دارد. پلن رایگان Render
# معمولا ۵۱۲ مگابایت RAM کل دارد، بنابراین اجرای هم‌زمان ربات
# تلگرام و یک Chromium ممکن است باعث کرش یا کندی شدید سرویس
# شود. به همین دلیل:
#   • این قابلیت به‌صورت پیش‌فرض خاموش است.
#   • فقط با ست‌کردن JOB_USE_HEADLESS=true در Environment Variables
#     فعال می‌شود.
#   • اگر پکیج playwright نصب نباشد یا فعال نشده باشد، کد بدون
#     خطا فقط از حالت مرورگر واقعی صرف‌نظر می‌کند و همان اسکرپ
#     ساده HTTP ادامه پیدا می‌کند (چیزی خراب نمی‌شود).
#
# اگر خواستید این حالت را فعال کنید:
#   1. در requirements.txt خط "playwright" را اضافه کنید.
#   2. در مرحله build روی Render، دستور زیر را هم اجرا کنید
#      (مثلا در Build Command):
#         pip install -r requirements.txt && playwright install --with-deps chromium
#   3. پیشنهاد می‌شود پلن سرویس را حداقل به یک پلن با RAM بیشتر
#      از پلن رایگان ارتقا دهید، وگرنه احتمال کرش سرویس هست.
#   4. JOB_USE_HEADLESS=true را در Environment Variables ست کنید.
# =========================================================

JOB_USE_HEADLESS = (
    os.getenv("JOB_USE_HEADLESS", "false").strip().lower() == "true"
)

_HEADLESS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def headless_enabled():
    """
    بررسی می‌کند که آیا حالت مرورگر واقعی فعال و قابل استفاده است.
    """

    if not JOB_USE_HEADLESS:
        return False

    try:
        import playwright  # noqa: F401
        return True

    except ImportError:
        print(
            "JOB HEADLESS: JOB_USE_HEADLESS=true است اما پکیج "
            "playwright نصب نیست؛ این حالت نادیده گرفته می‌شود. "
            "برای فعال‌سازی، «playwright» را به requirements.txt "
            "اضافه و «playwright install --with-deps chromium» را "
            "در مرحله build اجرا کنید."
        )
        return False


class HeadlessSession:
    """
    یک نشست مرورگر headless که فقط یک‌بار در طول کل فرآیند
    به‌روزرسانی بانک سؤال باز می‌شود و برای چند URL استفاده
    می‌شود (به‌جای باز و بستن مرورگر برای هر لینک که هم کند است
    و هم پرمصرف).

    استفاده:
        with HeadlessSession() as session:
            if session.available:
                html_content = session.fetch(url)
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._available = headless_enabled()

    def __enter__(self):

        if not self._available:
            return self

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()

            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

        except Exception as e:
            print(f"JOB HEADLESS: راه‌اندازی مرورگر ناموفق بود: {e}")
            self._available = False
            self._browser = None
            self._playwright = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass

        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

    @property
    def available(self):
        return self._available and self._browser is not None

    def fetch(self, url, wait_ms=2500, timeout_ms=25000):
        """
        صفحه را در مرورگر واقعی باز می‌کند، کمی صبر می‌کند تا
        جاوااسکریپت محتوا را بسازد، و HTML نهایی رندرشده را
        برمی‌گرداند. در صورت هر خطایی None برمی‌گرداند تا فراخوان
        بتواند بدون توقف کل فرآیند، ادامه دهد.
        """

        if not self.available:
            return None

        page = None

        try:
            page = self._browser.new_page(user_agent=_HEADLESS_UA)
            page.goto(
                url,
                timeout=timeout_ms,
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(wait_ms)
            return page.content()

        except Exception as e:
            print(f"JOB HEADLESS FETCH ERROR: {url} -> {e}")
            return None

        finally:
            try:
                if page:
                    page.close()
            except Exception:
                pass
