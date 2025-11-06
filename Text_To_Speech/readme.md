# AI Interview Recorder (FastAPI + CLI)

This project lets you run a simple interview practice tool:

* A **FastAPI backend** that serves questions and accepts audio uploads (API key protected)
* A **CLI client** that speaks questions, records your answers, and uploads them

Works on Windows without a virtual environment. (Optional venv steps are included at the end.)

---

## Prerequisites

* **Python 3.10+** in PATH (`python --version`)
* Microphone access (Windows: allow microphone for apps in Privacy settings)

Project structure:

```
ai-interview-recorder/
├─ server.py
├─ client.py
├─ requirements.txt
├─ data/
│  └─ questions.txt
├─ modules/
│  └─ text_to_speech.py
├─ answers/          # auto-created
└─ logs/             # auto-created
```

---

## One-Time Setup (Windows, no venv)

### 1) Upgrade pip for your user

```powershell
python -m pip install --upgrade --user pip
```

### 2) Install dependencies

```powershell
pip install --user fastapi uvicorn python-multipart requests sounddevice soundfile pyttsx3
```

*(Or if you prefer using the file:)*

```powershell
pip install --user -r requirements.txt
```

---

## Run the Backend (FastAPI Server)

Open **PowerShell in the project folder** and run:

1. Set an API key (choose any long random string):

```powershell
$env:AI_RECORDER_API_KEY="dev-key-1234567890abcdef"
```

2. Start the server:

```powershell
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

3. Test in browser:

* Docs UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Click **Authorize** and enter your key (e.g., `dev-key-1234567890abcdef`)

---

## Run the Client (CLI)

Open a **new PowerShell window** (keep server running) and run:

```powershell
$env:AI_RECORDER_API="http://127.0.0.1:8000"
$env:AI_RECORDER_API_KEY="dev-key-1234567890abcdef"
python client.py
```

**Usage in CLI:**

* `r` → repeat the question (speaks it)
* `rec` → press Enter to **start** recording, press Enter again to **stop**
* `s` → skip question

Outputs:

* Audio files saved to `answers/`
* Server also stores uploads, and `logs/` contains session logs

---

## Optional: Test API with curl (PowerShell)

**GET /questions**

```powershell
curl -H "Authorization: Bearer dev-key-1234567890abcdef" http://127.0.0.1:8000/questions
```

**POST /answers** (upload a WAV)

```powershell
curl -X POST http://127.0.0.1:8000/answers ^
  -H "Authorization: Bearer dev-key-1234567890abcdef" ^
  -F "question_index=1" ^
  -F "file=@answers/q1_123456.wav"
```

**POST /session_logs**

```powershell
curl -X POST http://127.0.0.1:8000/session_logs ^
  -H "Authorization: Bearer dev-key-1234567890abcdef" ^
  -F "filename=session_log.csv" ^
  -F "csv_content=@session_log.csv;type=text/csv"
```

---

## Common Issues & Fixes

**Pip upgrade error `[WinError 5] Access is denied`**
Use `--user` installs:

```powershell
python -m pip install --upgrade --user pip
```

**Upload fails with `422 Unprocessable Entity`**
Make sure server is the updated version that reads form fields (`question_index`, `file`) and you are using `-F` form fields in curl or the provided client.

**No voice / repeat only prints**
`pyttsx3` may be missing or restricted. The client falls back to printing the text. Install voices with `pip install --user pyttsx3` or keep using the fallback.

**Mic not recording**
Check Privacy → Microphone → allow desktop apps. Close apps that might be using the mic.

---

## (Optional) Running with a Virtual Environment

If you later prefer an isolated environment:

```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
$env:AI_RECORDER_API_KEY="dev-key-1234567890abcdef"
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

In a new window for client:

```powershell
./venv/Scripts/Activate.ps1
$env:AI_RECORDER_API="http://127.0.0.1:8000"
$env:AI_RECORDER_API_KEY="dev-key-1234567890abcdef"
python client.py
```

---

## Quick Command Cheat Sheet

**Server (one window):**

```powershell
$env:AI_RECORDER_API_KEY="dev-key-1234567890abcdef"
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Client (new window):**

```powershell
$env:AI_RECORDER_API="http://127.0.0.1:8000"
$env:AI_RECORDER_API_KEY="dev-key-1234567890abcdef"
python client.py
```

**Install (first time only):**

```powershell
python -m pip install --upgrade --user pip
pip install --user -r requirements.txt
```

---

## Notes

* Never commit real API keys or `keys.txt` to Git.
* For teammates on the same LAN, run the server with `--host 0.0.0.0` and share your local IP: set client `AI_RECORDER_API` to `http://<your-ip>:8000`.
* For internet access, use a tunneling tool like `ngrok` and keep the API key enabled.
