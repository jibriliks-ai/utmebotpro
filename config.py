"""
config.py - v23 FLUTTERWAVE + 2 PLANS
Monthly ₦2000 + 6 Months ₦6000
"""
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBot")
ADMIN_ID = os.getenv("ADMIN_ID", "")
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-app.onrender.com")

# PRICING - 2 PLANS
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
PREMIUM_PRICE_TEXT = f"₦{PREMIUM_PRICE}"
PREMIUM_6MONTHS_PRICE = int(os.getenv("PREMIUM_6MONTHS_PRICE", "6000"))
PREMIUM_6MONTHS_TEXT = f"₦{PREMIUM_6MONTHS_PRICE}"
FREE_MOCK_QS_DAILY = int(os.getenv("FREE_MOCK_QS_DAILY", "5"))
FREE_TUTOR_PER_DAY = int(os.getenv("FREE_TUTOR_PER_DAY", "10"))
PREMIUM_DAYS = int(os.getenv("PREMIUM_DAYS", "30"))

# REFERRAL
REFERRAL_REQUIRED = int(os.getenv("REFERRAL_REQUIRED", "3"))
REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", "7"))

# FLUTTERWAVE - You said you use Flutterwave, not Paystack
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utme_webhook_hash_123")
FLW_ENCRYPTION_KEY = os.getenv("FLW_ENCRYPTION_KEY", "")
FLUTTERWAVE_PAYMENT_LINK = os.getenv("FLUTTERWAVE_PAYMENT_LINK", "")

# PAYSTACK (kept as fallback)
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")

# CHANNEL
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "UTMESUCCESS")

USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_data.json")
YEARS = list(range(2010, 2025))
ALL_SUBJECTS = ["english","mathematics","biology","physics","chemistry","economics","government","commerce","accounting","literature","crk"]

print(f"Config v23 FLUTTERWAVE: Monthly {PREMIUM_PRICE_TEXT} + 6 Months {PREMIUM_6MONTHS_TEXT} | Free {FREE_MOCK_QS_DAILY} mock/day | Refer {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days")
