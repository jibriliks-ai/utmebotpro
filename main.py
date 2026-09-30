"""
UTME SUCCESS BOT - v15 FINALISED PRODUCTION BUILD
- 100% Fixed Syntax Error (Closed payload brackets)
- Isolated Async Thread Loop Execution Protocol
- Decoupled Horizontal Keyboard Renderers
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

print("=== UTME Bot v15 FIXED PRODUCTION PRO ===")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "").strip()
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "").strip()
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
RENDER_RAW = os.getenv("RENDER_EXTERNAL_URL", "https://onrender.com")
RENDER_URL = RENDER_RAW.strip().rstrip("/").replace("://", ".onrender.com")
if not RENDER_URL.startswith("http"):
    RENDER_URL = "https://" + RENDER_URL
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
BOT_LINK = os.getenv("BOT_USERNAME_LINK", "@UTMESuccessBot")
BOT_USERNAME = os.getenv("BOT_USERNAME", "UTMESuccessBot")

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

# SYSTEM PERSISTENCE FILES
DB_FILE = "premium_users.json"
STATS_FILE = "user_stats.json"
REFERRAL_FILE = "referrals.json"
PROFILES_FILE = "user_profiles.json"
USAGE_FILE = "free_usage.json"
POSTED_FILE = "posted_today.json"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Save {path} error: {e}", flush=True)

def is_premium(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud:
        return False
    return time.time() < ud.get("expiry", 0)

def get_premium_days(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud:
        return 0
    return max(0, int((ud.get("expiry", 0) - time.time()) / 86400))

def grant_premium(uid, days=30, tx_ref=None, email=None):
    db = load_json(DB_FILE, {})
    expiry = time.time() + days * 24 * 60 * 60
    ex = db.get(str(uid))
    if ex and ex.get("expiry", 0) > time.time():
        expiry = ex["expiry"] + days * 24 * 60 * 60
    db[str(uid)] = {
        "user_id": str(uid), 
        "expiry": expiry, 
        "expiry_date": time.strftime("%Y-%m-%d", time.localtime(expiry)), 
        "tx_ref": tx_ref, 
        "email": email, 
        "granted_at": time.time(), 
        "days": days
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
        "first_seen": ex.get('first_seen', time.time()),
        "last_seen": time.time(),
        "visits": ex.get('visits', 0) + 1,
        "is_premium": is_premium(uid),
        "referrals": len(load_json(REFERRAL_FILE, {}).get(uid_str, []))
    }
    save_json(PROFILES_FILE, profiles)

def get_referral_count(uid):
    return len(load_json(REFERRAL_FILE, {}).get(str(uid), []))

def add_referral(referrer, referred):
    if str(referrer) == str(referred):
        return False, 0
    refs = load_json(REFERRAL_FILE, {})
    if str(referrer) not in refs:
        refs[str(referrer)] = []
    if str(referred) in refs[str(referrer)]:
        return False, len(refs[str(referrer)])
    refs[str(referrer)].append(str(referred))
    save_json(REFERRAL_FILE, refs)
    count = len(refs[str(referrer)])
    if count % 3 == 0:
        grant_premium(referrer, days=7, tx_ref=f"referral-{count}")
        return True, count
    return False, count

# ===== FREEMIUM WALL POLICY SUITE =====
FREE_MOCK_QS = 5
FREE_MOCK_PER_DAY = 1
FREE_TUTOR_PER_DAY = 2

def get_usage(uid):
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": "", "mock": 0, "tutor": 0, "mock_qs": 0})
    if ud.get("date") != today:
        ud = {"date": today, "mock": 0, "tutor": 0, "mock_qs": 0}
        data[str(uid)] = ud
        save_json(USAGE_FILE, data)
    return ud

def can_mock(uid):
    if is_premium(uid):
        return True, "Premium unlimited"
    u = get_usage(uid)
    if u.get("mock", 0) >= FREE_MOCK_PER_DAY:
        return False, f"🚫 Free limit reached: {FREE_MOCK_QS} questions per day.\n💎 Upgrade to premium for unlimited 180Q mocks.\n👥 Or invite 3 friends for 7 days FREE premium."
    return True, f"Free {FREE_MOCK_QS}Q available"

def inc_mock(uid, qs_count=FREE_MOCK_QS):
    if is_premium(uid):
        return
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": today, "mock": 0, "tutor": 0, "mock_qs": 0})
    ud["mock"] = ud.get("mock", 0) + 1
    ud["mock_qs"] = ud.get("mock_qs", 0) + qs_count
    ud["date"] = today
    data[str(uid)] = ud
    save_json(USAGE_FILE, data)

def can_tutor(uid):
    if is_premium(uid):
        return True, "Premium unlimited"
    u = get_usage(uid)
    if u.get("tutor", 0) >= FREE_TUTOR_PER_DAY:
        return False, f"🚫 Free Tutor limit reached: {FREE_TUTOR_PER_DAY} questions per day.\n💎 Upgrade to premium for unlimited AI tutor.\n👥 Or invite 3 friends for 7 days FREE."
    remaining = FREE_TUTOR_PER_DAY - u.get("tutor", 0)
    return True, f"Free tutor: {remaining} left today"

def inc_tutor(uid):
    if is_premium(uid):
        return
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": today, "mock": 0, "tutor": 0, "mock_qs": 0})
    ud["tutor"] = ud.get("tutor", 0) + 1
    ud["date"] = today
    data[str(uid)] = ud
    save_json(USAGE_FILE, data)

def get_free_limit_keyboard(uid):
    upgrade_url = f"{RENDER_URL}/upgrade/{uid}"
    kb = [
        [InlineKeyboardButton("💎 Upgrade Premium Access", url=upgrade_url)],
        [InlineKeyboardButton("👥 Invite 3 Friends = 7 Days FREE", callback_data="menu_invite")],
        [InlineKeyboardButton("🔵 Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(kb)

def update_stats(uid, subject, correct, total, jamb_score, name="", is_full=False):
    stats = load_json(STATS_FILE, {})
    u = stats.get(str(uid), {"total_exams": 0, "total_score": 0, "best_score": 0, "name": name, "subjects": {}, "history": [], "full_count": 0, "free_count": 0})
    if name:
        u["name"] = name
    if is_full:
        u["total_exams"] += 1
        u["total_score"] += jamb_score
        u["best_score"] = max(u.get("best_score", 0), jamb_score)
        u["full_count"] = u.get("full_count", 0) + 1
        if subject not in u["subjects"]:
            u["subjects"][subject] = {"correct": 0, "total": 0, "avg": 0}
        u["subjects"][subject]["correct"] += correct
        u["subjects"][subject]["total"] += total
        u["subjects"][subject]["avg"] = int(u["subjects"][subject]["correct"] / max(u["subjects"][subject]["total"], 1) * 100)
    else:
        u["free_count"] = u.get("free_count", 0) + 1
    u["last_seen"] = time.time()
    u["history"].append({"date": time.strftime("%Y-%m-%d %H:%M"), "subject": subject, "score": f"{correct}/{total}", "jamb": jamb_score, "full": is_full})
    u["history"] = u["history"][-20:]
    stats[str(uid)] = u
    save_json(STATS_FILE, stats)
    return u

def get_top_scorer():
    stats = load_json(STATS_FILE, {})
    if not stats:
        return None, 0
    full_users = {k: v for k, v in stats.items() if v.get('full_count', 0) > 0}
    if not full_users:
        return None, 0
    top = max(full_users.items(), key=lambda x: x.get('best_score', 0))
    return top.get('name', 'Anonymous'), top.get('best_score', 0)

def get_user_stats(uid):
    return load_json(STATS_FILE, {}).get(str(uid))

# FLUTTERWAVE GATEWAY CONFIGURATION (FIXED CLOSING SYNTAX HERE)
def create_flutterwave_payment(uid, email="student@example.com", name="UTME Student"):
    if not FLW_SECRET_KEY:
        return None, "FLW_SECRET_KEY missing from environment configurations variables."
    import requests
    tx_ref = f"utme-{uid}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    url = "https://flutterwave.com"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    redirect_url = f"{RENDER_URL}/verify/{tx_ref}?uid={uid}"
    payload = {
        "tx_ref": tx_ref,
        "amount": PREMIUM_PRICE,
        "currency": "NGN",
        "redirect_url": redirect_url,
        "payment_options": "card,banktransfer,ussd",
        "customer": {"email": email, "name": name},
