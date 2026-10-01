import os
import sys
import html
import requests
from flask import Flask, request, jsonify, render_template_string

print("=== UTME BOT CORE PRO MASTER SEED INITIALISED ===", flush=True)

# Strict extraction of your Render configuration variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PREMIUM_PRICE = os.getenv("PREMIUM_PRICE", "2000")
RENDER_RAW = os.getenv("RENDER_EXTERNAL_URL", "").strip()

if not RENDER_RAW:
    RENDER_URL = "https://onrender.com"
else:
    clean_url = RENDER_RAW.replace("http://", "").replace("https://", "").strip("/")
    RENDER_URL = f"https://{clean_url}"

print(f"BOOT PIPELINE VALIDATION: TOKEN_PRESENT={bool(BOT_TOKEN)} HOST_URL={RENDER_URL}", flush=True)

# Inline dictionary data arrays to maintain session progress safely
ACTIVE_EXAMS = {}

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({
        "status": "UTME Bot Engine Active", 
        "mode": "Production Webhook Router",
        "api_sync": "Online"
    })

@flask_app.route("/telegram", methods=["POST"])
def webhook_endpoint():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"Incoming request parsing skip variance: {e}", flush=True)
        return "OK", 200
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        
        if text.startswith("/start"):
            welcome = "🎓 <b>Welcome to JAMB UTME Success Master Bot Pro!</b>\n\nStudy exact past questions from 2010 to 2024 dynamically over the cloud network.\n\nTap the option console below to launch your exam loop:"
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
            send_tg_message(chat_id, "⏳ <b>Streaming authentic questions from the cloud archive network...</b>")
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
                send_tg_message(chat_id, "⚠️ Network latency timeout. Tap /start to retry.")
                
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
                    jamb = int((score / 5) * 400)
                    send_tg_message(chat_id, f"🏁 <b>Mock Session Completed!</b>\n\nScore parameters: {score}/5\nEstimated JAMB Weighted Score: <b>{jamb}/400</b>\n\nType /start to reset dashboards.")
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
    clean_token = BOT_TOKEN.replace("telegram.org", "").strip()
    url = f"https://telegram.org{clean_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: 
        requests.post(url, json=payload, timeout=8)
    except Exception as e: 
        print(f"Telegram execution skip warning: {e}", flush=True)

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
                    "question": item.get("question", "Question context loading..."),
                    "options": {
                        "A": opts.get("a", "Option A choice descriptions"),
                        "B": opts.get("b", "Option B choice descriptions"),
                        "C": opts.get("c", "Option C choice descriptions"),
                        "D": opts.get("d", "Option D choice descriptions")
                    },
                    "answer": str(item.get("answer", "A")).upper().strip()
                })
            return clean
    except Exception as e:
        print(f"API directory ingestion delay loop: {e}", flush=True)
    return []

# AUTO-REGISTER FLUSH HOOK AT CONTAINER INSTANTIATION
if BOT_TOKEN:
    try:
        clean_token = BOT_TOKEN.replace("telegram.org", "").strip()
        target_webhook = f"{RENDER_URL}/telegram"
        r = requests.get(f"https://telegram.org{clean_token}/setWebhook?url={target_webhook}&drop_pending_updates=true", timeout=6)
        print(f"📢 Webhook Registration Status: {r.text}", flush=True)
    except Exception as e:
        print(f"Webhook tracking connection variance: {e}", flush=True)
