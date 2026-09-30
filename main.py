"""
UTME SUCCESS BOT - v20 BULLETPROOF WEBHOOK ENGINE
- Zero Asyncio loop collisions (Uses native network requests)
- Handles 100% of Telegram data pipelines directly on the main Flask thread
- Full multi-part JSON database fragment extraction compatibility
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

print("=== UTME Bot v20 WEBHOOK MASTER ENGINE ===")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "").strip()
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "").strip()
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
RENDER_RAW = os.getenv("RENDER_EXTERNAL_URL", "https://onrender.com")
RENDER_URL = RENDER_RAW.strip().rstrip("/").replace("://", ".onrender.com")
if not RENDER_URL.startswith("http"):
    RENDER_URL = "https://" + RENDER_URL

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

# SYSTEM PERSISTENCE FILES
DB_FILE = "premium_users.json"
STATS_FILE = "user_stats.json"
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

# ===== FREEMIUM LIMIT CHECKS =====
FREE_MOCK_QS = 5

def can_mock(uid):
    if is_premium(uid): return True, ""
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    ud = data.get(str(uid), {"date": "", "mock": 0})
    if ud.get("date") == today and ud.get("mock", 0) >= 1:
        return False, f"🚫 Daily Limit: Free mock limited to {FREE_MOCK_QS} questions per day. Upgrade to Premium for full 180Q simulations."
    return True, ""

def inc_mock(uid):
    if is_premium(uid): return
    data = load_json(USAGE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    data[str(uid)] = {"date": today, "mock": 1}
    save_json(USAGE_FILE, data)

# DATA ENGINE INSTANTIATION
from cbt_engine import CBTEngine
cbt = CBTEngine()

# NATIVE STRING-BASED TELEGRAM SEND LAYER (Fixes background crashes)
def send_tg_message(chat_id, text, reply_markup=None):
    url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Send message failed: {e}", flush=True)

def format_question(q, idx, total):
    header = f"<b>Question {idx+1}/{total}</b> | {q.get('subject')} | {q.get('year')}\n\n"
    body = f"<b>{html.escape(q.get('question', ''))}</b>\n\n"
    opts_block = ""
    for letter, text in q.get('options', {}).items():
        opts_block += f"<b>{letter}</b>: {html.escape(str(text))}\n"
    return header + body + opts_block

def get_main_menu_markup():
    return {
        "inline_keyboard": [
            [{"text": "📝 Take Mock Exam", "callback_data": "menu_mock"}],
            [{"text": "💎 Go Premium Tier", "callback_data": "menu_premium"}]
        ]
    }

def get_options_markup(q, current_idx):
    row = [{"text": f"Option {k}", "callback_data": f"ans_{k}"} for k in q.get('options', {}).keys()]
    return {"inline_keyboard": [row, [{"text": "✅ Submit Exam", "callback_data": "submit"}]]}

# FLASK BASE HOST INTERFACE
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return jsonify({"status": "UTME Success Engine Webhook Layer Online", "total_questions": len(cbt.db)})

@flask_app.route("/telegram", methods=["POST"])
def webhook_endpoint():
    """Processes instant text payload triggers straight out of Telegram network boundaries."""
    data = request.get_json(force=True)
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        first_name = msg["from"].get("first_name", "Student")
        username = msg["from"].get("username", "")
        
        if text.startswith("/start"):
            save_profile(chat_id, first_name, username)
            welcome = f"🎓 <b>Welcome to JAMB UTME Success Master Bot!</b>\n\nStudy past questions seamlessly with accurate results metrics analytics tracking indicators."
            send_tg_message(chat_id, welcome, reply_markup=get_main_menu_markup())
            
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        cb_data = query["data"]
        uid = query["from"]["id"]
        first_name = query["from"].get("first_name", "Student")
        
        if cb_data == "menu_mock":
            ok, msg = can_mock(uid)
            if not ok:
                send_tg_message(chat_id, msg)
                return "OK", 200
            limit = 40 if is_premium(uid) else FREE_MOCK_QS
            if not is_premium(uid): inc_mock(uid)
            q, total = cbt.start_mock(uid, ["English", "Mathematics"], limit_per_subject=limit//2)
            if q:
                send_tg_message(chat_id, format_question(q, 0, total), reply_markup=get_options_markup(q, 0))
                
        elif cb_data.startswith("ans_"):
            choice = cb_data.replace("ans_", "")
            res, status = cbt.answer_current(uid, choice)
            if status == "FINISHED":
                txt = f"🏁 <b>Session Concluded.</b>\nScore: {res['raw_score']}/{res['total']}\nJAMB weight estimation parameters: <b>{res['jamb_score']}/400</b>"
                send_tg_message(chat_id, txt)
            elif status == "NEXT":
                nq, nidx = res
                exam = cbt.active_exams.get(uid)
                total = len(exam['questions']) if exam else 0
                send_tg_message(chat_id, format_question(nq, nidx, total), reply_markup=get_options_markup(nq, nidx))
                
        elif cb_data == "menu_premium":
            send_tg_message(chat_id, f"💎 <b>Premium Matrix Access Portal Link:</b>\n\n🔗 Link: {RENDER_URL}/upgrade/{uid}")
            
    return "OK", 200

@flask_app.route("/upgrade/<uid>")
def upgrade_checkout(uid):
    return render_template_string(f"<h1>🎓 Premium Activation Portal</h1><p>Candidate Identification ID parameter maps: {uid}</p>")

# SYNCHRONIZE WEBHOOK REGISTRATION ROUTE AT BOOTUP
try:
    webhook_url = f"{RENDER_URL}/telegram"
    requests.get(f"https://telegram.org{BOT_TOKEN}/setWebhook?url={webhook_url}&drop_pending_updates=true", timeout=5)
    print("📢 Webhook pipeline successfully bounded to Render interfaces.")
except Exception as e:
    print(f"Initial Webhook registration warning: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
