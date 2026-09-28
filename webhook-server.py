
from flask import Flask, request, jsonify
import os
app = Flask(__name__)
@app.route("/")
def home(): return "OK LIVE"
@app.route("/flw-webhook", methods=["POST"])
def flw_webhook(): return jsonify({"status":"ok"}), 200
@app.route("/health")
def health(): return jsonify({"status":"ok"})
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
