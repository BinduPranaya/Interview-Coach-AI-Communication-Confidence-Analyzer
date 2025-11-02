import tempfile
import logging
from typing import List, Dict, Union
import os # NEW IMPORT: Needed for manual file deletion

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uvicorn
import librosa
from fastapi.middleware.cors import CORSMiddleware # NEW IMPORT

# ✅ Use official OpenAI Whisper
import whisper

# --- 1. CONFIGURATION AND INITIALIZATION ---

logging.basicConfig(level=logging.INFO)

FILLERS = ["um", "uh", "like", "you know", "so", "actually", "basically"]
POSITIVE_WORDS = ["good", "great", "amazing", "happy", "love", "excellent", "strong", "positive", "best"]
NEGATIVE_WORDS = ["bad", "sad", "angry", "hate", "terrible", "poor", "worst", "negative", "awful"]

app = FastAPI(
    title="Interview Coach AI - Speech Analyzer",
    description="Upload an audio file to get a full speech transcription and analysis report."
)

# --- CORS MIDDLEWARE CONFIGURATION ---
# The origins array ensures the frontend running on 127.0.0.1:8080 (or localhost)
# can successfully connect to the FastAPI backend.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------

# ✅ Load Whisper model globally
try:
    model = whisper.load_model("base")
    logging.info("✅ Whisper 'base' model loaded successfully.")
except Exception as e:
    logging.error(f"❌ Failed to load Whisper model: {e}")
    model = None


# --- 2. Pydantic Models ---

class FillerAnalysis(BaseModel):
    fillers_found: List[str]
    filler_count: int

class ToneAnalysis(BaseModel):
    tone: str
    positive_score: int
    negative_score: int

class PaceAnalysis(BaseModel):
    duration_sec: float
    words: int
    pace_wpm: float

class AnalysisResponse(BaseModel):
    transcription: str
    filler_analysis: FillerAnalysis
    tone_analysis: ToneAnalysis
    pace_analysis: Union[PaceAnalysis, Dict]


# --- 3. CORE FUNCTIONS ---

def speech_to_text(audio_path: str) -> str:
    """Transcribes audio using the Whisper model."""
    if not model:
        raise RuntimeError("Whisper model is not loaded properly.")

    # Using fp16=False for stability, especially on CPUs or older GPUs
    result = model.transcribe(audio_path, fp16=False)
    return result.get("text", "").strip()


def filler_detector(text: str) -> FillerAnalysis:
    """Detects filler words."""
    text_lower = text.lower()
    detected = [word for word in FILLERS if word in text_lower]
    count = sum(text_lower.count(f) for f in FILLERS)
    return FillerAnalysis(fillers_found=detected, filler_count=count)


def tone_analyzer(text: str) -> ToneAnalysis:
    """Performs simple sentiment tone analysis."""
    text_lower = text.lower()
    pos_score = sum(text_lower.count(w) for w in POSITIVE_WORDS)
    neg_score = sum(text_lower.count(w) for w in NEGATIVE_WORDS)

    tone = "Neutral"
    if pos_score > neg_score:
        tone = "Positive"
    elif neg_score > pos_score:
        tone = "Negative"

    return ToneAnalysis(tone=tone, positive_score=pos_score, negative_score=neg_score)


def pace_calculator(audio_path: str, text: str) -> Union[PaceAnalysis, Dict]:
    """Calculates speech pace (Words Per Minute)."""
    try:
        duration = librosa.get_duration(path=audio_path)
        words = len(text.split())
        pace_wpm = round(words / (duration / 60), 2) if duration > 0 else 0

        return PaceAnalysis(
            duration_sec=round(duration, 2),
            words=words,
            pace_wpm=pace_wpm
        )
    except Exception as e:
        logging.error(f"Pace calculation failed: {e}")
        return {"error": str(e)}


# --- 4. API ENDPOINTS ---

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):
    """Main Speech-to-Text and Communication Analyzer."""
    if not model:
        raise HTTPException(status_code=503, detail="Whisper model not available on the server.")

    # FIX: Use NamedTemporaryFile(delete=False) and manually clean up
    # This prevents the file from being deleted immediately after the handle is closed, 
    # ensuring Whisper/Librosa can access it.
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file.filename)
    tmp_path = tmp_file.name
    
    try:
        # Write contents to the temporary file
        contents = await file.read()
        tmp_file.write(contents)
        tmp_file.flush()
        
        # Explicitly close the file handle BEFORE calling external tools (FFmpeg/Whisper/Librosa)
        # This releases the file lock (fixes 'Permission denied')
        tmp_file.close()
        
        logging.info(f"Received: {file.filename}, saved to {tmp_path}")

        # --- Transcribe ---
        text = speech_to_text(tmp_path)

        # --- Analyze ---
        fillers = filler_detector(text)
        tone = tone_analyzer(text)
        pace = pace_calculator(tmp_path, text)

        return AnalysisResponse(
            transcription=text,
            filler_analysis=fillers,
            tone_analysis=tone,
            pace_analysis=pace,
        )
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        # Re-raise as HTTPException for FastAPI to handle
        raise HTTPException(status_code=500, detail=f"Analysis Failed: {str(e)}")
    finally:
        # Manually delete the temporary file on exit, ensuring cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            logging.info(f"Cleaned up temporary file: {tmp_path}")


# --- 5. ENTRY POINT ---

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8080, reload=True)
