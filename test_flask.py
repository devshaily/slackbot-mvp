
from flask import Flask, jsonify

flask_app = Flask(__name__)

@flask_app.get("/")
def home():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=8000)
