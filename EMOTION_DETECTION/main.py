# main.py - FIXED VERSION

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
# --- NEW IMPORT ---
from fastapi.middleware.cors import CORSMiddleware
# ------------------
import io
import time
from emotion_model import EmotionPredictor

# Initialize FastAPI app
app = FastAPI(title="Production Emotion Analyzer API", version="1.0.0")

# --- CORS CONFIGURATION TO FIX CONNECTION ERRORS ---
# Add origins that are allowed to make requests.
# Allowing "*" means any origin (essential for testing from local files or different ports).
origins = [
    "*", 
    # You could also list specific allowed origins like:
    # "http://localhost",
    # "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # Allows specific origins
    allow_credentials=True,            # Allows cookies/authorization headers
    allow_methods=["*"],               # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],               # Allows all headers
)
# ---------------------------------------------------


# Dependency: Initialize the predictor once at startup
def get_emotion_predictor():
    """Initializes and yields the predictor instance."""
    predictor = EmotionPredictor()
    return predictor

# Use the dependency injection to get the singleton predictor instance
predictor = get_emotion_predictor()

@app.get("/", tags=["Health Check"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Emotion Analysis API is running."}

# The core prediction endpoint
@app.post("/predict_emotion/", tags=["Prediction"])
async def predict_emotion(
    file: UploadFile = File(...),
):
    """
    Receives an image file and returns the predicted emotion.
    The client is responsible for sending a single frame/image.
    """
    try:
        start_time = time.time()
        
        # Read the uploaded file's content
        image_data = await file.read()
        
        # Get prediction from the core model logic
        result = predictor.predict_emotion(image_data)
        
        end_time = time.time()
        result["latency_ms"] = round((end_time - start_time) * 1000, 2)
        
        # Log and return the result
        print(f"Request processed in {result['latency_ms']}ms. Result: {result.get('emotion')}")
        return JSONResponse(content=result)
        
    except Exception as e:
        # Catch and report the specific error, but return a generic 500 to the client
        print(f"API Error: {e}")
        # Raising HTTPException ensures the client receives a 500 status code
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")