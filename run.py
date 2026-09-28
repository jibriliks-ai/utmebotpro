import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))
print("=== UTME Bot Starting ===")
print(f"CWD: {os.getcwd()}")

try:
    files = os.listdir('.')
    print(f"Files in root: {files[:30]}")
except Exception as e:
    print(f"List error: {e}")

from dotenv import load_dotenv
load_dotenv()

print("=== ENV DEBUG ===")
bot_token = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN exists: {bool(bot_token)}")
if bot_token:
    print(f"BOT_TOKEN len: {len(bot_token)}, starts: {bot_token[:7]}")
    if ":" not in bot_token:
        print("ERROR: BOT_TOKEN should contain ':'")
else:
    print("ERROR: BOT_TOKEN missing - set in Render Environment")

try:
    from webhook_server import app
    print("✅ Loaded webhook_server.py")
except Exception as e:
    print(f"webhook_server import failed: {e}")
    import traceback
    traceback.print_exc()
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "UTME Bot LIVE - fallback"

    @app.route("/health")
    def health():
        bt = os.getenv("BOT_TOKEN")
        return jsonify({
            "status": "ok",
            "bot_token_exists": bool(bt),
            "bot_token_len": len(bt) if bt else 0,
            "routes": ["/", "/health", "/flw-webhook"]
        })

    @app.route("/flw-webhook", methods=["POST"])
    def flw():
        return jsonify({"status": "fallback ok"}), 200

def start_bot():
    time.sleep(2)
    print("🤖 Starting bot thread...")
    try:
        from main_bot import main
        main()
    except Exception as e:
        print(f"Bot thread failed: {e}")
        import traceback
        traceback.print_exc()
        while True:
            time.sleep(60)
            print("Bot thread waiting after failure...")

if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    print("✅ Bot thread started")
    port = int(os.getenv("PORT", 10000))
    print(f"Binding Flask to 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
