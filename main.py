from flask import Flask, render_template, request, send_file, jsonify
from modules.tts_service import synthesize_speech
import os
from config import Config
import logging

app = Flask(__name__)
app.config.from_object(Config)

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/speak", methods=["POST"])
def api_speak():
    api_key = request.headers.get("X-API-KEY")
    if api_key != app.config["API_KEY"]:
        logging.warning(f"Unauthorized request from {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    text = data.get("text", "").strip()
    rate = int(data.get("rate", 160))
    fmt = data.get("format", "mp3").lower()

    if not text:
        return jsonify({"error": "Text is required"}), 400

    file_path = synthesize_speech(text, fmt, rate)
    if not os.path.exists(file_path):
        return jsonify({"error": "File generation failed"}), 500

    logging.info(f"TTS generated successfully for: {text[:30]}...")
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
