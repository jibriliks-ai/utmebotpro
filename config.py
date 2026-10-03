"""
config.py — all settings. Override via Render env vars.
"""
import os
import logging

log = logging.getLogger(__name__)

# Telegram
BOT_TOKEN      = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME   = os.getenv("BOT_USERNAME", "YourBot")
ADMIN_ID       = os.getenv("ADMIN_ID", "")

# Channel auto-posting
CHANNEL_ID       = os.getenv("CHANNEL_ID", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "UTMESUCCESS")

# Web app
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-app.onrender.com")
PORT        = int(os.getenv("PORT", "5000"))

# Storage
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_data.json")

# Pricing (2 plans)
PREMIUM_PRICE         = int(os.getenv("PREMIUM_PRICE", "2000"))
PREMIUM_PRICE_TEXT    = f"\u20a6{PREMIUM_PRICE}"
PREMIUM_6MONTHS_PRICE = int(os.getenv("PREMIUM_6MONTHS_PRICE", "6000"))
PREMIUM_6MONTHS_TEXT  = f"\u20a6{PREMIUM_6MONTHS_PRICE}"
PREMIUM_DAYS          = int(os.getenv("PREMIUM_DAYS", "30"))
PREMIUM_6MONTHS_DAYS  = int(os.getenv("PREMIUM_6MONTHS_DAYS", "180"))

# Free tier
FREE_MOCK_QS_DAILY = int(os.getenv("FREE_MOCK_QS_DAILY", "5"))
FREE_TUTOR_PER_DAY = int(os.getenv("FREE_TUTOR_PER_DAY", "10"))

# Referrals
REFERRAL_REQUIRED    = int(os.getenv("REFERRAL_REQUIRED", "3"))
REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", "7"))

# Flutterwave
FLW_PUBLIC_KEY           = os.getenv("FLW_PUBLIC_KEY", "")
FLW_SECRET_KEY           = os.getenv("FLW_SECRET_KEY", "")
FLW_ENCRYPTION_KEY       = os.getenv("FLW_ENCRYPTION_KEY", "")
FLW_SECRET_HASH          = os.getenv("FLW_SECRET_HASH", "")
FLUTTERWAVE_PAYMENT_LINK = os.getenv("FLUTTERWAVE_PAYMENT_LINK", "")
FLUTTERWAVE_6MONTHS_LINK = os.getenv("FLUTTERWAVE_6MONTHS_LINK", "")

# Paystack (optional backup)
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")

# Subject list — matches your 11 databank files
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
    "crk",
]

# Year range in your bank
YEARS = list(range(1976, 2025))

if os.getenv("CONFIG_VERBOSE", "0") == "1":
    log.info(
        "config loaded | %s/mo · %s/6mo | free %s mock/day | refer %s=%s",
        PREMIUM_PRICE_TEXT, PREMIUM_6MONTHS_TEXT,
        FREE_MOCK_QS_DAILY, REFERRAL_REQUIRED, REFERRAL_REWARD_DAYS,
    )
