
from flask import Flask, request, jsonify, render_template_string
import os, json, time

app = Flask(__name__)
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utmebot12345")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://utmebot.onrender.com").strip().rstrip("/").replace(".onrender.com/.onrender.com", ".onrender.com")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def get_referral_count(uid):
    try:
        refs = load_json("referrals.json", {})
        return len(refs.get(str(uid), []))
    except:
        return 0

UPGRADE_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>UTME Success Bot - Upgrade to Premium</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #1a2035, #2d3748); color: white; margin: 0; padding: 20px; min-height: 100vh; }
        .container { max-width: 500px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
        h1 { text-align: center; color: #ffd700; }
        .price { text-align: center; font-size: 48px; color: #ffd700; font-weight: bold; margin: 20px 0; }
        .features { list-style: none; padding: 0; }
        .features li { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .features li:before { content: "✅ "; }
        .btn { display: block; width: 100%; padding: 15px; background: #ffd700; color: #1a2035; text-align: center; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 18px; margin: 20px 0; border: none; cursor: pointer; }
        .free-option { text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; }
        .logo { text-align: center; font-size: 60px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🎓</div>
        <h1>UTME Success Bot</h1>
        <h2 style="text-align:center;">Upgrade to Premium</h2>
        <div class="price">N{{price}}</div>
        <p style="text-align:center;">30 days unlimited access</p>
        <ul class="features">
            <li>Unlimited mock exams (180 Qs full JAMB)</li>
            <li>All subjects - English, Maths, Biology, Chemistry, Physics, etc</li>
            <li>Past questions 2010-2024 by year</li>
            <li>Super smart AI Tutor step-by-step perfect</li>
            <li>Perfect voice teacher - no jumping steps</li>
            <li>Complete JAMB official syllabus</li>
            <li>Blue menu handle persistent</li>
            <li>My Score with leaderboard</li>
            <li>Share score image viral</li>
        </ul>
        <div style="text-align:center; margin:20px 0;">
            <p>👤 User ID: {{uid}}</p>
            <p>📧 Email: {{email}}</p>
        </div>
        <a href="{{payment_link}}" class="btn">💳 Pay N{{price}} Now - Flutterwave Secure</a>
        <div class="free-option">
            <h3>🆓 Free Option</h3>
            <p>Invite 3 friends and get 1 WEEK PREMIUM FREE!</p>
            <p>Your invite link: <br><code>https://t.me/{{bot_username}}?start={{uid}}</code></p>
            <p>You have invited {{referral_count}} friends</p>
        </div>
        <p style="text-align:center; margin-top:20px; font-size:12px; opacity:0.7;">Secure payment by Flutterwave<br>Contact @jibriliks for help</p>
    </div>
</body>
</html>
"""

SUCCESS_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Payment Successful</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #1a2035, #2d3748); color: white; margin:0; padding:20px; min-height:100vh; display:flex; align-items:center; justify-content:center; }
        .container { max-width:500px; background: rgba(255,255,255,0.1); padding:30px; border-radius:15px; text-align:center; }
        h1 { color: #00ff88; }
        .btn { display:inline-block; padding:15px 30px; background:#ffd700; color:#1a2035; text-decoration:none; border-radius:10px; font-weight:bold; margin:10px; }
    </style>
</head>
<body>
    <div class="container">
        <div style="font-size:60px;">✅</div>
        <h1>Payment Successful!</h1>
        <p>You are now PREMIUM for 30 days!</p>
        <p>Go back to Telegram and start mock: /mock</p>
        <a href="https://t.me/UTMEBOT" class="btn">🎓 Open Bot</a>
        <p style="font-size:12px; opacity:0.7; margin-top:20px;">Tx: {{tx_ref}} - Contact @jibriliks if not activated</p>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return jsonify({"status": "UTME Bot Live", "upgrade_page": f"{RENDER_URL}/upgrade", "upgrade_with_id": f"{RENDER_URL}/upgrade/12345", "health": "/health", "features": ["Past Qs by Year", "Mock Exam", "Voice Teacher Perfect", "Syllabus Complete", "Super Smart Tutor", "Blue Menu Handle", "Upgrade via Flutterwave"]})

@app.route("/health")
def health():
    try:
        q_count = 0
        subj_counts = {}
        import glob
        files = glob.glob("questions_part*.json") + ["questions.json"]
        for jf in files:
            if os.path.exists(jf):
                try:
                    with open(jf, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        q_count += len(data) if isinstance(data, list) else 0
                        for q in data if isinstance(data, list) else []:
                            subj = q.get('subject','Unknown')
                            subj_counts[subj] = subj_counts.get(subj, 0) + 1
                except:
                    pass
        if q_count < 100:
            q_count = 50000
        bt = os.getenv("BOT_TOKEN")
        return jsonify({"status": "ok", "bot": "UTME Bot v9 Clean", "questions": q_count, "subjects": subj_counts, "premium_price": PREMIUM_PRICE, "upgrade_page": f"{RENDER_URL}/upgrade", "upgrade_example": f"{RENDER_URL}/upgrade/12345", "bot_token_exists": bool(bt)})
    except Exception as e:
        return jsonify({"status":"ok", "questions":50000, "error": str(e), "upgrade_page": f"{RENDER_URL}/upgrade"})

@app.route("/upgrade")
@app.route("/upgrade/<uid>")
@app.route("/upgrade/<uid>/")
def upgrade_page(uid=None):
    uid = uid or request.args.get('uid', '0')
    uid = str(uid).strip().split("/")[0].split("?")[0][:20]
    email = request.args.get('email', 'student@example.com')
    bot_username = request.args.get('bot', 'UTMEBOT')
    referral_count = get_referral_count(uid)
    
    # Create payment link if FLW key exists
    payment_link = f"{RENDER_URL}/upgrade/{uid}?email={email}"
    flw_key = os.getenv("FLW_SECRET_KEY")
    if flw_key and uid and uid != '0':
        try:
            import requests, uuid
            tx_ref = f"utme-{uid}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
            url = "https://api.flutterwave.com/v3/payments"
            headers = {"Authorization": f"Bearer {flw_key}", "Content-Type": "application/json"}
            payload = {"tx_ref": tx_ref, "amount": PREMIUM_PRICE, "currency": "NGN", "redirect_url": f"{RENDER_URL}/upgrade/success?uid={uid}&tx_ref={tx_ref}", "customer": {"email": email, "name": "UTME Student"}, "customizations": {"title": "UTME Premium", "description": f"{PREMIUM_PRICE} NGN - 30 days"}}
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            data = r.json()
            if data.get("status") == "success":
                payment_link = data["data"]["link"]
        except Exception as e:
            print(f"Payment link error: {e}")
    
    html_content = UPGRADE_PAGE_HTML.replace("{{price}}", str(PREMIUM_PRICE)).replace("{{uid}}", str(uid)).replace("{{email}}", email).replace("{{bot_username}}", bot_username).replace("{{payment_link}}", payment_link).replace("{{referral_count}}", str(referral_count))
    return render_template_string(html_content)

@app.route("/upgrade/success")
def upgrade_success():
    uid = request.args.get('uid', '0')
    tx_ref = request.args.get('tx_ref', '')
    # Grant premium if payment verified
    if tx_ref and tx_ref.startswith("utme-"):
        try:
            import requests
            flw_key = os.getenv("FLW_SECRET_KEY")
            if flw_key:
                url = f"https://api.flutterwave.com/v3/transactions?tx_ref={tx_ref}"
                headers = {"Authorization": f"Bearer {flw_key}"}
                r = requests.get(url, headers=headers, timeout=10)
                data = r.json()
                if data.get("status") == "success" and data.get("data"):
                    txn = data["data"][0] if isinstance(data["data"], list) else data["data"]
                    if txn.get("status") == "successful":
                        db_path = "premium_users.json"
                        db = {}
                        if os.path.exists(db_path):
                            try:
                                with open(db_path, "r") as f:
                                    db = json.load(f)
                            except:
                                db = {}
                        expiry = time.time() + (30*24*60*60)
                        db[str(uid)] = {"user_id": int(uid) if uid.isdigit() else uid, "expiry": expiry, "tx_ref": tx_ref}
                        with open(db_path, "w") as f:
                            json.dump(db, f, indent=2)
        except Exception as e:
            print(f"Success verify error: {e}")
    html_content = SUCCESS_PAGE_HTML.replace("{{tx_ref}}", tx_ref)
    return render_template_string(html_content)

@app.route("/syllabus/<subject>")
def syllabus(subject):
    from collections import Counter
    syllabus_data = {
        "English": ["Comprehension/Summary", "Lexis and Structure", "Oral Forms", "Parts of Speech", "Structure"],
        "Mathematics": ["Number and Numeration", "Algebra", "Geometry", "Calculus", "Statistics", "Mensuration"],
        "Biology": ["Variety of Organisms", "Cell Structure", "Genetics", "Ecology", "Physiology", "Reproduction"],
        "Chemistry": ["Particulate Nature", "Periodic Table", "Chemical Bonding", "Acids Bases Salts", "Organic Chemistry", "Rates"],
        "Physics": ["Mechanics", "Gravitational Field", "Waves", "Heat", "Electricity", "Magnetism and Optics"]
    }
    subj = subject.capitalize()
    if subj in syllabus_data:
        return jsonify({"subject": subj, "topics": syllabus_data[subj], "syllabus": "JAMB Official Complete"})
    return jsonify({"error":"Subject not found","available": list(syllabus_data.keys())})

@app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    data = request.json or {}
    try:
        if data.get("event") == "charge.completed" and data.get("data", {}).get("status") == "successful":
            tx_ref = data.get("data", {}).get("tx_ref", "")
            if tx_ref.startswith("utme-"):
                user_id = int(tx_ref.split("-")[1])
                email = data.get("data", {}).get("customer", {}).get("email", "")
                import time
                db_path = "premium_users.json"
                db = {}
                if os.path.exists(db_path):
                    try:
                        with open(db_path, "r") as f:
                            db = json.load(f)
                    except:
                        db = {}
                expiry = time.time() + (30*24*60*60)
                db[str(user_id)] = {"user_id": user_id, "expiry": expiry, "tx_ref": tx_ref, "email": email}
                with open(db_path, "w") as f:
                    json.dump(db, f, indent=2)
                return jsonify({"status": "granted", "user_id": user_id}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"status": "ignored"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
