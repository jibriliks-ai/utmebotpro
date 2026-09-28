
from flask import Flask, request, jsonify
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utmebot12345")

@app.route("/")
def home():
    return "🎓 UTME Bot LIVE - Webhook: /flw-webhook - Health: /health"

@app.route("/health")
def health():
    try:
        from payment import load_db
        db = load_db()
        return jsonify({"status":"ok","premium_users":len(db),"url":"https://utmebot.onrender.com","hash":FLW_SECRET_HASH})
    except Exception as e:
        return jsonify({"status":"ok","error":str(e),"url":"https://utmebot.onrender.com"})

@app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    signature = request.headers.get("verif-hash") or request.headers.get("Verif-Hash")
    print(f"Signature: {signature}, Expected: {FLW_SECRET_HASH}")
    data = request.json or {}
    print(f"Webhook body: {str(data)[:500]}")
    try:
        from payment import grant_premium
        event = data.get("event")
        txn = data.get("data", {})
        if event == "charge.completed" and txn.get("status") == "successful":
            tx_ref = txn.get("tx_ref","")
            if tx_ref.startswith("utme-"):
                user_id = int(tx_ref.split("-")[1])
                email = txn.get("customer",{}).get("email","")
                grant_premium(user_id, days=30, tx_ref=tx_ref, email=email)
                print(f"Premium granted to {user_id}")
                return jsonify({"status":"granted","user_id":user_id}), 200
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
    return jsonify({"status":"ignored"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
