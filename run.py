
import os, sys
print("=== UTME Bot Starting ===")
print(f"CWD: {os.getcwd()}")
try:
    print(f"Files: {os.listdir('.')[:20]}")
except:
    pass

# Flask app INSIDE run.py - no import needed
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def home():
    return "🎓 UTME Bot LIVE - URL works! Webhook: /flw-webhook"

@app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    data = request.json or {}
    print(f"WEBHOOK: {data}")
    # Lazy import payment only here
    try:
        from payment import grant_premium
        event = data.get("event")
        txn_data = data.get("data", {})
        if event == "charge.completed" and txn_data.get("status") == "successful":
            tx_ref = txn_data.get("tx_ref", "")
            parts = tx_ref.split("-")
            user_id = int(parts[1])
            grant_premium(user_id, days=30, tx_ref=tx_ref, email=txn_data.get("customer",{}).get("email"))
            return jsonify({"status":"granted","user_id":user_id}), 200
    except Exception as e:
        print(f"Webhook error (ignored): {e}")
    return jsonify({"status":"ignored"}), 200

@app.route("/health")
def health():
    return jsonify({"status":"ok"})

# Start Telegram bot in background thread
def start_bot():
    import time, threading
    time.sleep(3)
    print("🤖 Starting Telegram bot thread...")
    try:
        # Add paths
        sys.path.insert(0, os.path.dirname(__file__))
        from main_bot import main
        main()
    except Exception as e:
        print(f"Bot failed (Flask still running): {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    import threading
    # Start bot thread
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    print("✅ Bot thread started, starting Flask...")

    port = int(os.getenv("PORT", 10000))
    print(f"💳 Binding Flask to 0.0.0.0:{port}")
    # This MUST bind - no try/except that hides it
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
