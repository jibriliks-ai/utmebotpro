import os
from webhook_server import app
port = int(os.getenv("PORT", 10000))
print(f"Starting Flask on {port}")
app.run(host="0.0.0.0", port=port)
