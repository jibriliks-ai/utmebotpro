"""
config.py - UTME Bot v17.1 FINAL - Complete Env Vars
Free: 5 mock Qs (daily locked) + 2 tutor/day
Premium: ₦2000 unlimited
Referral: 3 people = 1 week premium
"""
import os

# CORE
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBot")
ADMIN_ID = os.getenv("ADMIN_ID", "")
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-app.onrender.com")

# ALOC
ALOC_ACCESS_TOKEN = os.getenv("ALOC_ACCESS_TOKEN", "")

# PRICING & LIMITS - AS PER USER SPEC
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
PREMIUM_PRICE_TEXT = f"₦{PREMIUM_PRICE}"
FREE_MOCK_QS_DAILY = int(os.getenv("FREE_MOCK_QS_DAILY", "5"))  # 5 free mock Qs per day - LOCKED
FREE_TUTOR_PER_DAY = int(os.getenv("FREE_TUTOR_PER_DAY", "10"))  # 2 tutor Qs free
PREMIUM_DAYS = int(os.getenv("PREMIUM_DAYS", "30"))

# REFERRAL - 3 people = 1 week premium
REFERRAL_REQUIRED = int(os.getenv("REFERRAL_REQUIRED", "3"))
REFERRAL_REWARD_DAYS = int(os.getenv("REFERRAL_REWARD_DAYS", "7"))

# PAYSTACK
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")

# FLUTTERWAVE
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utme_webhook_hash_123")
FLW_ENCRYPTION_KEY = os.getenv("FLW_ENCRYPTION_KEY", "")

# CHANNEL - Auto posting 3x daily 8am,1pm,8pm
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "UTMESUCCESS")

# STORAGE
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_data.json")

YEARS = list(range(2010, 2025))
ALL_SUBJECTS = ["english","mathematics","biology","physics","chemistry","economics","government","commerce","accounting","literature","crk","geography","civic","history"]

print(f"Config v21 PROFESSIONAL: Premium {PREMIUM_PRICE_TEXT} | Free {FREE_MOCK_QS_DAILY} mock/day + {FREE_TUTOR_PER_DAY} tutor/day | Refer {REFERRAL_REQUIRED}= {REFERRAL_REWARD_DAYS} days premium")
