"""
UTME SUCCESS BOT - v18 WEBHOOK PRODUCTION PERFECT Build
- Drop polling mechanisms to eliminate background thread asyncio crashes
- Natively process updates via clean webhooks over standard Flask routing ports
- Fixed question matrix layouts and horizontal keyboard button arrays
"""

import os
import json
import time
import uuid
import re
import html
import asyncio
from flask import Flask, request, jsonify, render_template_string, redirect

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=== UTME Bot v18 WEBHOOK ENGINE ACTIVE ===")
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
REFERRAL_FILE = "referrals.json"
PROFILES_FILE = "user_profiles.json"
USAGE_FILE = "free_usage.json"

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
    if not ud: return False
    return time.time() < ud.get("expiry", 0)

def grant_premium(uid, days=30, tx_ref=None):
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

# ===== FREEMIUM TIERS SYSTEM =====
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
    if is_premium(uid): return True, ""
    if get_usage(uid).get("mock", 0) >= FREE_MOCK_PER_DAY:
        return False, f"🚫 Daily Limit: Free mock limited to {FREE_MOCK_QS} questions per day. Upgrade to Premium for full 180Q simulations."
    return True, ""

def inc_mock(uid):
    if is_premium(uid): return
    data = load_json(USAGE_FILE, {})
    ud = data.get(str(uid))
    ud["mock"] = ud.get("mock", 0) + 1
    save_json(USAGE_FILE, data)

def can_tutor(uid):
    if is_premium(uid): return True, ""
    if get_usage(uid).get("tutor", 0) >= FREE_TUTOR_PER_DAY:
        return False, "🚫 AI Tutor free limit reached for today. Upgrade to Premium for unhindered concepts analysis."
    return True, ""

def inc_tutor(uid):
    if is_premium(uid): return
    data = load_json(USAGE_FILE, {})
    ud = data.get(str(uid))
    ud["tutor"] = ud.get("tutor", 0) + 1
    save_json(USAGE_FILE, data)

# CORE DATA ENGINE INSTANTIATION
from cbt_engine import CBTEngine
cbt = CBTEngine()

# TELEGRAM AND FLASK GATEWAYS CONVERGENCE
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

app = Application.builder().token(BOT_TOKEN).build()

def format_question(q, idx, total, time_left=None):
    t_str = f" ⏱️ {time_left//60}:{time_left%60:02d}" if time_left else ""
    header = f"<b>Question {idx+1}/{total}</b> | {q.get('subject')} | {q.get('year')}{t_str}\n\n"
    body = f"<b>{html.escape(q.get('question', ''))}</b>\n\n"
    opts_block = ""
    for letter, text in q.get('options', {}).items():
        opts_block += f"<b>{letter}</b>: {html.escape(str(text))}\n"
    return header + body + opts_block

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Take Mock Exam", callback_data="menu_mock"), InlineKeyboardButton("📚 Past Questions", callback_data="menu_past")],
        [InlineKeyboardButton("💬 Ask AI Tutor", callback_data="menu_tutor"), InlineKeyboardButton("💎 Go Premium Tier", callback_data="menu_premium")]
    ])

def get_options_keyboard(q, current_idx):
    row = [InlineKeyboardButton(f"Option {k}", callback_data=f"ans_{k}") for k in q.get('options', {}).keys()]
    return InlineKeyboardMarkup([row, [InlineKeyboardButton("✅ Submit Exam", callback_data="submit")]])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_profile(uid, update.effective_user)
    await update.message.reply_text(f"🎓 <b>JAMB UTME Success Master Bot Active.</b>\n\nChoose an evaluation suite module from the options dashboard:", reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in cbt.active_exams: return
    ok, err = can_tutor(uid)
    if not ok:
        await update.message.reply_text(err)
        return
    inc_tutor(uid)
    await update.message.reply_text("🧠 *AI Tutor is processing concept blueprints...*")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    
    if data == "menu_mock":
        ok, msg = can_mock(uid)
        if not ok:
            await query.message.reply_text(msg)
            return
        limit = 40 if is_premium(uid) else FREE_MOCK_QS
        if not is_premium(uid): inc_mock(uid)
        q, total = cbt.start_mock(uid, ["English", "Mathematics"], limit_per_subject=limit//2)
        if q:
            await query.message.reply_text(format_question(q, 0, total, 45*60), reply_markup=get_options_keyboard(q, 0), parse_mode=ParseMode.HTML)
        return
    elif data.startswith("ans_"):
        choice = data.replace("ans_", "")
        res, status = cbt.answer_current(uid, choice)
        if status == "FINISHED":
            await query.message.reply_text(f"🏁 <b>Session Concluded.</b>\nScore: {res['raw_score']}/{res['total']}\nJAMB weight estimation parameters: <b>{res['jamb_score']}/400</b>", parse_mode=ParseMode.HTML)
        elif status == "NEXT":
            nq, nidx = res
            exam = cbt.active_exams.get(uid)
            total = len(exam['questions']) if exam else 0
            await query.message.reply_text(format_question(nq, nidx, total, cbt.get_time_left(uid)), reply_markup=get_options_keyboard(nq, nidx), parse_mode=ParseMode.HTML)
        return
    elif data == "menu_premium":
        await query.message.reply_text(f"💎 <b>Premium Matrix Access Portal Link:</b>\n\n🔗 Link: {RENDER_URL}/upgrade/{uid}", parse_mode=ParseMode.HTML)

# REGISTER STANDARD TELEGRAM HOOK HANDLERS
app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# FLASK NATIVE WEBHOOK PROCESSING ROUTER
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return jsonify({"status": "UTME Success Engine Webhook Layer Online"})

@flask_app.route("/telegram", methods=["POST"])
def webhook_endpoint():
    """Natively accepts encrypted json metrics out of Telegram securely."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    update = Update.de_json(request.get_json(force=True), app.bot)
    loop.run_until_complete(app.process_update(update))
    return "OK", 200

@flask_app.route("/upgrade/<uid>")
def upgrade_checkout(uid):
    return render_template_string(f"<h1>🎓 Premium Activation Portal</h1><p>Candidate Identification Token Profile Key parameters maps: {uid}</p>")

if __name__ == "__main__":
    # Bootstraps the webhook endpoint registration cycle during deployment
    async def configure_webhook():
        async with app:
            await app.bot.set_webhook(url=f"{RENDER_URL}/telegram", drop_pending_updates=True)
            print("🔗 Webhook pipeline destination successfully synchronized.")
            
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(configure_webhook())
    
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
