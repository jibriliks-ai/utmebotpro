from flask import Flask, request, jsonify, render_template_string
import os, json
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

UPGRADE_HTML_PATH = "upgrade.html"
USERS_FILE = "users.json"

def load_html():
    try:
        with open(UPGRADE_HTML_PATH) as f:
            html = f.read()
        pub_key = os.getenv("FLW_PUBLIC_KEY", "FLWPUBK_TEST-xxxxxxxxxxxxxxxx-X")
        return html.replace("FLWPUBK_TEST-xxxxxxxxxxxxxxxx-X", pub_key)
    except Exception as e:
        return f"<h1>Upgrade Page Error: {e}</h1>"

def load_users():
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route("/")
def home():
    return jsonify({"status":"ok","service":"UTMEbot","upgrade":"/upgrade"})

@app.route("/upgrade")
def upgrade_page():
    return render_template_string(load_html())

@app.route("/success")
def success():
    plan = request.args.get("plan","premium")
    display = "Monthly (₦2,000)" if plan=="monthly" else "6 Months (₦6,000)"
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>
    body{{font-family:Arial;text-align:center;padding:30px;background:#f0fdf4}}
    .card{{background:white;max-width:420px;margin:auto;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.1)}}
    .btn{{display:inline-block;background:#0066ff;color:white;padding:14px 28px;border-radius:12px;text-decoration:none;font-weight:700;margin-top:15px}}
    </style></head><body><div class='card'>
    <h1>✅ Payment Successful!</h1><p>Your <b>{display}</b> plan is activating.</p>
    <p>Go back to Telegram bot and type <b>/start</b> to enjoy premium.</p>
    <p style='font-size:12px;color:gray'>If not activated in 2 mins, send receipt to @UTMESUCCESS</p>
    <a class='btn' href='https://t.me/UTMEbot'>Open UTMEbot</a>
    </div></body></html>
    """

@app.route("/verify-flutterwave")
def verify_flutterwave():
    tx_ref = request.args.get("tx_ref")
    telegram_id = request.args.get("telegram_id")
    secret = os.getenv("FLW_SECRET_KEY")
    if not secret or not tx_ref:
        return jsonify({"status":"pending"})
    headers = {"Authorization": f"Bearer {secret}"}
    try:
        r = requests.get(f"https://api.flutterwave.com/v3/transactions?tx_ref={tx_ref}", headers=headers, timeout=15)
        j = r.json()
        if j.get("status")=="success" and j.get("data"):
            data_obj = j["data"][0] if isinstance(j["data"], list) else j["data"]
            if data_obj.get("status") in ["successful","success"]:
                activate_user(telegram_id, data_obj.get("amount",0), tx_ref)
                return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","error":str(e)})
    return jsonify({"status":"pending"})

def activate_user(telegram_id, amount, tx_ref):
    if not telegram_id or telegram_id=="GUEST":
        if "UTMEBOT_" in str(tx_ref):
            try:
                telegram_id = str(tx_ref).split("_")[-1]
            except:
                return
    if not telegram_id or telegram_id=="GUEST":
        return
    users = load_users()
    uid = str(telegram_id)
    if uid not in users:
        users[uid] = {}
    plan = "six_months" if float(amount) >= 6000 else "monthly"
    days = 180 if plan=="six_months" else 30
    users[uid]["is_premium"] = True
    users[uid]["premium_until"] = (datetime.now() + timedelta(days=days)).isoformat()
    users[uid]["plan"] = plan
    users[uid]["last_payment_amount"] = amount
    users[uid]["last_payment_tx"] = tx_ref
    users[uid]["last_payment_date"] = datetime.now().isoformat()
    users[uid]["over_limit_attempts"] = 0
    save_users(users)

@app.route("/webhook/flutterwave", methods=["POST"])
def webhook():
    secret_hash = os.getenv("FLW_SECRET_HASH")
    signature = request.headers.get("verif-hash") or request.headers.get("Verif-Hash")
    if secret_hash and signature != secret_hash:
        return jsonify({"status":"invalid hash"}), 401
    payload = request.get_json(silent=True) or {}
    data = payload.get("data",{})
    status = data.get("status")
    tx_ref = data.get("tx_ref","")
    amount = data.get("amount",0)
    meta = data.get("meta",{}) or payload.get("meta",{})
    telegram_id = meta.get("telegram_id")
    if status == "successful":
        activate_user(telegram_id, amount, tx_ref)
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))