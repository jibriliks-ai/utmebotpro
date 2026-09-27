
import os, sys, threading, time
# Add current dir and any subfolder to path so imports work
sys.path.insert(0, os.path.dirname(__file__))
# If files are in utme-bot/ subfolder, add that too
for sub in ["utme-bot", "src", "bot", "."]:
    p = os.path.join(os.path.dirname(__file__), sub)
    if os.path.exists(p):
        sys.path.insert(0, p)
        print(f"Added to path: {p} -> files: {os.listdir(p)[:10]}")

print(f"Current dir: {os.getcwd()}")
print(f"Files in cwd: {os.listdir('.')[:15]}")

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}")

def run_bot():
    print("🤖 Starting bot...")
    time.sleep(2)
    try:
        from main_bot import main
        main()
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback; traceback.print_exc()
        while True:
            time.sleep(60)

def run_flask():
    port = int(os.getenv("PORT", 10000))
    print(f"💳 Flask starting on port {port}")
    try:
        from webhook_server import app
        print(f"✅ Flask app imported, binding to {port}")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask error: {e}")
        import traceback; traceback.print_exc()
        while True:
            time.sleep(60)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread started")
    run_flask()
