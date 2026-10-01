
"""
run.py - Professional Entry Point
Runs both Telegram bot (main.py) and payment server (webhook_server.py) together on Render
"""
import os, threading, time

print("🚀 UTME Success Bot v17 FINAL - Starting...")

# Start webhook server in background thread
def start_webhook():
    try:
        from webhook_server import app
        port = int(os.environ.get("PORT", 5000))
        print(f"💳 Payment server (Flutterwave + Paystack) starting on port {port}")
        app.run(host="0.0.0.0", port=port, use_reloader=False)
    except Exception as e:
        print(f"Webhook server error: {e}")
        # Fallback to main.py flask if webhook_server fails
        try:
            from main import flask_app
            port = int(os.environ.get("PORT", 5000))
            flask_app.run(host="0.0.0.0", port=port)
        except:
            pass

# Start bot in main thread
def start_bot():
    try:
        from main import main as bot_main
        print("🤖 Telegram Bot starting...")
        bot_main()
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # On Render, PORT is taken by web server, so we need both
    if os.getenv("RENDER"):
        # Web server in background, bot in foreground (Render expects web server on PORT)
        threading.Thread(target=start_bot, daemon=True).start()
        start_webhook()
    else:
        # Local: bot only, or both
        threading.Thread(target=start_webhook, daemon=True).start()
        time.sleep(2)
        start_bot()
