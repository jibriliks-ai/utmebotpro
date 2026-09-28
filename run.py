
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__))
print("=== UTME Bot Starting ===")

from dotenv import load_dotenv
load_dotenv()

# Import Flask app from webhook_server
try:
    from webhook_server import app
    print("✅ Flask app loaded from webhook_server.py")
except Exception as e:
    print(f"Failed to import webhook_server: {e}")
    # Fallback minimal app
    from flask import Flask, request, jsonify
    app = Flask(__name__)
    @app.route("/")
    def home(): return "Fallback OK"
    @app.route("/flw-webhook", methods=["POST"])
    def flw(): return jsonify({"status":"fallback"}), 200

def start_bot():
    time.sleep(2)
    print("🤖 Starting Telegram bot...")
    try:
        from main_bot import main
        main()
    except Exception as e:
        print(f"Bot error (Flask still running): {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    print("✅ Bot thread started")
    port = int(os.getenv("PORT", 10000))
    print(f"💳 Binding Flask to 0.0.0.0:{port}")
    print(f"🔗 Webhook URL: https://utmebot.onrender.com/flw-webhook")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
