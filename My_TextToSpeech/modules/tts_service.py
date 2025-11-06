import pyttsx3
import os
import time
from config import Config
from modules.utils import safe_filename


def synthesize_speech(text, fmt="mp3", rate=160):
    """Convert text to speech and save as file"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    filename = f"{safe_filename(text[:20])}_{int(time.time())}.{fmt}"
    filepath = os.path.join(Config.OUTPUT_DIR, filename)

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", 1.0)

    voices = engine.getProperty("voices")
    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)

    engine.save_to_file(text, filepath)
    engine.runAndWait()

    return filepath
