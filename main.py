"""
UTMEbot - Main entry point
Render runs either:
- Web service: gunicorn app:app  (for upgrade page + webhook)
- Background worker: python main.py (for Telegram bot)

If you have only ONE service on Render, use this main.py to run both web + bot in same process.
"""
import os
import threading
from app import app
from bot import main as bot_main

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # If FLASK_ONLY env is set, run only web
    if os.getenv("FLASK_ONLY") == "1":
        run_flask()
    else:
        # Run bot in main thread (polling), Flask in background thread if needed
        # For Render: Best to have 2 services. This file is for local testing or single service.
        t = threading.Thread(target=run_flask, daemon=True)
        t.start()
        bot_main()