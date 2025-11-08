from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import pyttsx3
import uuid
from typing import Any

# --- Configuration (Integrated) ---
class Config:
    # API_KEY and middleware are now removed for simplicity
    OUTPUT_DIR = "generated_audio"
    
# --- Ensure output directory exists ---
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

# --- FastAPI app setup ---
app = FastAPI(
    title="Simple FastAPI TTS",
    description="JSON-based Text-to-Speech FastAPI Service (No Auth).",
    version="4.3"
)

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- ✅ Enable CORS for frontend / external testing ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Input Model for Swagger ---
class TTSRequest(BaseModel):
    text: str
    format: str = "mp3"
    rate: int = 160


# -----------------------------------------------
# --- Text-to-Speech function (Robust) ---
# -----------------------------------------------
def synthesize_speech(text: str, fmt: str, rate: int) -> str:
    """
    Generate speech audio using pyttsx3 and return file path.
    Raises RuntimeError on pyttsx3 failure.
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)

        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id) 

        file_name = f"tts_{uuid.uuid4().hex[:8]}.{fmt}"
        file_path = os.path.join(Config.OUTPUT_DIR, file_name)

        engine.save_to_file(text, file_path)
        engine.runAndWait() 
        
        logging.info(f"TTS file created → {file_path}")

        if not os.path.exists(file_path):
             raise RuntimeError(f"File was not created by pyttsx3 at path: {file_path}")
        
        return file_path

    except Exception as e:
        logging.error(f"TTS FATAL ERROR: {e}")
        raise RuntimeError(f"pyttsx3 failed to initialize or generate audio. Cause: {e}")
        
# -----------------------------------------------
# --- API Endpoints ---
# -----------------------------------------------

@app.post("/api/speak", response_class=FileResponse, summary="Convert Text to Speech (No Auth)")
async def api_speak(data: TTSRequest):
    """
    Generates speech from text. No API key required.
    """
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text input required")

    fmt = data.format.lower()
    rate = int(data.rate)

    logging.info(f"TTS request → text='{text[:40]}...' format={fmt}, rate={rate}")

    try:
        file_path = synthesize_speech(text, fmt, rate)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"TTS generation failed: {e}"
        )

    # Note: os.path.exists check is already inside synthesize_speech, but FileResponse handles cleanup.
    return FileResponse(
        file_path,
        media_type=f"audio/{fmt}",
        filename=os.path.basename(file_path)
    )

@app.get("/",tags=['about'] )
async def root():
    return JSONResponse({"status": "Model is runnning"})

@app.get("/health", response_model=Any)
async def health_check():
    """Simple health check endpoint."""
    return JSONResponse({"status": "ok", "service": "TTS API"})

