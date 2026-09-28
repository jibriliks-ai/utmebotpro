
    import os, sys, threading, time
    sys.path.insert(0, os.path.dirname(__file__))
    print("=== UTME Bot Starting ===")
    print(f"CWD: {os.getcwd()}")
    try:
        files = os.listdir('.')
        print(f"Files: {files[:20]}")
    except Exception as e:
        print(f"List error: {e}")

    from dotenv import load_dotenv
    load_dotenv()

    # DEBUG ENV
    print("=== ENV DEBUG ===")
    all_keys = list(os.environ.keys())
    print(f"All env keys: {all_keys[:30]}")
    # Check variations
    for k in ["BOT_TOKEN", "BOT_TOKEN ", " BOT_TOKEN", "BOT-TOKEN", "BOT_TOKEN
"]:
        if k in os.environ:
            print(f"Found key [{k}] = {os.environ[k][:10]}...")
    bot_token = os.getenv("BOT_TOKEN")
    print(f"BOT_TOKEN exists: {bool(bot_token)}")
    if bot_token:
        print(f"BOT_TOKEN length: {len(bot_token)}, starts with: {bot_token[:6]}...")
        if ":" not in bot_token:
            print("ERROR: BOT_TOKEN format invalid - should contain ':' like 123456:AAH...")
        if " " in bot_token:
            print("ERROR: BOT_TOKEN contains spaces - remove spaces!")
    else:
        print("ERROR: BOT_TOKEN is None/empty - Check Render Environment tab, key must be exactly BOT_TOKEN")

    try:
        from webhook_server import app
        print("✅ Loaded webhook_server.py")
    except Exception as e:
        print(f"webhook_server import failed: {e}")
        from flask import Flask, request, jsonify
        app = Flask(__name__)
        @app.route("/")
        def home(): return "UTME Bot LIVE"
        @app.route("/health")
        def health(): 
            bt = os.getenv("BOT_TOKEN")
            return jsonify({"status":"ok","bot_token_exists":bool(bt),"bot_token_len":len(bt) if bt else 0})
        @app.route("/flw-webhook", methods=["POST"])
        def flw(): return jsonify({"status":"ok"}), 200

    def start_bot():
        time.sleep(2)
        print("🤖 Starting Telegram bot thread...")
        print(f"Thread sees BOT_TOKEN exists: {bool(os.getenv('BOT_TOKEN'))}")
        try:
            # Force re-read env
            import importlib
            import config
            importlib.reload(config)
            print(f"config.BOT_TOKEN exists: {bool(config.BOT_TOKEN)}")
            from main_bot import main
            main()
        except Exception as e:
            print(f"Bot failed: {e}")
            import traceback; traceback.print_exc()
            # Keep thread alive to see logs
            while True:
                time.sleep(60)
                print("Bot thread waiting after failure...")

    if __name__ == "__main__":
        t = threading.Thread(target=start_bot, daemon=False)  # NOT daemon, so logs visible
        t.start()
        print("✅ Bot thread started (non-daemon)")
        port = int(os.getenv("PORT", 10000))
        print(f"💳 Binding Flask to 0.0.0.0:{port}")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
