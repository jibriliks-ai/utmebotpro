import os
import sys
import threading
import time
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
for sub in ['.', 'utme-bot', 'src', 'utme-bot/utme-bot']:
    p = os.path.join(ROOT, sub)
    if os.path.exists(p):
        sys.path.insert(0, os.path.abspath(p))

print("=== UTME Bot Starting ===")
print(f"CWD: {os.getcwd()}")
print(f"ROOT: {ROOT}")
print(f"sys.path: {sys.path[:5]}")

def list_files(path):
    try:
        if os.path.exists(path):
            print(f"Files in {path}: {os.listdir(path)[:40]}")
        else:
            print(f"Dir not exist: {path}")
    except Exception as e:
        print(f"List {path} error: {e}")

list_files('.')
list_files('./utme-bot')
list_files('/opt/render/project/src')
list_files('/opt/render/project/src/utme-bot')

from dotenv import load_dotenv
load_dotenv()

print("=== ENV DEBUG ===")
bot_token = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN exists: {bool(bot_token)}")
if bot_token:
    print(f"BOT_TOKEN len: {len(bot_token)}, starts: {bot_token[:7]}")

def load_module_from_file(name, filename):
    """Load module from file path directly, bypassing import name issues"""
    for search_dir in [ROOT, os.path.join(ROOT, 'utme-bot'), '/opt/render/project/src', '/opt/render/project/src/utme-bot', '.']:
        full_path = os.path.join(search_dir, filename)
        if os.path.exists(full_path):
            print(f"Found {filename} at {full_path}")
            try:
                spec = importlib.util.spec_from_file_location(name, full_path)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
                print(f"Loaded {name} from {full_path}")
                return mod
            except Exception as e:
                print(f"Failed to load {full_path}: {e}")
                import traceback; traceback.print_exc()
    print(f"Could not find {filename} anywhere")
    return None

# Load webhook_server
app = None
ws_mod = load_module_from_file("webhook_server", "webhook_server.py")
if ws_mod and hasattr(ws_mod, 'app'):
    app = ws_mod.app
    print("Loaded webhook_server.py with /health and /flw-webhook")
else:
    print("webhook_server.py not found or no app - using fallback")
    from flask import Flask, request, jsonify
    app = Flask(__name__)
    @app.route("/")
    def home(): return "UTME Bot LIVE - fallback, webhook file missing"
    @app.route("/health")
    def health():
        bt = os.getenv("BOT_TOKEN")
        return jsonify({"status":"ok_fallback","bot_token_exists":bool(bt),"note":"webhook_server.py not found in root - move it to root"})
    @app.route("/flw-webhook", methods=["POST"])
    def flw(): return jsonify({"status":"fallback ok"}), 200

def start_bot():
    time.sleep(2)
    print("Starting bot thread...")
    mod = load_module_from_file("main_bot", "main_bot.py")
    if not mod:
        print("CRITICAL: main_bot.py not found - bot cannot start! Upload main_bot.py to GitHub ROOT (not inside folder)")
        while True:
            time.sleep(60)
            print("Waiting - main_bot.py still missing...")
    try:
        if hasattr(mod, 'main'):
            mod.main()
        else:
            print("main_bot.py has no main() function")
    except Exception as e:
        print(f"Bot thread failed: {e}")
        import traceback; traceback.print_exc()
        while True:
            time.sleep(60)
            print("Bot thread waiting after failure...")

if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    print("Bot thread started")
    port = int(os.getenv("PORT", 10000))
    print(f"Binding Flask to 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
