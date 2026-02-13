# server.py
import os
import shutil
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel

QUESTIONS_FILE = "data/questions.txt"
ANSWERS_DIR = "answers"
LOGS_DIR = "logs"
os.makedirs(ANSWERS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Accept either x-api-key or Authorization: Bearer <key>
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
auth_header = APIKeyHeader(name="Authorization", auto_error=False)

app = FastAPI(title="AI Interview Recorder API (API key protected)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_allowed_keys() -> List[str]:
    env_key = os.environ.get("AI_RECORDER_API_KEY")
    if env_key:
        return [env_key.strip()]
    if os.path.exists("keys.txt"):
        with open("keys.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


def get_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Security(auth_header),
) -> APIKey:
    provided = None
    if x_api_key:
        provided = x_api_key.strip()
    elif authorization:
        # Accept "Bearer <key>" or raw key
        if authorization.lower().startswith("bearer "):
            provided = authorization.split(" ", 1)[1].strip()
        else:
            provided = authorization.strip()

    allowed = load_allowed_keys()
    if not provided:
        raise HTTPException(status_code=401, detail="Missing API key")
    if provided not in allowed:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return provided


class Question(BaseModel):
    index: int
    text: str


def load_questions() -> List[str]:
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


@app.get("/questions", response_model=List[Question])
def get_questions(api_key: APIKey = Depends(get_api_key)):
    qs = load_questions()
    return [{"index": i + 1, "text": t} for i, t in enumerate(qs)]


@app.get("/questions/{idx}", response_model=Question)
def get_question(idx: int, api_key: APIKey = Depends(get_api_key)):
    qs = load_questions()
    if idx < 1 or idx > len(qs):
        raise HTTPException(status_code=404, detail="Question not found")
    return {"index": idx, "text": qs[idx - 1]}


@app.post("/answers")
async def upload_answer(
    question_index: int = Form(...),
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: APIKey = Depends(get_api_key),
):
    # Validate extension
    if not file.filename.lower().endswith((".wav", ".mp3", ".flac", ".m4a")):
        raise HTTPException(status_code=400, detail="Unsupported audio file type")
    ts = int(time.time())
    sid = session_id or str(uuid.uuid4())[:8]
    safe_name = f"q{question_index}_{sid}_{ts}_{os.path.basename(file.filename)}"
    dest_path = os.path.join(ANSWERS_DIR, safe_name)
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)
    return {
        "saved_as": safe_name,
        "path": dest_path,
        "question_index": question_index,
        "session_id": sid,
        "timestamp": ts,
    }


@app.post("/session_logs")
def upload_session_log(
    filename: str = Form(...),
    csv_content: str = Form(...),
    api_key: APIKey = Depends(get_api_key),
):
    ts = int(time.time())
    safe_name = f"session_log_{ts}_{uuid.uuid4().hex[:6]}.csv"
    path = os.path.join(LOGS_DIR, safe_name)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)
    return {"saved_as": safe_name, "path": path}


@app.get("/session_logs")
def list_session_logs(api_key: APIKey = Depends(get_api_key)):
    files = os.listdir(LOGS_DIR)
    return {"logs": files}


@app.get("/health")
def health():
    return {"status": "ok"}
