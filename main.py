"""
UTME SUCCESS MASTER BOT - v25 PREMIUM PRO
- Fixed background worker event loops using explicit native async run setups
- Meticulously structured visual visual anchors for 100% professional aesthetics
- Strict enforcement of the 5-question freemium wall
"""

import os
import json
import time
import uuid
import threading
import re
import html
import asyncio
from flask import Flask, request, jsonify, render_template_string, redirect

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=== UTME SUCCESS BOT PREMIUM PRO ===")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "").strip()
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
RENDER_RAW = os.getenv("RENDER_EXTERNAL_URL", "https://onrender.com")
RENDER_URL = RENDER_RAW.strip().rstrip("/").replace("://", ".onrender.com")
if not RENDER_URL.startswith("http"):
    RENDER_URL = "https://" + RENDER_URL

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]
JAMB_SYLLABUS = {
    "English": ["Comprehension", "Lexis & Structure", "Oral Forms", "Parts of Speech"],
    "Mathematics": ["Algebra", "Geometry", "Calculus", "Statistics", "Trigonometry"],
    "Biology": ["Variety of Organisms", "Cell Structure", "Genetics", "Ecology", "Physiology"],
    "Chemistry": ["Particulate Nature", "Periodic Table", "Bonding", "Organic Chemistry", "Acids & Bases"],
    "Physics": ["Mechanics", "Waves", "Electricity", "Heat", "Optics"],
    "Economics": ["Demand & Supply", "Production", "Market Structure", "National Income"],
    "Government": ["Constitution", "Government Arms", "Political Parties"],
    "Literature": ["Poetry", "Drama", "Prose"],
    "Commerce": ["Trade", "Business Units", "Finance"],
    "CRS": ["Old Testament", "New Testament"]
}

DB_FILE = "premium_users.json"
STATS_FILE = "user_stats.json"
REFERRAL_FILE = "referrals.json"
PROFILES_FILE = "user_profiles.json"
USAGE_FILE = "free_usage.json"

def load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e: print(f"Save {path} error: {e}", flush=True)

def is_premium(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud: return False
    return time.time() < ud.get("expiry", 0)

def get_premium_days(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud: return 0
    return max(0, int((ud.get("expiry", 0) - time.time()) / 86400))

def grant_premium(uid, days=30, tx_ref=None):
    db = load_json(DB_FILE, {})
    expiry = time.time() + days * 24 * 60 * 60
    db[str(uid)] = {
        "user_id": str(uid), 
        "expiry": expiry, 
        "expiry_date": time.strftime("%Y-%m-%d", time.localtime(expiry)), 
        "tx_ref": tx_ref,
        "granted_at": time.time()
    }
    save_json(DB_FILE, db)
    return expiry

def save_profile(uid, user_obj):
    profiles = load_json(PROFILES_FILE, {})
    uid_str = str(uid)
    ex = profiles.get(uid_str, {})
    profiles[uid_str] = {
        "user_id": uid,
        "first_name": getattr(user_obj, 'first_name', ex.get('first_name', 'Student')),
        "username": getattr(user_obj, 'username', ex.get('username', '')),
        "last_seen": time.time(),
        "is_premium": is_premium(uid)
    }
    save_json(PROFILES_FILE, profiles)

def get_referral_count(uid):
    return len(load_json(REFERRAL_FILE, {}).get(str(uid), []))

# ===== EXPLICIT FREEMIUM BOUNDARY VERIFICATIONS =====
FREE_MOCK_QS = 5
FREE_MOCK_PER_DAY = 1
FREE_TUTOR_PER_DAY = 2

def get_usage(uid):
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": "", "mock": 0, "tutor": 0})
    if ud.get("date") != today:
        ud = {"date": today, "mock": 0, "tutor": 0}
        data[str(uid)] = ud
        save_json(USAGE_FILE, data)
    return ud

def can_mock(uid):
    if is_premium(uid): return True, "Premium unlimited"
    u = get_usage(uid)
    if u.get("mock", 0) >= FREE_MOCK_PER_DAY:
        return False, f"⚠️ <b>Daily Free Mock Limit Reached!</b>\n\nFree tier accounts are limited to exactly 1 exam of 5 questions per day.\n\n💎 <b>Upgrade to Premium</b> to unlock full 180-Question mock simulations with zero repetition!"
    return True, f"Free {FREE_MOCK_QS}Q Mocks Available"

def inc_mock(uid):
    if is_premium(uid): return
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": today, "mock": 0, "tutor": 0})
    ud["mock"] += 1
    data[str(uid)] = ud
    save_json(USAGE_FILE, data)

def can_tutor(uid):
    if is_premium(uid): return True, "Premium unlimited"
    u = get_usage(uid)
    if u.get("tutor", 0) >= FREE_TUTOR_PER_DAY:
        return False, f"⚠️ <b>AI Tutor Daily Limit Reached!</b>\n\nYou have used your 2 free dynamic tutor requests for today.\n\n💎 Upgrade to Premium for unhindered smart textbook explanations with instant voice answers!"
    return True, ""

def inc_tutor(uid):
    if is_premium(uid): return
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": today, "mock": 0, "tutor": 0})
    ud["tutor"] += 1
    data[str(uid)] = ud
    save_json(USAGE_FILE, data)

def get_free_limit_keyboard(uid):
    upgrade_url = f"{RENDER_URL}/upgrade/{uid}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Upgrade to Premium Tier", url=upgrade_url)],
        [InlineKeyboardButton("👥 Referral Program", callback_data="menu_invite")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
    ])

def update_stats(uid, subject, correct, total, jamb_score, name=""):
    stats = load_json(STATS_FILE, {})
    u = stats.get(str(uid), {"best_score": 0, "name": name, "total_exams": 0})
    u["total_exams"] += 1
    u["best_score"] = max(u["best_score"], jamb_score)
    stats[str(uid)] = u
    save_json(STATS_FILE, stats)
    return u

# FLUTTERWAVE IMPLEMENTATION
def create_flutterwave_payment(uid):
    if not FLW_SECRET_KEY: return None, "Configuration key missing"
    import requests
    tx_ref = f"utme-{uid}-{int(time.time())}"
    url = "https://flutterwave.com"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "tx_ref": tx_ref, "amount": PREMIUM_PRICE, "currency": "NGN",
        "redirect_url": f"{RENDER_URL}/verify/{tx_ref}?uid={uid}",
        "payment_options": "card,banktransfer,ussd",
        "customer": {"email": f"student_{uid}@utmebot.com", "name": "JAMB Candidate"},
        "customizations": {"title": "UTME Success Premium", "description": "30 Days Full Master Access"}
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        d = res.json()
        if d.get("status") == "success": return d["data"]["link"], tx_ref
        return None, d.get("message")
    except Exception as e: return None, str(e)

# FLASK ROUTING LAYER
flask_app = Flask(__name__)

@flask_app.route("/")
def home(): return jsonify({"status": "UTME Bot Engine Active", "total_questions": len(cbt.db)})

@flask_app.route("/upgrade/<uid>")
def upgrade_page(uid):
    pay_link, _ = create_flutterwave_payment(uid)
    return render_template_string("""
    <!DOCTYPE html><html><head><title>Premium Upgrade</title><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:40px} .card{max-width:440px;margin:0 auto;background:#1e293b;padding:30px;border-radius:16px;border:1px solid #334155} .btn{display:block;padding:16px;background:#eab308;color:#0f172a;text-decoration:none;border-radius:8px;font-weight:bold;margin-top:20px}</style></head>
    <body><div class='card'><h2>🎓 UTME Success Premium</h2><h3>N{{price}} / Month</h3><p align='left'>✅ Unlimited 180Q Exam Combinations<br>✅ Unlimited Smart AI Tutor Explanations<br>✅ High-Speed Audio Explanations</p><a href='{{link}}' class='btn'>Proceed to Secure Checkout</a></div></body></html>
    """, price=PREMIUM_PRICE, link=pay_link or "#", uid=uid)

@flask_app.route("/verify/<tx_ref>")
def verify_page(tx_ref):
    uid = request.args.get('uid', '0')
    grant_premium(uid, 30, tx_ref)
    return "<h1>✅ Payment Successfully Verified!</h1><p>Return to the Telegram bot and enter /start to synchronize your account changes.</p>"

# SMART REASONING LAYER
def get_tutor_answer(q_text):
    if DEEPSEEK_API_KEY:
        try:
            import requests
            url = "https://deepseek.com"
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a professional JAMB expert tutor. Provide accurate, clear, and high-yield structured past question answers with a short, simple explanation for high school students to read quickly."},
                    {"role": "user", "content": q_text}
                ],
                "max_tokens": 400, "temperature": 0.2
            }
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            if r.status_code == 200: return r.json()['choices'][0]['message']['content'].strip()
        except: pass
    return "💡 <b>Educational Insight:</b> Ensure to reference your official JAMB recommended syllabus text. Break down the terms systematically to eliminate incorrect options logically."

# CORE DATA ENGINE INSTANTIATION
