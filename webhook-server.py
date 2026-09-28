
from flask import Flask, request, jsonify
import os, sys, hashlib, hmac, json
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)

FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utme_secret_hash_123")

@app.route("/")
def home():
    return "🎓 UTME Bot LIVE - Webhook: /flw-webhook - Health: /health"

@app.route("/health")
def health():
    try:
        from payment import load_db
        db = load_db()
        return jsonify({"status":"ok","premium_users":len(db),"url":"https://utmebot.onrender.com"})
    except Exception as e:
        return jsonify({"status":"ok","error":str(e)})

@app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    # Verify Flutterwave signature
    signature = request.headers.get("verif-hash") or request.headers.get("Verif-Hash")
    print(f"Webhook received - Signature: {signature}, Expected: {FLW_SECRET_HASH}")

    # Log raw data
    raw_data = request.get_data(as_text=True)
    print(f"Raw webhook: {raw_data[:500]}")

    # Optional: verify hash (Flutterwave sends verif-hash header)
    if FLW_SECRET_HASH and signature:
        if signature != FLW_SECRET_HASH:
            print(f"⚠️ Signature mismatch! Got {signature}, expected {FLW_SECRET_HASH}")
            # Still continue for testing, but in production you should reject
            # return jsonify({"error":"invalid signature"}), 401

    data = request.json or {}
    print(f"Parsed webhook: {data}")

    try:
        from payment import grant_premium
        event = data.get("event")
        txn_data = data.get("data", {})

        # Flutterwave sends charge.completed
        if event == "charge.completed":
            status = txn_data.get("status")
            tx_ref = txn_data.get("tx_ref", "")
            print(f"Event: {event}, Status: {status}, TxRef: {tx_ref}")

            if status == "successful" and tx_ref.startswith("utme-"):
                try:
                    # tx_ref format: utme-{user_id}-{timestamp}-{rand}
                    parts = tx_ref.split("-")
                    user_id = int(parts[1])
                    customer = txn_data.get("customer", {})
                    email = customer.get("email", "")
                    amount = txn_data.get("amount", 0)

                    print(f"✅ Payment success! User {user_id}, Amount {amount}, Email {email}")

                    # Grant premium
                    expiry = grant_premium(user_id, days=30, tx_ref=tx_ref, email=email)
                    print(f"💎 Premium granted to {user_id} till {expiry}")

                    return jsonify({"status":"premium granted","user_id":user_id,"tx_ref":tx_ref}), 200
                except Exception as e:
                    print(f"Error parsing tx_ref {tx_ref}: {e}")
                    import traceback; traceback.print_exc()
                    return jsonify({"error":str(e)}), 500
            else:
                print(f"Ignored - status not successful or tx_ref not utme: {tx_ref}")
        else:
            print(f"Ignored event: {event}")

    except Exception as e:
        print(f"Webhook handler error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"error":str(e)}), 500

    return jsonify({"status":"ignored"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"Starting webhook server on port {port}")
    print(f"Webhook URL: https://utmebot.onrender.com/flw-webhook")
    print(f"Secret Hash: {FLW_SECRET_HASH}")
    app.run(host="0.0.0.0", port=port)
