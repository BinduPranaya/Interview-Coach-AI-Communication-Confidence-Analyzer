# client.py
import os
import time
import random
import queue
import threading
import requests
from typing import Optional
import sounddevice as sd
import soundfile as sf

from modules.text_to_speech import speak_text

QUESTIONS_FILE = "data/questions.txt"
ANSWERS_DIR = "answers"

API_URL = os.environ.get("AI_RECORDER_API")  # e.g. "http://127.0.0.1:8000"
CLIENT_API_KEY = os.environ.get("AI_RECORDER_API_KEY")  # must be set if using API

def _auth_headers():
    if not CLIENT_API_KEY:
        return {}
    return {"Authorization": f"Bearer {CLIENT_API_KEY}"}  # or {"x-api-key": CLIENT_API_KEY}

def load_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def fetch_questions_from_api():
    if not API_URL:
        return None
    try:
        resp = requests.get(f"{API_URL.rstrip('/')}/questions", headers=_auth_headers(), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [item["text"] for item in data]
    except Exception as e:
        print("Warning: could not fetch questions from API:", e)
        return None

def ensure_answers_dir():
    os.makedirs(ANSWERS_DIR, exist_ok=True)

def record_answer(filename, samplerate=44100, channels=1):
    q = queue.Queue()
    stop_event = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        q.put(indata.copy())

    def stopper():
        input()  # wait for Enter
        stop_event.set()

    print("\nPress Enter to START recording...")
    input()
    print("Recording... Press Enter to STOP recording.")
    stopper_thread = threading.Thread(target=stopper, daemon=True)
    stopper_thread.start()

    with sf.SoundFile(filename, mode="w", samplerate=samplerate, channels=channels, subtype="PCM_16") as file:
        with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
            while not stop_event.is_set():
                try:
                    data = q.get(timeout=0.1)
                except queue.Empty:
                    continue
                file.write(data)
    print("Saved:", filename)

def ask_and_record(question_idx, question_text):
    timestamp = int(time.time())
    qlabel = f"Question {question_idx}"
    speak_text(f"{qlabel}. {question_text}")
    print(f"\n🧠 {qlabel}: {question_text}\n")

    while True:
        print("Options: [r]epeat question  |  [rec] record answer  |  [s]kip question")
        choice = input("Enter choice (r / rec / s): ").strip().lower()
        if choice == "r":
            speak_text(f"{qlabel}. {question_text}")
        elif choice == "rec":
            ensure_answers_dir()
            filename = os.path.join(ANSWERS_DIR, f"q{question_idx}_{timestamp}.wav")
            record_answer(filename)
            return filename
        elif choice == "s":
            print("Skipped.\n")
            return None
        else:
            print("Invalid choice — try again.")

def upload_answer_to_api(question_index: int, filepath: str, session_id: Optional[str]=None):
    if not API_URL:
        return None
    url = f"{API_URL.rstrip('/')}/answers"
    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f, "audio/wav")}
        data = {"question_index": str(question_index)}
        if session_id:
            data["session_id"] = session_id
        try:
            resp = requests.post(url, headers=_auth_headers(), files=files, data=data, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print("Warning: upload failed:", e)
            return None

def main():
    print("🤖 AI Interview Question Reader (with recording, repeat, shuffle)\n")

    api_questions = fetch_questions_from_api()
    if api_questions:
        questions = api_questions
        print(f"Loaded {len(questions)} questions from API ({API_URL}).\n")
    else:
        if not os.path.exists(QUESTIONS_FILE):
            print(f"Questions file not found: {QUESTIONS_FILE}")
            return
        questions = load_questions(QUESTIONS_FILE)
        if not questions:
            print("No questions found in the file.")
            return

    shuffle_choice = input("Shuffle questions? (y/n) [n]: ").strip().lower()
    if shuffle_choice == "y":
        random.shuffle(questions)
        print("Questions shuffled.\n")

    print("Starting session. You can repeat, record, or skip each question.\n")

    session_log = []
    session_id = str(int(time.time()))

    for i, q in enumerate(questions, start=1):
        ans_file = ask_and_record(i, q)
        if ans_file and API_URL:
            upload_result = upload_answer_to_api(i, ans_file, session_id=session_id)
            print("Upload result:", upload_result)
        session_log.append((i, q, ans_file))
        time.sleep(0.5)

    # Save session log locally
    import csv
    logname = f"session_log_{int(time.time())}.csv"
    with open(logname, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question_index", "question", "answer_file"])
        for row in session_log:
            writer.writerow(row)

    # upload session log to server if API configured
    if API_URL:
        with open(logname, "r", encoding="utf-8") as f:
            csv_text = f.read()
        try:
            resp = requests.post(
                f"{API_URL.rstrip('/')}/session_logs",
                headers=_auth_headers(),
                data={"filename": logname, "csv_content": csv_text},
                timeout=15,
            )
            if resp.ok:
                print("Session log uploaded:", resp.json())
            else:
                print("Session log upload failed:", resp.text)
        except Exception as e:
            print("Warning: session log upload failed:", e)

    print(f"\n✅ Session complete. Answers saved in '{ANSWERS_DIR}' and log in {logname}")

if __name__ == "__main__":
    main()
