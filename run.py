import os, sys, asyncio, threading, time
print("=== UTME Bot Starting via run.py - Redirecting to main.py v9 CLEAN ===", flush=True)
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(f"✅ Main loop created: {loop}", flush=True)
except Exception as e:
    print(f"Loop setup: {e}", flush=True)
try:
    import main
    def run_flask():
        port = int(os.getenv("PORT", 10000))
        print(f"🌐 Flask starting on 0.0.0.0:{port}", flush=True)
        main.flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    flask_thread = threading.Thread(target=run_flask, daemon=True, name="FlaskThread")
    flask_thread.start()
    print("✅ Flask thread started", flush=True)
    time.sleep(2)
    print("🤖 Starting bot in MAIN THREAD - v9 CLEAN", flush=True)
    main.start_telegram_bot()
except Exception as e:
    print(f"❌ Failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    while True:
        time.sleep(60)
