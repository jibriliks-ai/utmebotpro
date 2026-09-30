import os, asyncio, threading, time
print("=== UTME Bot v10 OVERHAUL via run.py ===", flush=True)
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
except Exception as e:
    print(f"Loop: {e}", flush=True)
try:
    import main
    def run_flask():
        port = int(os.getenv("PORT", 10000))
        print(f"🌐 Flask v10 on 0.0.0.0:{port}", flush=True)
        main.flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    print("🤖 Bot MAIN THREAD v10 OVERHAUL", flush=True)
    main.start_telegram_bot()
except Exception as e:
    print(f"Failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    while True:
        time.sleep(60)
