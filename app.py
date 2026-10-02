
from flask import Flask, request, jsonify, render_template_string, redirect
import os, json, hmac, hashlib
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

CONFIG_PATH = "config.py"
UPGRADE_HTML_PATH = "upgrade.html"

# Load upgrade html
try:
    with open(UPGRADE_HTML_PATH) as f:
        UPGRADE_HTML = f.read()
except:
    UPGRADE_HTML = "<h1>Upgrade Page</h1>"

USERS_FILE = "users.json"

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
    return "UTMEbot is live! Bot + Upgrade page ready."

@app.route("/upgrade")
def upgrade_page():
    # Inject telegram_id from query if present
    html = UPGRADE_HTML
    # Replace placeholder public key with env if set
    pub_key = os.getenv("FLW_PUBLIC_KEY", "FLWPUBK_TEST-xxxxxxxxxxxxxxxx-X")
    html = html.replace("FLWPUBK_TEST-xxxxxxxxxxxxxxxx-X", pub_key)
    return render_template_string(html)

@app.route("/success")
def success():
    plan = request.args.get("plan","premium")
    return f'''
    <center style="font-family:Arial;padding:40px">
    <h1>✅ Payment Successful!</h1>
    <p>Your {plan} plan is being activated.</p>
    <p>Go back to Telegram bot and type /start to enjoy premium.</p>
    <p>If not activated in 2 mins, send receipt to @UTMESUCCESS</p>
    <a href="https://t.me/UTMEbot">Open Bot</a>
    </center>
    '''

@app.route("/verify-flutterwave")
def verify_flutterwave():
    tx_ref = request.args.get("tx_ref")
    telegram_id = request.args.get("telegram_id")
    secret = os.getenv("FLW_SECRET_KEY")
    if not secret:
        return jsonify({"status":"no_secret_configured, manual verification needed"})
    # Verify transaction
    headers = {"Authorization": f"Bearer {secret}"}
    try:
        r = requests.get(f"https://api.flutterwave.com/v3/transactions?tx_ref={tx_ref}", headers=headers)
        data = r.json()
        if data.get("status")=="success" and data.get("data"):
            # Activate user
            if telegram_id:
                users = load_users()
                uid = str(telegram_id)
                if uid not in users:
                    users[uid] = {}
                # set premium
                plan = "monthly"
                # find amount to determine plan
                amount = 0
                if data["data"]:
                    first = data["data"][0] if isinstance(data["data"], list) else data["data"]
                    amount = first.get("amount",0)
                    if amount >= 6000:
                        plan = "six_months"
                days = 180 if amount >= 6000 or plan=="six_months" else 30
                users[uid]["is_premium"] = True
                users[uid]["premium_until"] = (datetime.now() + timedelta(days=days)).isoformat()
                users[uid]["plan"] = plan
                save_users(users)
            return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","error":str(e)})
    return jsonify({"status":"pending"})

@app.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():
    # Flutterwave webhook verification
    secret_hash = os.getenv("FLW_SECRET_HASH") # set in Flutterwave dashboard
    signature = request.headers.get("verif-hash")
    if secret_hash and signature != secret_hash:
        return jsonify({"status":"invalid hash"}), 401
    
    payload = request.json
    print("Webhook:", payload)
    # payload contains txRef etc.
    data = payload.get("data",{})
    tx_ref = data.get("tx_ref","")
    status = data.get("status")
    meta = data.get("meta",{})
    telegram_id = meta.get("telegram_id") or data.get("meta",{}).get("telegram_id")

    if status == "successful":
        # Extract telegram_id from tx_ref if not in meta: UTMEBOT_timestamp_telegramid
        if not telegram_id and "UTMEBOT_" in tx_ref:
            try:
                telegram_id = tx_ref.split("_")[-1]
            except:
                pass
        if telegram_id:
            users = load_users()
            uid = str(telegram_id)
            if uid not in users:
                users[uid] = {}
            amount = data.get("amount",0)
            plan = "six_months" if amount >= 6000 else "monthly"
            days = 180 if amount >= 6000 or plan=="six_months" else 30
            users[uid]["is_premium"] = True
            users[uid]["premium_until"] = (datetime.now() + timedelta(days=days)).isoformat()
            users[uid]["plan"] = plan
            users[uid]["last_payment_tx"] = tx_ref
            save_users(users)
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
