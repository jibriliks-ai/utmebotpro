"""
UTME BOT - ALL IN ONE FILE
Combines: config + cbt_engine + payment + webhook_server + main_bot + run
StartCommand: python main.py
"""
import os
import sys
import json
import time
import uuid
import random
import threading
import sqlite3
from collections import defaultdict

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=== UTME Bot Starting (ALL-IN-ONE) ===")
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utmebot12345")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)} len {len(BOT_TOKEN) if BOT_TOKEN else 0}")
print(f"FLW keys exist: {bool(FLW_SECRET_KEY)}")
print(f"CWD: {os.getcwd()} Files: {os.listdir('.')[:20]}")

# Try to list utme-bot subfolder too
try:
    if os.path.exists('./utme-bot'):
        print(f"utme-bot/ files: {os.listdir('./utme-bot')[:20]}")
except:
    pass

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","CRS","Commerce"]

# ===== PAYMENT DB =====
DB_FILE = "premium_users.json"
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
def save_db(db):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"save_db error: {e}")
def is_premium(user_id):
    db = load_db()
    ud = db.get(str(user_id))
    if not ud: return False
    return time.time() < ud.get("expiry", 0)
def get_premium_info(user_id):
    return load_db().get(str(user_id))
def grant_premium(user_id, days=30, tx_ref=None, email=None):
    db = load_db()
    expiry = time.time() + (days*24*60*60)
    existing = db.get(str(user_id))
    if existing and existing.get("expiry",0) > time.time():
        expiry = existing["expiry"] + (days*24*60*60)
    db[str(user_id)] = {
        "user_id": user_id,
        "expiry": expiry,
        "expiry_date": time.strftime("%Y-%m-%d", time.localtime(expiry)),
        "tx_ref": tx_ref,
        "email": email,
        "granted_at": time.time()
    }
    save_db(db)
    print(f"Granted premium to {user_id} until {db[str(user_id)]['expiry_date']}")
    return expiry
def create_flutterwave_link(user_id, email="user@example.com", name="UTME Student"):
    if not FLW_SECRET_KEY:
        return None, "FLW_SECRET_KEY not set"
    import requests
    tx_ref = f"utme-{user_id}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "tx_ref": tx_ref,
        "amount": PREMIUM_PRICE,
        "currency": "NGN",
        "redirect_url": "https://t.me/utmebot",
        "payment_options": "card,banktransfer,ussd",
        "customer": {"email": email, "name": name},
        "customizations": {"title": "UTME Success Bot Premium", "description": f"30 days unlimited - {PREMIUM_PRICE} NGN", "logo": "https://cdn-icons-png.flaticon.com/512/2232/2232688.png"},
        "meta": {"user_id": str(user_id), "bot": "utme_success"}
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        data = res.json()
        if data.get("status") == "success":
            return data["data"]["link"], tx_ref
        else:
            print(f"FLW Error: {data}")
            return None, str(data)
    except Exception as e:
        print(f"FLW Exception: {e}")
        return None, str(e)
def verify_by_tx_ref(tx_ref):
    if not FLW_SECRET_KEY:
        return False, "No secret key"
    import requests
    url = f"https://api.flutterwave.com/v3/transactions?tx_ref={tx_ref}"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        if data.get("status") == "success" and data.get("data"):
            txn = data["data"][0] if isinstance(data["data"], list) else data["data"]
            if txn.get("status") == "successful":
                return True, txn
        return False, data
    except Exception as e:
        return False, str(e)

# ===== CBT ENGINE =====
class CBTEngine:
    def __init__(self, db_path="questions.db"):
        self.use_sqlite = os.path.exists(db_path)
        self.db_path = db_path
        self.json_path = "questions.json"
        # also check subfolder
        if not os.path.exists(self.json_path) and os.path.exists(f"./utme-bot/{self.json_path}"):
            self.json_path = f"./utme-bot/{self.json_path}"
        self.db = []
        if self.use_sqlite:
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM questions")
                count = c.fetchone()[0]
                print(f"Loaded {count} from SQLite")
                conn.close()
            except:
                self.use_sqlite=False
        if not self.use_sqlite:
            if os.path.exists(self.json_path):
                try:
                    with open(self.json_path,'r',encoding='utf-8') as jf:
                        self.db=json.load(jf)
                    print(f"Loaded {len(self.db)} from JSON {self.json_path}")
                except Exception as e:
                    print(f"JSON load error: {e}")
                    self.db=[]
            if not self.db:
                print("No DB, using dummy")
                self.db=[{"id":1,"subject":"Biology","year":2020,"topic":"General","question":"What is biology?","options":{"A":"Study of life","B":"Study of rocks","C":"Study of stars","D":"Study of metals"},"answer":"A","explanation":"Biology is study of life","examType":"utme"}]
        self.active_exams={}
        self.user_stats=defaultdict(lambda: {"total_attempted":0,"total_correct":0,"by_subject":{}})
    def get_questions(self, subject=None, year=None, topic=None, limit=40):
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q['subject'].lower()==subject.lower()]
        random.shuffle(filtered)
        return filtered[:limit] if filtered else self.db[:limit]
    def start_mock(self, user_id, subjects, duration=45*60):
        all_selected=[]
        per_subject=40 if len(subjects)==1 else 10
        for subj in subjects:
            qs=self.get_questions(subject=subj, limit=per_subject)
            all_selected.extend(qs)
        if not all_selected:
            all_selected=self.db[:10]
        random.shuffle(all_selected)
        self.active_exams[user_id]={"questions":all_selected,"current_idx":0,"score":0,"answers":{},"subjects":subjects,"start_time":time.time(),"duration":duration,"finished":False}
        return all_selected[0], len(all_selected)
    def get_current_question(self, user_id):
        exam=self.active_exams.get(user_id)
        if not exam: return None,0
        idx=exam['current_idx']
        if idx>=len(exam['questions']): return None,idx
        return exam['questions'][idx],idx
    def answer_current(self, user_id, option_letter):
        exam=self.active_exams.get(user_id)
        if not exam or exam['finished']: return None,"NO_EXAM"
        idx=exam['current_idx']
        q=exam['questions'][idx]
        is_correct=(option_letter.upper()==q['answer'].upper())
        exam['answers'][idx]={"user":option_letter.upper(),"correct":is_correct,"q":q}
        if is_correct: exam['score']+=1
        exam['current_idx']+=1
        if exam['current_idx']>=len(exam['questions']):
            return self.finish_exam(user_id),"FINISHED"
        next_q,next_idx=self.get_current_question(user_id)
        return (next_q,next_idx),"NEXT"
    def finish_exam(self, user_id):
        exam=self.active_exams.pop(user_id,None)
        if not exam: return None
        total=len(exam['questions'])
        score=exam['score']
        jamb=int((score/total)*400) if total else 0
        breakdown=defaultdict(lambda: {"score":0,"total":0})
        for idx,q in enumerate(exam['questions']):
            subj=q['subject']
            breakdown[subj]["total"]+=1
            ans=exam['answers'].get(idx)
            if ans and ans['correct']: breakdown[subj]["score"]+=1
        result={"raw_score":score,"total":total,"jamb_score":jamb,"breakdown":dict(breakdown),"answers":exam['answers'],"questions":exam['questions'],"subjects":exam['subjects']}
        self.active_exams[f"{user_id}_last"]=result
        return result
    def get_time_left(self,user_id):
        exam=self.active_exams.get(user_id)
        if not exam: return 0
        elapsed=time.time()-exam['start_time']
        return max(0,int(exam['duration']-elapsed))

# Init CBT
try:
    cbt = CBTEngine()
    print("CBT Engine OK")
except Exception as e:
    print(f"CBT failed: {e}")
    cbt = None

# ===== FLASK WEBHOOK =====
from flask import Flask, request, jsonify
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return f"🎓 UTME Bot LIVE - BotToken:{bool(BOT_TOKEN)} CBT:{len(cbt.db) if cbt else 0} Qs - /health - /flw-webhook"

@flask_app.route("/health")
def health():
    db = load_db()
    return jsonify({"status":"ok","premium_users":len(db),"bot_token_exists":bool(BOT_TOKEN),"cbt_questions":len(cbt.db) if cbt else 0,"url":"https://utmebot.onrender.com","hash":FLW_SECRET_HASH})

@flask_app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    sig = request.headers.get("verif-hash") or request.headers.get("Verif-Hash") or ""
    print(f"Webhook sig {sig} expected {FLW_SECRET_HASH}")
    data = request.json or {}
    print(f"Body: {str(data)[:500]}")
    try:
        event = data.get("event")
        txn = data.get("data", {})
        if event == "charge.completed" and txn.get("status") == "successful":
            tx_ref = txn.get("tx_ref","")
            if tx_ref.startswith("utme-"):
                uid = int(tx_ref.split("-")[1])
                email = txn.get("customer",{}).get("email","")
                grant_premium(uid, days=30, tx_ref=tx_ref, email=email)
                print(f"Premium granted to {uid}")
                return jsonify({"status":"granted","user_id":uid}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback; traceback.print_exc()
    return jsonify({"status":"ignored"}), 200

# ===== TELEGRAM BOT =====
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode
    TG_AVAILABLE = True
except Exception as e:
    print(f"telegram import failed: {e}")
    TG_AVAILABLE = False

FREE_EXPLAIN_LIMIT = 3

def format_question(q, idx, total, time_left=None):
    time_str = f"⏱ {time_left//60}:{time_left%60:02d} | " if time_left else ""
    header = f"📝 Q{idx+1}/{total} | {q['subject']} {q.get('year','')} {time_str}\n\n"
    body = f"<b>{q['question']}</b>\n\n"
    opts = "\n".join([f"<b>{k}</b>: {v}" for k,v in q['options'].items()])
    return header + body + opts

def get_options_keyboard(q, current_idx):
    row = [InlineKeyboardButton(f"{k}", callback_data=f"ans_{k}") for k in q['options'].keys()]
    nav_row = [InlineKeyboardButton("⬅️ Prev", callback_data="nav_prev"), InlineKeyboardButton("➡️ Next", callback_data="nav_next"), InlineKeyboardButton("🏁 Submit", callback_data="submit")]
    explain_row = [InlineKeyboardButton("🧠 Explain", callback_data=f"explain_{current_idx}")]
    return InlineKeyboardMarkup([row, nav_row, explain_row])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    prem = is_premium(uid)
    status = "💎 PREMIUM" if prem else f"🆓 FREE (N{PREMIUM_PRICE})"
    welcome = f"🎓 *UTME SUCCESS BOT* 🎓\n{status}\n\nCommands:\n/mock - Full mock\n/practice - One subject\n/subscribe - Premium\n\nBot is LIVE and responding!"
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_premium(uid):
        await update.message.reply_text("💎 Already PREMIUM!")
        return
    await update.message.reply_text(f"💳 Premium N{PREMIUM_PRICE}/30 days\nSend your email:", parse_mode=ParseMode.MARKDOWN)
    context.user_data["awaiting_email"] = True

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_email"): return
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("❌ Invalid email")
        return
    uid = update.effective_user.id
    name = update.effective_user.full_name
    await update.message.reply_text("⏳ Creating payment link...")
    link, tx_ref = create_flutterwave_link(uid, email=email, name=name)
    if not link:
        await update.message.reply_text(f"❌ Could not create link: {tx_ref}")
        return
    context.user_data["awaiting_email"] = False
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Pay N{PREMIUM_PRICE}", url=link)],[InlineKeyboardButton("✅ Verify", callback_data=f"verify_{tx_ref}")]])
    await update.message.reply_text(f"🔗 Pay N{PREMIUM_PRICE}:\nAfter pay click Verify\nTx: {tx_ref}", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    if data.startswith("verify_"):
        tx_ref = data.replace("verify_","")
        await query.message.reply_text("🔍 Verifying...")
        success,_ = verify_by_tx_ref(tx_ref)
        if success:
            grant_premium(uid,30,tx_ref)
            await query.message.reply_text("✅ Payment Confirmed! PREMIUM 30 days")
        else:
            await query.message.reply_text(f"❌ Not yet. Tx: {tx_ref}")
        return
    if cbt is None:
        await query.message.reply_text("⚠️ DB not loaded")
        return
    if data.startswith("combo_"):
        subs = ["English","Mathematics","Biology","Chemistry"] if "science" in data else ["English","Literature","Government","CRS"]
        try:
            q,total = cbt.start_mock(uid, subs, duration=120*60)
            await query.message.reply_text(f"🔥 Mock {','.join(subs)} - {total} Qs", parse_mode=ParseMode.MARKDOWN)
            left = cbt.get_time_left(uid)
            await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.message.reply_text(f"Error: {e}")
        return
    elif data.startswith("prac_"):
        subj = data.replace("prac_","")
        try:
            q,total = cbt.start_mock(uid, [subj], duration=45*60)
            left = cbt.get_time_left(uid)
            await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.message.reply_text(f"Error: {e}")
        return
    elif data.startswith("ans_"):
        opt = data.replace("ans_","")
        try:
            result,status = cbt.answer_current(uid, opt)
            if status == "NO_EXAM":
                await query.message.reply_text("No exam. /mock")
                return
            if status == "FINISHED":
                txt = f"🏁 Finished! Score: {result['raw_score']}/{result['total']} JAMB: {result['jamb_score']}/400"
                await query.message.reply_text(txt)
            else:
                next_q,next_idx = result
                left = cbt.get_time_left(uid)
                total = len(cbt.active_exams[uid]['questions'])
                await query.message.reply_text(format_question(next_q,next_idx,total,left), reply_markup=get_options_keyboard(next_q,next_idx), parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.message.reply_text(f"Error: {e}")
    elif data.startswith("nav_"):
        exam = cbt.active_exams.get(uid)
        if not exam: return
        if data=="nav_prev": exam['current_idx']=max(0,exam['current_idx']-1)
        else: exam['current_idx']=min(len(exam['questions'])-1,exam['current_idx']+1)
        q,idx = cbt.get_current_question(uid)
        left=cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,idx,len(exam['questions']),left), reply_markup=get_options_keyboard(q,idx), parse_mode=ParseMode.HTML)
    elif data=="submit":
        final=cbt.finish_exam(uid)
        if final: await query.message.reply_text(f"🏁 Submitted! {final['raw_score']}/{final['total']} JAMB: {final['jamb_score']}/400")
    elif data.startswith("explain_"):
        if not is_premium(uid):
            await query.message.reply_text(f"🚫 Free limit. /subscribe N{PREMIUM_PRICE}")
            return
        await query.message.reply_text("🧠 Explanation feature coming soon")

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb=[[InlineKeyboardButton("🔬 Science", callback_data="combo_science")],[InlineKeyboardButton("🎨 Art", callback_data="combo_art")]]
    await update.message.reply_text("Choose:", reply_markup=InlineKeyboardMarkup(kb))
async def practice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons=[[InlineKeyboardButton(s, callback_data=f"prac_{s}")] for s in SUBJECTS[:8]]
    await update.message.reply_text("Select subject:", reply_markup=InlineKeyboardMarkup(buttons))

def start_telegram_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set - bot cannot start")
        return
    if not TG_AVAILABLE:
        print("❌ telegram library not available")
        return
    print(f"BOT_TOKEN found: {BOT_TOKEN[:5]}... len {len(BOT_TOKEN)}")
    try:
        import requests
        print("Deleting webhook...")
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=15)
        print(f"DeleteWebhook: {r.text[:200]}")
    except Exception as e:
        print(f"DeleteWebhook failed: {e}")
    print("Building Application...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("mock", mock_cmd))
    app.add_handler(CommandHandler("practice", practice_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    print("✅ Handlers registered")
    print("UTME Bot polling started... send /start now!")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message","callback_query"])

# ===== MAIN ENTRY =====
if __name__ == "__main__":
    # Start bot in thread
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread started")
    port = int(os.getenv("PORT", 10000))
    print(f"Binding Flask to 0.0.0.0:{port}")
    print(f"Routes: /, /health, /flw-webhook")
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
