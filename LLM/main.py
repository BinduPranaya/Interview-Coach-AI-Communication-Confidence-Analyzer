# main.py
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, status, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import the core logic and Pydantic schemas
# NOTE: Ensure recruiter_core.py is accessible and models.py is updated if needed.
from recruiter_core import AIRecruiter, CONFIG, SYSTEM_PROMPT 
from models import InterviewStart, InterviewContinue, InterviewResponse, ErrorResponse

# --- In-Memory Session Store ---
# Using a dict for simplicity here.
session_store: Dict[str, Any] = {} # Storing the complex AIRecruiter object directly

# --- Application Startup/Shutdown Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    """
    print("Application Startup: FastAPI is ready.")
    yield
    # Cleanup on shutdown: Clear all in-memory sessions
    session_store.clear()
    print("Application Shutdown: All in-memory sessions cleared.")

app = FastAPI(
    title="Ollama AI Recruiter API",
    description="A microservice for conducting mock technical interviews using Ollama's LLMs. Specify the job role and LLM model to tailor the interview.",
    version="1.1.0",
    lifespan=lifespan,
)

# --- Middleware (Production Ready Feature) ---

# 1. CORS Middleware: Crucial for allowing frontend applications to connect.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # WARNING: Set this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Custom Logging Middleware: To log request processing time and basic info.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs the time taken to process each request."""
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        # Catch exceptions not handled by the route or other middleware
        print(f"Middleware caught unhandled exception: {e}")
        # --- FIX: Ensure 'content' is provided to JSONResponse ---
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal Server Error: {e}"} # <-- The required 'content' argument is now present
        )
        # Note: We return the response instead of raising to ensure the request is finished gracefully
        # If you raise here, the error will just be caught again by Uvicorn, which is fine, 
        # but returning the response is cleaner for middleware
        return response # Return the error response

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"[{request.method}] {request.url.path} - Process Time: {process_time:.4f}s - Status: {response.status_code}")
    return response

# --- API Endpoints ---

@app.post(
    "/interview/start",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}
)
async def start_interview_endpoint(
    data: InterviewStart,
    model_name: str = CONFIG['MODEL_NAME'] # Allows overriding the default model via query parameter
):
    """
    Starts a new mock interview session for a specified job role.
    Optionally, specify a different Ollama 'model_name' (e.g., 'mixtral').
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Instantiate the AIRecruiter with the potentially overridden model
        recruiter = AIRecruiter(model=model_name)

        # Start the conversation
        initial_reply = recruiter.start_interview(data.role)

        if "error" in initial_reply.lower():
            # Handle Ollama connection/model not found error from the core class
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=initial_reply
            )

        # Store the active session's full recruiter object
        session_store[session_id] = recruiter 

        return InterviewResponse(session_id=session_id, interviewer_reply=initial_reply)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Critical error in /interview/start: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An internal server error occurred: {e}"
        )

@app.post(
    "/interview/continue",
    response_model=InterviewResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}
)
async def continue_interview_endpoint(data: InterviewContinue):
    """
    Submits a candidate's reply and gets the next question/analysis.
    The 'END INTERVIEW' command will be handled here by the recruiter.
    """
    recruiter: AIRecruiter = session_store.get(data.session_id)
    
    if not recruiter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session ID not found or interview has concluded. Please start a new session."
        )

    try:
        # Continue the conversation
        next_reply = recruiter.continue_interview(data.candidate_reply)

        if "error" in next_reply.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=next_reply
            )
        
        # Check if the AI's reply indicates the end (based on the SYSTEM_PROMPT rule 5)
        if "interview concluded" in next_reply.lower() or "interview finished" in next_reply.lower():
             del session_store[data.session_id]
             print(f"Session {data.session_id} concluded and removed.")

        return InterviewResponse(session_id=data.session_id, interviewer_reply=next_reply)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Critical error in /interview/continue for session {data.session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An internal server error occurred: {e}"
        )

@app.delete(
    "/interview/terminate/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}}
)
def terminate_interview_endpoint(
    session_id: str = Path(..., description="The unique ID of the interview session to terminate.")
):
    """
    Explicitly terminates and clears an interview session.
    Used for manual cleanup or client-side end-interview actions.
    """
    if session_id in session_store:
        del session_store[session_id]
        print(f"Session {session_id} explicitly terminated and removed.")
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session ID '{session_id}' not found."
        )

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "AI Recruiter API", "active_sessions": len(session_store)}