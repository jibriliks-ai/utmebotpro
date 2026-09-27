from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "OK - UTME Webhook Live - URL works!"

@app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    print(f"Webhook: {request.json}")
    return jsonify({"status":"ok"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
