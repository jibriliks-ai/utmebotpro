"""
UTME SUCCESS MASTER BOT - WEBHOOK PRODUCTION Build
- Synchronous direct request web architecture
- 100% Fixed environment port bindings for stable Render deployment
"""

import os
import json
import time
import uuid
import re
import html
import requests
from flask import Flask, request, jsonify, render_template_string, redirect

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=== UTME SUCCESS BOT MASTER ENGINE BOOTING ===")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
RENDER_RAW = os.getenv("RENDER_EXTERNAL_URL", "https://onrender.com")
RENDER_URL = RENDER_RAW.strip().rstrip("/").replace("://", ".onrender.com")
if not RENDER_URL.startswith("http"):
    RENDER_URL = "https://" + RENDER_URL

if not BOT_TOKEN:
    print("❌ CRITICAL ERROR: BOT_TOKEN is missing in Render Environment Variables! Exiting...")
    exit(1)

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

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
    except Exception as e: print(f"Save database error: {e}", flush=True)

def is_premium(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud: return False
    return time.time() < ud.get("expiry", 0)

def save_profile(uid, first_name, username):
    profiles = load_json(PROFILES_FILE, {})
    uid_str = str(uid)
    profiles[uid_str] = {
        "user_id": uid,
        "first_name": first_name or 'Student',
        "username": username or '',
        "last_seen": time.time(),
        "is_premium": is_premium(uid)
    }
    save_json(PROFILES_FILE, profiles)

# ===== FREEMIUM ACCESS RULES =====
FREE_MOCK_QS = 5
FREE_MOCK_PER_DAY = 1

def get_usage(uid):
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": "", "mock": 0})
    if ud.get("date") != today:
        ud = {"date": today, "mock": 0}
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
    ud = data.get(str(uid), {"date": today, "mock": 0})
    ud["mock"] += 1
    data[str(uid)] = ud
    save_json(USAGE_FILE, data)

# NATIVE HTTP TELEGRAM REQUEST MESSENGER
def send_tg_message(chat_id, text, reply_markup=None):
    url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Delivery Timeout Warning: {e}", flush=True)

# CORE DATA ENGINE INSTANTIATION
from cbt_engine import CBTEngine
cbt = CBTEngine()

def format_question(q, idx, total):
    header = f"<b>📝 Question {idx+1}/{total}</b> | {q.get('subject')} | {q.get('year')}\n\n"
    body = f"<b>{html.escape(q.get('question', ''))}</b>\n\n"
    opts_block = ""
    for letter, text in q.get('options', {}).items():
        opts_block += f"<b>{letter}</b>: {html.escape(str(text))}\n"
    return header + body + opts_block

def get_main_menu_markup():
    return {
        "inline_keyboard": [
            [{"text": "📝 Take Mock Exam", "callback_data": "menu_mock"}, {"text": "📚 Past Questions", "callback_data": "menu_past"}],
            [{"text": "💎 Go Premium Access", "callback_data": "menu_premium"}]
        ]
    }

def get_options_markup(q, current_idx):
    row = [{"text": f"Option {k}", "callback_data": f"ans_{k}"} for k in q.get('options', {}).keys()]
    return {
        "inline_keyboard": [
            row,
            [{"text": "🛑 Submit Exam", "callback_data": "submit"}],
            [{"text": "🔙 Back to Main Menu", "callback_data": "menu_main"}]
        ]
    }

# FLASK CORE INSTANCE
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({"status": "UTME Bot Engine Active", "api_mode": "Streaming"})

@flask_app.route("/telegram", methods=["POST"])
def webhook_endpoint():
    data = request.get_json(force=True)
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        first_name = msg["from"].get("first_name", "Student")
        username = msg["from"].get("username", "")
        
        if text.startswith("/start"):
            save_profile(chat_id, first_name, username)
            status_tag = "💎 Premium Tier" if is_premium(chat_id) else "🆓 Free Access Tier"
            welcome = f"🎓 <b>Welcome to JAMB UTME Success Master Bot Pro!</b>\n\n⚙️ Account Status: <b>{status_tag}</b>\n\nSelect an option module below to kickstart your preparation loops:"
            send_tg_message(chat_id, welcome, reply_markup=get_main_menu_markup())
            
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        cb_data = query["data"]
        uid = query["from"]["id"]
        
        if cb_data == "menu_main":
            status_tag = "💎 Premium Tier" if is_premium(uid) else "🆓 Free Access Tier"
            send_tg_message(chat_id, f"🎓 <b>Main Console Dashboard:</b>\n\nStatus: <b>{status_tag}</b>", reply_markup=get_main_menu_markup())
            
        elif cb_data == "menu_mock":
            ok, msg = can_mock(uid)
            if not ok:
                send_tg_message(chat_id, msg)
                return "OK", 200
            limit = 40 if is_premium(uid) else FREE_MOCK_QS
            if not is_premium(uid): inc_mock(uid)
            q, total = cbt.start_mock(uid, ["English", "Mathematics"], limit_per_subject=limit//2)
            if q:
                send_tg_message(chat_id, format_question(q, 0, total), reply_markup=get_options_markup(q, 0))
                
        elif cb_data == "menu_past":
            row1 = [{"text": s[:4], "callback_data": f"past_{s}"} for s in SUBJECTS[:5]]
            row2 = [{"text": s[:4], "callback_data": f"past_{s}"} for s in SUBJECTS[5:]]
            markup = {"inline_keyboard": [row1, row2, [{"text": "🔙 Back", "callback_data": "menu_main"}]]}
            send_tg_message(chat_id, "📚 <b>Select Past Question Subject Array:</b>", reply_markup=markup)
            
        elif cb_data.startswith("past_"):
            subj = cb_data.replace("past_", "")
            ok, msg = can_mock(uid)
            if not ok:
                send_tg_message(chat_id, msg)
                return "OK", 200
            limit = 40 if is_premium(uid) else FREE_MOCK_QS
            if not is_premium(uid): inc_mock(uid)
            q, total = cbt.start_mock(uid, [subj], limit_per_subject=limit)
            if q:
                send_tg_message(chat_id, format_question(q, 0, total), reply_markup=get_options_markup(q, 0))
                
        elif cb_data.startswith("ans_"):
            choice = cb_data.replace("ans_", "")
            res, status = cbt.answer_current(uid, choice)
            if status == "FINISHED":
                update_stats(uid, "General Mix", res['raw_score'], res['total'], res['jamb_score'])
                send_tg_message(chat_id, f"🏁 <b>Exam Session Finished!</b>\n\nScore parameters: {res['raw_score']}/{res['total']}\nEstimated JAMB Score: <b>{res['jamb_score']}/400</b>")
            elif status == "NEXT":
                nq, nidx = res
                exam = cbt.active_exams.get(uid)
                total = len(exam['questions']) if exam else 0
                send_tg_message(chat_id, format_question(nq, nidx, total), reply_markup=get_options_markup(nq, current_idx=nidx))
                
        elif cb_data == "submit":
            res = cbt.finish_exam(uid)
            if res:
                send_tg_message(chat_id, f"🏁 <b>Exam session early terminated.</b>\nScore: {res['raw_score']}/{res['total']}")
                
        elif cb_data == "menu_premium":
            send_tg_message(chat_id, f"💎 <b>Premium Billing Portal Checkout Link:</b>\n\n🔗 Link: {RENDER_URL}/upgrade/{uid}")
            
    return "OK", 200

@flask_app.route("/upgrade/<uid>")
def upgrade_checkout(uid):
    return render_template_string(f"<h1>🎓 Premium Activation</h1><p>User Token Parameter: {uid}</p>")

# AUTO-REGISTER WEBHOOK TARGET ON STARTUP
try:
    target_webhook = f"{RENDER_URL}/telegram"
    r = requests.get(f"https://telegram.org{BOT_TOKEN}/setWebhook?url={target_webhook}&drop_pending_updates=true", timeout=6)
    print(f"📢 Webhook setup response: {r.text}", flush=True)
except Exception as e:
    print(f"Webhook setup notice flag: {e}", flush=True)

if __name__ == "__main__":
    # MANDATORY FIX: Pull Render's assigned port dynamically or fall back to 10000
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Launching core server instance layer on host 0.0.0.0 and port: {port}", flush=True)
    flask_app.run(host="0.0.0.0", port=port)
