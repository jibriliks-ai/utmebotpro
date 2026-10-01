import os
import sys
import html
import requests
from flask import Flask, request, jsonify, render_template_string

# Instant Traceback Fallback Setup
print("=== PRODUCTION APPLICATION INGESTION LOOP INITIATED ===", flush=True)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Dotenv optional block bypassed: {e}", flush=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
RENDER_RAW = os.getenv("RENDER_EXTERNAL_URL", "https://onrender.com")
RENDER_URL = RENDER_RAW.strip().rstrip("/").replace("://", ".onrender.com")
if not RENDER_URL.startswith("http"):
    RENDER_URL = "https://" + RENDER_URL

print(f"VERIFYING ENVIRONMENT PARAMETERS: TOKEN_PRESENT={bool(BOT_TOKEN)} URL={RENDER_URL}", flush=True)

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

# INLINE STORAGE DICTIONARY SUITE
ACTIVE_EXAMS = {}

# FLASK BACKEND ENGINE
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({"status": "UTME Bot Engine Active", "mode": "Production Gunicorn Webhook Layer"})

@flask_app.route("/telegram", methods=["POST"])
def webhook_endpoint():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"JSON Ingestion Error: {e}", flush=True)
        return "OK", 200
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        
        if text.startswith("/start"):
            welcome = "🎓 <b>Welcome to JAMB UTME Success Master Bot Pro!</b>\n\nTap the option below to kickstart your preparation loops:"
            markup = {
                "inline_keyboard": [[{"text": "📝 Take Mock Exam", "callback_data": "menu_mock"}]]
            }
            send_tg_message(chat_id, welcome, reply_markup=markup)
            
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        cb_data = query["data"]
        uid = query["from"]["id"]
        
        if cb_data == "menu_mock":
            # Direct API Stream Handling Loop
            send_tg_message(chat_id, "⏳ <b>Streaming fresh questions live from the cloud directory archive...</b>")
            qs = fetch_jamb_questions(subject="english", limit=5)
            if qs:
                ACTIVE_EXAMS[str(uid)] = {"questions": qs, "current": 0, "score": 0}
                q = qs[0]
                q_text = f"<b>📝 Question 1/5</b>\n\n{html.escape(q['question'])}\n\n"
                for l, t in q["options"].items():
                    q_text += f"<b>{l}</b>: {html.escape(t)}\n"
                
                row = [{"text": f"Option {k}", "callback_data": f"ans_{k}"} for k in q["options"].keys()]
                markup = {"inline_keyboard": [row]}
                send_tg_message(chat_id, q_text, reply_markup=markup)
            else:
                send_tg_message(chat_id, "⚠️ Network connection delay. Please tap /start to try again shortly.")
                
        elif cb_data.startswith("ans_"):
            choice = cb_data.replace("ans_", "").upper()
            exam = ACTIVE_EXAMS.get(str(uid))
            if exam:
                curr = exam["current"]
                qs = exam["questions"]
                if choice == qs[curr]["answer"]:
                    exam["score"] += 1
                exam["current"] += 1
                
                if exam["current"] >= len(qs):
                    score = exam["score"]
                    send_tg_message(chat_id, f"🏁 <b>Exam Completed!</b>\n\nYour Score: <b>{score}/5</b>\nEstimated JAMB weight score matches: <b>{int((score/5)*400)}/400</b>")
                    ACTIVE_EXAMS.pop(str(uid), None)
                else:
                    n_idx = exam["current"]
                    q = qs[n_idx]
                    q_text = f"<b>📝 Question {n_idx+1}/5</b>\n\n{html.escape(q['question'])}\n\n"
                    for l, t in q["options"].items():
                        q_text += f"<b>{l}</b>: {html.escape(t)}\n"
                    row = [{"text": f"Option {k}", "callback_data": f"ans_{k}"} for k in q["options"].keys()]
                    markup = {"inline_keyboard": [row]}
                    send_tg_message(chat_id, q_text, reply_markup=markup)
                    
    return "OK", 200

def send_tg_message(chat_id, text, reply_markup=None):
    if not BOT_TOKEN: return
    url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: requests.post(url, json=payload, timeout=8)
    except Exception as e: print(f"Telegram Post Timeout: {e}", flush=True)

def fetch_jamb_questions(subject="english", limit=5):
    url = f"https://aloc.ng{subject.lower().strip()}&limit={limit}"
    headers = {"Accept": "application/json", "X-Public-Key": "anon_public_key_utme_success_bot_2026"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            raw = r.json().get("data", [])
            clean = []
            for item in raw:
                opts = item.get("option", {})
                clean.append({
                    "question": item.get("question", "Question placeholder text."),
                    "options": {
                        "A": opts.get("a", "Option A description"),
                        "B": opts.get("b", "Option B description"),
                        "C": opts.get("c", "Option C description"),
                        "D": opts.get("d", "Option D description")
                    },
                    "answer": str(item.get("answer", "A")).upper().strip()
                })
            return clean
    except Exception as e:
        print(f"API Data Stream Interruption Loop: {e}", flush=True)
    return []

# INITIAL AUTOMATED PIPELINE BINDING
if BOT_TOKEN:
    try:
        target_webhook = f"{RENDER_URL}/telegram"
        requests.get(f"https://telegram.org{BOT_TOKEN}/setWebhook?url={target_webhook}&drop_pending_updates=true", timeout=6)
        print("📢 Webhook pipeline configuration successfully synchronised.", flush=True)
    except Exception as e:
        print(f"Webhook binding warning logged: {e}", flush=True)
