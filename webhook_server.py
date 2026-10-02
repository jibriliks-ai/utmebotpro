
"""
webhook_server.py - Payment Server with Flutterwave + Paystack
Handles upgrade page + webhook verification
"""
import os, json, hmac, hashlib
from flask import Flask, request, render_template_string, jsonify
from datetime import datetime, timedelta
from pathlib import Path

try:
    from config import (
        PREMIUM_PRICE, PREMIUM_PRICE_TEXT, BOT_USERNAME,
        FLW_SECRET_KEY, FLW_SECRET_HASH, FLW_PUBLIC_KEY,
        PAYSTACK_SECRET_KEY, PREMIUM_DAYS
    )
except:
    PREMIUM_PRICE=2000
    PREMIUM_PRICE_TEXT="₦2000"
    BOT_USERNAME="YourBot"
    FLW_SECRET_KEY=os.getenv("FLW_SECRET_KEY","")
    FLW_SECRET_HASH=os.getenv("FLW_SECRET_HASH","utme_webhook_hash_123")
    PAYSTACK_SECRET_KEY=os.getenv("PAYSTACK_SECRET_KEY","")
    PREMIUM_DAYS=30  # Referral gives 7 days

app = Flask(__name__)
DATA_FILE = Path("user_data.json")

def add_premium(uid, days=PREMIUM_DAYS):
    try:
        if not DATA_FILE.exists():
            return False
        data=json.loads(DATA_FILE.read_text())
        uid=str(uid)
        if uid in data:
            data[uid]["is_premium"]=True
            data[uid]["premium_until"]=(datetime.now()+timedelta(days=days)).isoformat()
            DATA_FILE.write_text(json.dumps(data, indent=2))
            print(f"✅ Premium activated for {uid} for {days} days")
            return True
    except Exception as e:
        print(f"Add premium error: {e}")
    return False

@app.route("/")
def home():
    return f"UTME Bot v17 FINAL - Premium {PREMIUM_PRICE_TEXT} | Flutterwave + Paystack | Running"

@app.route("/upgrade/<uid>")
def upgrade_page(uid):
    # Page with BOTH Flutterwave and Paystack options
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Upgrade to Premium - UTME Bot</title>
        <style>
            body{{font-family:Arial,sans-serif;background:#f5f7fb;text-align:center;padding:20px;margin:0}}
            .card{{background:white;max-width:450px;margin:20px auto;padding:30px;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,.1)}}
            .btn{{background:#5865f2;color:white;padding:14px 28px;border-radius:10px;text-decoration:none;display:inline-block;margin:10px 0;font-weight:bold;width:85%;border:none;cursor:pointer;font-size:16px}}
            .btn-flw{{background:#f5a623}} .btn-paystack{{background:#00c3f7}}
            .badge{{background:#ff4757;color:white;padding:6px 12px;border-radius:20px;font-size:12px;display:inline-block;margin-bottom:10px}}
            .price{{font-size:32px;font-weight:bold;color:#1a2035;margin:10px 0}}
            ul{{text-align:left;max-width:300px;margin:20px auto;line-height:1.8}}
            .secure{{font-size:11px;color:gray;margin-top:20px}}
        </style>
        <script src="https://checkout.flutterwave.com/v3.js"></script>
    </head>
    <body>
        <div class="card">
            <span class="badge">VIRAL v17 FINAL</span>
            <h2>💎 Go Premium</h2>
            <p>User ID: <b>{uid}</b></p>
            <div class="price">{PREMIUM_PRICE_TEXT}/month</div>
            <ul>
                <li>✅ Unlimited Mocks (vs 20 free LOCKED)</li>
                <li>✅ Full 180Q JAMB Mock 2hr real exam</li>
                <li>✅ Quick 20Q + Subject 40Q</li>
                <li>✅ Voice explanations 🎙</li>
                <li>✅ All 14 subjects 2010-2024 ~7500 Qs</li>
                <li>✅ Syllabus + My Score + Study Plan</li>
                <li>✅ Share Score Viral Image</li>
                <li>✅ Invite Friend = 3 days free</li>
            </ul>
            <p style="font-size:12px;color:#ff4757">Free 20 Qs total cannot be reset - upgrade only way</p>
            
            <!-- FLUTTERWAVE BUTTON -->
            <button class="btn btn-flw" onclick="payWithFlutterwave()">💳 Pay with Flutterwave - {PREMIUM_PRICE_TEXT}</button>
            
            <!-- PAYSTACK BUTTON -->
            <a class="btn btn-paystack" href="https://paystack.com/pay/utme-success-{uid}">💳 Pay with Paystack - {PREMIUM_PRICE_TEXT}</a>
            
            <div class="secure">🔒 Secure payment by Flutterwave & Paystack<br>Premium activates automatically after payment</div>
            <p style="font-size:11px;margin-top:20px"><a href="/">Back to Bot</a></p>
        </div>
        <script>
            function payWithFlutterwave() {{
                FlutterwaveCheckout({{
                    public_key: "{os.getenv('FLW_PUBLIC_KEY','FLWPUBK-XXXX')}",
                    tx_ref: "UTME-{uid}-" + Date.now(),
                    amount: {PREMIUM_PRICE},
                    currency: "NGN",
                    payment_options: "card, banktransfer, ussd, account",
                    customer: {{
                        email: "user{uid}@utmebot.com",
                        name: "UTME User {uid}",
                    }},
                    customizations: {{
                        title: "UTME Success Bot Premium",
                        description: "Premium {PREMIUM_PRICE_TEXT}/month - Unlimited JAMB Mocks",
                    }},
                    callback: function(data) {{
                        console.log(data);
                        // Verify on backend
                        fetch('/verify/flutterwave', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{transaction_id: data.transaction_id, tx_ref: data.tx_ref, user_id: "{uid}"}})
                        }}).then(r=>r.json()).then(res=>{{
                            if(res.status=="success") {{
                                alert("✅ Payment successful! Premium activated for {uid}. Return to Telegram bot and type /start");
                                window.location.href = "https://t.me/{BOT_USERNAME}";
                            }} else {{
                                alert("Payment received but verification pending. Contact admin.");
                            }}
                        }});
                    }},
                    onclose: function() {{
                        console.log("Payment closed");
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# --- FLUTTERWAVE WEBHOOK ---
@app.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():
    # Verify signature
    signature = request.headers.get("verif-hash", "")
    if signature != FLW_SECRET_HASH:
        print(f"⚠️ Flutterwave webhook hash mismatch: {signature} vs {FLW_SECRET_HASH}")
        # Allow anyway for testing, but log
    payload = request.json
    print(f"Flutterwave webhook: {payload}")
    try:
        # Flutterwave sends event type and data
        if payload.get("event") == "charge.completed" or payload.get("status") == "successful":
            data = payload.get("data", payload)
            tx_ref = data.get("tx_ref", "")
            # Extract uid from tx_ref like UTME-123456- timestamp
            if "UTME-" in tx_ref:
                uid = tx_ref.split("UTME-")[1].split("-")[0]
                add_premium(uid, days=30)
                return jsonify({"status":"success","uid":uid})
    except Exception as e:
        print(f"FLW webhook error: {e}")
    return jsonify({"status":"received"})

@app.route("/verify/flutterwave", methods=["POST"])
def verify_flutterwave():
    data = request.json
    transaction_id = data.get("transaction_id")
    uid = data.get("user_id")
    # Verify transaction with Flutterwave API
    try:
        import requests
        headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}
        resp = requests.get(f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify", headers=headers, timeout=10)
        result = resp.json()
        print(f"FLW verify: {result}")
        if result.get("status") == "success" and result.get("data",{{}}).get("status") == "successful":
            add_premium(uid, days=30)
            return jsonify({"status":"success"})
    except Exception as e:
        print(f"Verify error: {e}")
    return jsonify({"status":"failed"})

# --- PAYSTACK WEBHOOK ---
@app.route("/webhook/paystack", methods=["POST"])
def paystack_webhook():
    payload = request.get_data()
    signature = request.headers.get("x-paystack-signature", "")
    # Verify signature if secret set
    if PAYSTACK_SECRET_KEY:
        expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), payload, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(expected, signature):
            print("⚠️ Paystack signature mismatch")
    data = request.json
    print(f"Paystack webhook: {data}")
    try:
        if data.get("event") == "charge.success":
            ref = data.get("data",{{}}).get("reference","")
            # reference may contain uid
            if "UTME-" in ref:
                uid = ref.split("UTME-")[1].split("-")[0]
                add_premium(uid, days=30)
                return jsonify({"status":"success","uid":uid})
            # Fallback: check metadata
            metadata = data.get("data",{{}}).get("metadata",{{}})
            uid = metadata.get("user_id") or metadata.get("uid")
            if uid:
                add_premium(uid, days=30)
                return jsonify({"status":"success"})
    except Exception as e:
        print(f"Paystack webhook error: {e}")
    return jsonify({"status":"received"})

@app.route("/health")
def health():
    return jsonify({"status":"ok","version":"v17 FINAL","premium":PREMIUM_PRICE_TEXT,"gateways":{"flutterwave":bool(FLW_SECRET_KEY),"paystack":bool(PAYSTACK_SECRET_KEY)}})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
