
import os, threading, time
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
    print(f"💳 Flask starting on {port}")
    try:
        from webhook_server import app
        # This must bind quickly
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask error: {e}")
        import traceback; traceback.print_exc()
        while True:
            time.sleep(60)

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread started")
    # Flask in main thread - Render monitors this
    run_flask()
