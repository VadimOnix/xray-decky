# Xray Decky — کلاینت VPN و پروکسی برای Steam Deck

[English](README.md) · [Русский](README.ru.md) · [中文](README.zh-CN.md) · **فارسی** · [Español](README.es.md)

![Xray Decky — کلاینت VPN و پروکسی برای Steam Deck](site/public/assets/hero-banner-800w.png)

یک VPN روی Steam Deck خود اجرا کنید — حتی در حالت گیمینگ (Gaming Mode).
Xray Decky یک افزونه برای [Decky Loader](https://wiki.deckbrew.xyz/) است: یک
کلاینت پروکسی کامل (VLESS/VMess/Trojan/Shadowsocks/SOCKS5/Hysteria2/TUIC) که حالت
TUN آن **تمام** ترافیک سیستم را از طریق یک تونل رمزنگاری‌شده مسیریابی
می‌کند — پوششی در سطح کل سیستم و به سبک VPN که بازی‌ها هم نمی‌توانند
نادیده‌اش بگیرند. اشتراک چند سروری، پنل مدیریت وب با ظاهر Steam، کیل سوییچ
(kill switch) و آمار زنده ترافیک نیز در آن گنجانده شده است.

## امکانات

- **پوشش گسترده پروتکل‌ها و ترنسپورت‌ها** — وارد کردن **VLESS**
  (REALITY / XTLS-Vision)، **VMess**، **Trojan** و **Shadowsocks** (شامل
  رمزهای 2022) روی RAW/TCP، WebSocket، gRPC، HTTPUpgrade، XHTTP و mKCP،
  همراه با مجموعه کامل پارامترهای TLS / REALITY / اثر انگشت uTLS.
  **Hysteria2** و **TUIC** روی هسته sing-box اجرا می‌شوند که در صورت نیاز
  دانلود می‌شود. پروکسی **SOCKS5** شخصی خودتان
  (`socks://[user:pass@]host:port`) هم کار می‌کند — نیازی به اشتراک نیست.
- **پروفایل‌های چندسروری و اشتراک‌ها** — نگهداری چندین سرور؛ وارد کردن لینک
  اشتراک (به‌صورت base64 یا لیست‌های متنی ساده) و به‌روزرسانی آن در همان جا.
  سرورهایی که به‌صورت دستی اضافه شده‌اند پس از به‌روزرسانی حفظ می‌شوند و در
  صورت در دسترس بودن، سهمیه دیتا / تاریخ انقضای ارائه‌دهنده
  (`Subscription-Userinfo`) نمایش داده می‌شود.
- **تست تأخیر (Latency)** — TCPing گرفتن از همه سرورها، با نتایج رنگی برای
  هر سرور هم در انتخابگر QAM و هم در پنل وب.
- **آمار زنده ترافیک** — سرعت دانلود/آپلود و مجموع ترافیک نشست در QAM،
  به‌علاوه نمودار سرعت زنده در پنل وب.
- **پنل مدیریت وب** — رابط مدیریتی با ظاهر Steam روی گوشی/کامپیوتر (اتصال
  با اسکن QR از QAM): وضعیت زنده + نمودار سرعت، لیست سرورها، اطلاعات
  اشتراک، وارد کردن سرور، کلیدهای TUN / کیل سوییچ، و بررسی به‌روزرسانی
  هسته. با یک توکن تصادفی مخصوص هر نصب و محدودسازی نرخ تلاش‌های ناموفق برای
  ورود، محافظت می‌شود.
- **منوی دسترسی سریع (Quick Access Menu)** — کلید اتصال، انتخاب سرور،
  وضعیت/سرعت زنده، TUN + کیل سوییچ، و کد QR پنل مدیریت.
- **انگلیسی / روسی** — هم QAM و هم پنل وب بومی‌سازی شده‌اند (به‌صورت خودکار
  بر اساس زبان Steam / مرورگر تشخیص داده می‌شود).
- **کلید اتصال** — روشن/خاموش کردن پروکسی از منوی دسترسی سریع.
- **حالت TUN** — مسیریابی سراسری سیستم به سبک VPN از طریق یک اینترفیس شبکه
  مجازی، **برای حالت گیمینگ (Gaming Mode) توصیه می‌شود**.
- **کیل سوییچ (Kill Switch)** — مسدود کردن ترافیک هنگام قطع شدن پروکسی
  (اختیاری).
- **پایداری بالا** — کرش کردن xray-core بلافاصله شناسایی و با backoff
  مجدداً راه‌اندازی می‌شود؛ مسیرهای TUN پس از خواب/بیداری سیستم دوباره
  اعمال می‌شوند؛ اگر فایل‌سیستم غیرقابل‌تغییر باینری داخلی را پاک کند، هسته
  پین‌شده خودش را ترمیم می‌کند.

**بازیابی شبکه:** اگر Deck به‌دلیل بسته شدن ناگهانی افزونه اتصال شبکه‌اش را
از دست داد، از یک ترمینال در حالت دسکتاپ (Desktop Mode) دستور
`sudo bash recover.sh` را اجرا کنید (که در پوشه افزونه قرار دارد و همچنین
در [defaults/recover.sh](defaults/recover.sh) موجود است) — این اسکریپت
زنجیره فایروال کیل سوییچ، مسیرهای TUN باقی‌مانده و پروکسی سیستم را حذف
می‌کند.

## نصب

**پیش‌نیازها:** یک Steam Deck که [Decky Loader](https://wiki.deckbrew.xyz/) روی آن نصب باشد.

- **فروشگاه افزونه (توصیه‌شده):** Decky Loader → Plugin Store → جست‌وجوی «Xray Decky» → Install.
- **حالت دسکتاپ (نصب یک‌کلیکی):** فایل [Install-Xray-Decky.desktop](https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop) را دانلود کنید، آن را قابل اجرا کنید (Properties → Permissions) و دوبار کلیک کنید تا اجرا شود. به [scripts/README.md](scripts/README.md) مراجعه کنید.
- **نصب دستی:** فایل zip [آخرین نسخه منتشرشده](https://github.com/VadimOnix/xray-decky/releases/latest) را دانلود کنید → Decky Loader → Settings → Developer → Install Plugin from URL → لینک zip را وارد کنید.

**حالت TUN (توصیه‌شده):** در حالت گیمینگ، Steam تنظیمات پروکسی SOCKS سیستم
را رعایت نمی‌کند — بازی‌ها و اکثر سرویس‌های سیستمی آن را نادیده می‌گیرند.
حالت TUN یک اینترفیس شبکه مجازی می‌سازد که **تمام** ترافیک سیستم را از
طریق پروکسی مسیریابی می‌کند و به همین دلیل تنها روش قابل‌اعتماد برای
پروکسی کردن ترافیک در حالت گیمینگ است. TUN را در تنظیمات افزونه فعال
کنید؛ نیازی به تنظیم اضافه‌ای نیست.

بدون TUN، افزونه به حالت پروکسی SOCKS برمی‌گردد که در حالت دسکتاپ کار
می‌کند اما ممکن است بازی‌ها و سرویس‌های سیستمی را در حالت گیمینگ پوشش
ندهد.

**راهنمای استفاده، رفع اشکال و موارد بیشتر:** [مستندات GitHub Pages](https://vadimonix.github.io/xray-decky/).

## توسعه

### پیش‌نیازها

- Node.js v16.14+
- pnpm v9 (اجباری)
- Python 3.x
- باینری xray-core

### راه‌اندازی

```bash
pnpm install
pnpm run build
# Backend: pip install -r requirements-dev.txt
# xray-core: place in bin/xray-core
```

تست‌ها و لینترها (بدون نیاز به دستگاه واقعی): `pnpm test`، `pnpm run lint`،
`pytest tests/`، `ruff check py_modules/ tests/ main.py conftest.py`.
به [Tests and linters](CONTRIBUTING.md#tests-and-linters) مراجعه کنید.

### ساختار پروژه

```
├── src/                      # Frontend TypeScript/React
├── py_modules/backend/src/   # Backend Python, xray-core/sing-box managers
├── defaults/static/          # Embedded web admin panel (ships to plugin root)
├── defaults/recover.sh       # Network recovery script (ships to plugin root)
├── tests/                    # Python test suite (pytest)
├── tests/frontend/           # Frontend test suite (vitest: src/ + admin panel)
├── bin/                      # Local dev core binaries (xray-core, sing-box)
├── site/                     # GitHub Pages site (Astro, 5 locales)
├── main.py                   # Backend entry point
├── plugin.json
└── package.json
```

برای اطلاعات بیشتر به [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) و [docs/RELEASING.md](docs/RELEASING.md) مراجعه کنید.

## حمایت از پروژه

Xray Decky رایگان و متن‌باز است و در اوقات فراغت توسعه داده می‌شود. اگر به
کارتان آمد، با یک کمک مالی رمزارزی به ادامه توسعه آن کمک کنید.

| رمزارز | شبکه | آدرس |
| --- | --- | --- |
| GRAM | TON | `UQC_UNDyKIbeAy7qhTG8b6lFIJL3eyYwZit6pxQRtZZ6Dzo6` |
| USDT | TON | `UQC_UNDyKIbeAy7qhTG8b6lFIJL3eyYwZit6pxQRtZZ6Dzo6` |
| USDT | Tron (TRC-20) | `TZ3K36oh6FbpMvxncBwxqPzTC6NnHYQ1pL` |
| ETH | Ethereum (ERC-20) | `0x5F3FbC45A723c92a4797D98ECeE991f2a7b6eec6` |
| SOL | Solana | `ACpEC9m3MuacKL4wwEnfTKGCNNDHuvaKdPLD7DuFvvvB` |
| BTC | Bitcoin | `bc1q9zx6y445lqryl60z3phfekqajyjs45meex4cd4` |

## مجوز

MIT — به فایل LICENSE مراجعه کنید.

## منابع

- [Decky Loader](https://wiki.deckbrew.xyz/)
- [xray-core](https://xtls.github.io/)
- [مشخصات افزونه](./specs/001-xray-vless-decky/spec.md)
