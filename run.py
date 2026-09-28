
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__))
print("=== UTME Bot Starting ===")
print(f"CWD: {os.getcwd()}")

from dotenv import load_dotenv
load_dotenv()

# Try to import full webhook app
try:
    from webhook_server import app
    print("✅ Loaded webhook_server.py with /health")
except Exception as e:
    print(f"webhook_server import failed: {e}, using fallback with /health")
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "🎓 UTME Bot LIVE - URL works! Webhook: /flw-webhook - Health: /health"

    @app.route("/health")
    def health():
        try:
            from payment import load_db
            db = load_db()
            return jsonify({"status":"ok","premium_users":len(db),"url":"https://utmebot.onrender.com","routes":["/","/health","/flw-webhook"]})
        except Exception as ex:
            return jsonify({"status":"ok","premium_users":0,"error":str(ex),"routes":["/","/health","/flw-webhook"]})

    @app.route("/flw-webhook", methods=["POST"])
    def flw_webhook():
        data = request.json or {}
        print(f"WEBHOOK: {data}")
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
            print(f"Webhook error: {e}")
            import traceback; traceback.print_exc()
        return jsonify({"status":"ignored"}), 200

def start_bot():
    time.sleep(2)
    print("🤖 Starting Telegram bot thread...")
    try:
        from main_bot import main
        main()
    except Exception as e:
        print(f"Bot failed (Flask still running): {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    print("✅ Bot thread started")
    port = int(os.getenv("PORT", 10000))
    print(f"💳 Binding Flask to 0.0.0.0:{port}")
    print(f"Routes: /, /health, /flw-webhook")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
