import os
print("🚀 UTME Bot v17.4 FINAL - Blue MENU + Fallback Qs - Advertising Ready")
print(f"BOT_TOKEN set: {bool(os.getenv('BOT_TOKEN'))} | ALOC set: {bool(os.getenv('ALOC_ACCESS_TOKEN'))} | PORT={os.getenv('PORT','5000')}")
try:
    from main import main
    main()
except Exception as e:
    print(f"❌ Failed to start: {e}")
    import traceback
    traceback.print_exc()
    from flask import Flask
    app = Flask(__name__)
    @app.route("/")
    def home():
        return f"Bot failed: {e}. Check BOT_TOKEN env var."
    @app.route("/health")
    def health():
        return {"status": "error", "error": str(e)}
    port = int(os.environ.get("PORT", 5000))
    print(f"Fallback Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
