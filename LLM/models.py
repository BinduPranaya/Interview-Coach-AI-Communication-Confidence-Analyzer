# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# --- Interview Session Management ---

class InterviewStart(BaseModel):
    """Schema for starting a new interview."""
    role: str = Field(..., description="The job role for the mock interview, e.g., 'Senior Python Developer'.")

class InterviewContinue(BaseModel):
    """Schema for continuing an existing interview."""
    session_id: str = Field(..., description="Unique ID for the interview session.")
    candidate_reply: str = Field(..., description="The candidate's response to the previous question.")

class InterviewSessionState(BaseModel):
    """Schema for the session data stored by the API."""
    recruiter: Any  # We'll store the AIRecruiter object here, as it's not JSON serializable.
    history: List[Dict[str, str]]

# --- API Responses ---

class InterviewResponse(BaseModel):
    """Standard response for all interview endpoints."""
    session_id: str = Field(..., description="The unique ID for the current session.")
    interviewer_reply: str = Field(..., description="The AI Recruiter's response (question or greeting/conclusion).")

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="A clear description of the error.")