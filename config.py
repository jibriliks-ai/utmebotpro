"""
config.py - v24 Production-Grade
Flutterwave payments | 2 plans | matches actual question bank
"""
import os
import logging

log = logging.getLogger(__name__)

# ---------- Telegram ----------
BOT_TOKEN      = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME   = os.getenv("BOT_USERNAME", "YourBot")
ADMIN_ID       = os.getenv("ADMIN_ID", "")

# ---------- Channel (single source of truth) ----------
CHANNEL_ID       = os.getenv("CHANNEL_ID", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "UTMESUCCESS")

# ---------- Web app ----------
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-app.onrender.com")
PORT        = int(os.getenv("PORT", "5000"))

# ---------- Storage ----------
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_data.json")

# ---------- Pricing ----------
PREMIUM_PRICE           = int(os.getenv("PREMIUM_PRICE", "2000"))
PREMIUM_PRICE_TEXT      = f"\u20a6{PREMIUM_PRICE}"     # ₦2000
PREMIUM_6MONTHS_PRICE   = int(os.getenv("PREMIUM_6MONTHS_PRICE", "6000"))
PREMIUM_6MONTHS_TEXT    = f"\u20a6{PREMIUM_6MONTHS_PRICE}"

PREMIUM_DAYS            = int(os.getenv("PREMIUM_DAYS", "30"))
PREMIUM_6MONTHS_DAYS    = int(os.getenv("PREMIUM_6MONTHS_DAYS", "180"))

# ---------- Free tier ----------
FREE_MOCK_QS_DAILY   = int(os.getenv("FREE_MOCK_QS_DAILY", "5"))
FREE_TUTOR_PER_DAY   = int(os.getenv("FREE_TUTOR_PER_DAY", "10"))

# ---------- Referrals ----------
REFERRAL_REQUIRED     = int(os.getenv("REFERRAL_REQUIRED", "3"))
REFERRAL_REWARD_DAYS  = int(os.getenv("REFERRAL_REWARD_DAYS", "7"))

# ---------- Flutterwave ----------
FLW_PUBLIC_KEY            = os.getenv("FLW_PUBLIC_KEY", "")
FLW_SECRET_KEY            = os.getenv("FLW_SECRET_KEY", "")
FLW_ENCRYPTION_KEY        = os.getenv("FLW_ENCRYPTION_KEY", "")
FLW_SECRET_HASH           = os.getenv("FLW_SECRET_HASH", "")   # NO default — must be set in prod
FLUTTERWAVE_PAYMENT_LINK  = os.getenv("FLUTTERWAVE_PAYMENT_LINK", "")     # monthly
FLUTTERWAVE_6MONTHS_LINK  = os.getenv("FLUTTERWAVE_6MONTHS_LINK", "")     # 6-month

# Legacy / other gateways (kept for compatibility)
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
ALOC_ACCESS_TOKEN   = os.getenv("ALOC_ACCESS_TOKEN", "")

# ---------- Subjects (match actual question bank) ----------
# Only include subjects that exist in the databank.
# Do NOT add crk / geography / civic / history until questions exist for them.
ALL_SUBJECTS = [
    "english",
    "mathematics",
    "biology",
    "physics",
    "chemistry",
    "economics",
    "government",
    "commerce",
    "accounting",
    "literature",
]

# ---------- Year range (reflects actual databank) ----------
# Your bank contains questions from ~1976 through 2018.
YEARS = list(range(1976, 2019))

# ---------- Startup diagnostic ----------
if os.getenv("CONFIG_VERBOSE", "0") == "1":
    log.info(
        "config v24 | monthly=%s | 6mo=%s | free=%s mock/day | "
        "tutor=%s/day | refer %s=%s days | subjects=%d",
        PREMIUM_PRICE_TEXT, PREMIUM_6MONTHS_TEXT,
        FREE_MOCK_QS_DAILY, FREE_TUTOR_PER_DAY,
        REFERRAL_REQUIRED, REFERRAL_REWARD_DAYS, len(ALL_SUBJECTS),
    )
