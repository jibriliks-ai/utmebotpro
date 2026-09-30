import os, sys, asyncio, threading, time

# v8.5 FINAL FIX - run.py now just calls main.py correctly
# This fixes "There is no current event loop in thread 'Thread-1'"

print("=== UTME Bot Starting via run.py - Redirecting to main.py ===", flush=True)

# Ensure event loop in main thread
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(f"✅ Main loop created: {loop}", flush=True)
except Exception as e:
    print(f"Loop setup: {e}", flush=True)

# Import and run main.py directly
try:
    import main
    # If main has start_telegram_bot, call it in main thread with Flask in background
    if hasattr(main, 'flask_app'):
        def run_flask():
            port = int(os.getenv("PORT", 10000))
            print(f"🌐 Flask starting on 0.0.0.0:{port}", flush=True)
            main.flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True, name="FlaskThread")
        flask_thread.start()
        print("✅ Flask thread started", flush=True)
        time.sleep(2)
        print("🤖 Starting bot in MAIN THREAD - Fixes Thread-1 error", flush=True)
        main.start_telegram_bot()
    else:
        print("❌ main.py missing flask_app", flush=True)
except Exception as e:
    print(f"❌ Failed to run main.py: {e}", flush=True)
    import traceback
    traceback.print_exc()
    # Fallback: keep alive
    while True:
        time.sleep(60)
