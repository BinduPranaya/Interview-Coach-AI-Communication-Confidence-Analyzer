import os
import sys
import uvicorn
from pathlib import Path
from groq import Groq, GroqError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# --- Configuration & Initialization ---

# 1. Load environment variables from .env file
load_dotenv()

# 2. Safely get the API Key and ensure it exists
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY is not set in environment variables or .env file.", file=sys.stderr)
    sys.exit(1)

# 3. Initialize the Groq client
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"❌ ERROR: Could not initialize Groq client: {e}", file=sys.stderr)
    sys.exit(1)

# 4. Define TTS constants
TTS_MODEL = "playai-tts"
# Note: The Groq API only supports 'mp3', 'wav', 'pcm', 'flac'
# Let's default to mp3 as it's more common, but allow 'wav'
DEFAULT_RESPONSE_FORMAT = "mp3" 

# 5. Initialize FastAPI app
app = FastAPI(
    title="Groq TTS API",
    description="A simple API to proxy text-to-speech requests to the Groq API.",
    version="1.0.0"
)

# --- API Models ---

class TTSRequest(BaseModel):
    """Defines the JSON body for a /synthesize request."""
    text: str
    voice: str = "Aaliyah-PlayAI" # Default voice, can be overridden
    format: str = DEFAULT_RESPONSE_FORMAT # Default format, can be 'wav', 'pcm', etc.

# --- API Endpoints ---

@app.get("/", summary="Root/Health Check")
async def read_root():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Groq TTS API is running."}

@app.post("/synthesize/", 
          summary="Synthesize Speech",
          description="Takes text and returns streaming audio data.")
async def create_synthesis(request: TTSRequest):
    """
    Handles the POST request to /synthesize/.
    - Takes a JSON body with "text", "voice", and "format".
    - Calls the Groq API.
    - Streams the audio response back.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    print(f"✨ Received request for voice: {request.voice}, format: {request.format}")
    print(f'   -> Input: "{request.text[:50]}..."') # Log first 50 chars

    try:
        # 4. API Call
        # Note: The Groq client's 'create' method returns a streaming-capable object
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=request.voice,
            response_format=request.format,
            input=request.text
        )

        # 5. Stream the audio response
        # We use iter_bytes() which is a generator, perfect for StreamingResponse
        return StreamingResponse(
            response.iter_bytes(),
            media_type=f"audio/{request.format}"
        )

    except GroqError as e:
        # Handle specific Groq API errors
        print(f"\n❌ Groq API Error: {e}", file=sys.stderr)
        status_code = e.status_code if hasattr(e, 'status_code') else 500
        detail = f"Groq API error: {e.message or str(e)}"
        if status_code == 401:
            detail = "Authentication failed. Check your GROQ_API_KEY."
        elif 'rate limit' in str(e).lower():
            detail = "You may have hit a rate limit. Try again shortly."
        raise HTTPException(status_code=status_code, detail=detail)
        
    except Exception as e:
        # Handle other unexpected errors
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Server Execution ---

if __name__ == "__main__":
    """Run the FastAPI server using uvicorn."""
    # print("🚀 Starting FastAPI server at http://127.0.0.1:8000")
    # print("   -> Access API docs at http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
