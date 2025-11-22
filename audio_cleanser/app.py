from flask import Flask, render_template, request, send_from_directory
import os
import librosa
import soundfile as sf

app = Flask(__name__)

OUTPUT_FOLDER = "cleaned_files"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clean_and_normalize(input_path, output_path):
    y, sr = librosa.load(input_path, sr=None)
    y_norm = librosa.util.normalize(y)
    y_clean = librosa.effects.preemphasis(y_norm)
    sf.write(output_path, y_clean, sr)

@app.route("/", methods=["GET", "POST"])
def index():
    cleaned_file = None
    original_file = None
    if request.method == "POST":
        if "audio_file" not in request.files:
            return render_template("index.html", error="No file uploaded")
        file = request.files["audio_file"]
        if file.filename == "":
            return render_template("index.html", error="Please select a file")

        original_file = file.filename
        original_path = os.path.join("static", "uploads", original_file)
        os.makedirs(os.path.dirname(original_path), exist_ok=True)
        file.save(original_path)

        output_filename = "cleaned_" + file.filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        clean_and_normalize(original_path, output_path)
        cleaned_file = output_filename

    return render_template("index.html", cleaned_file=cleaned_file, original_file=original_file)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
