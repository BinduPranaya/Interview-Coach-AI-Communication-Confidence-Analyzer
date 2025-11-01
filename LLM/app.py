# app.py
import streamlit as st
import requests
import json
import time

# --- Configuration ---
# NOTE: Ensure your FastAPI server is running at this address (e.g., uvicorn main:app --reload)
API_BASE_URL = "http://localhost:8000"

# --- Helper Functions for API Communication ---

def start_new_interview(role: str, model: str) -> requests.Response:
    """Calls the FastAPI /interview/start endpoint."""
    url = f"{API_BASE_URL}/interview/start?model_name={model}"
    payload = {"role": role}
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: Ensure FastAPI is running at {API_BASE_URL}. Details: {e}")
        return None

def continue_conversation(session_id: str, reply: str) -> requests.Response:
    """Calls the FastAPI /interview/continue endpoint."""
    url = f"{API_BASE_URL}/interview/continue"
    payload = {"session_id": session_id, "candidate_reply": reply}
    
    try:
        response = requests.post(url, json=payload, timeout=30) # Allow longer timeout for LLM inference
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Error continuing interview: {e}")
        return None

def terminate_interview(session_id: str):
    """Calls the FastAPI /interview/terminate/{session_id} endpoint."""
    url = f"{API_BASE_URL}/interview/terminate/{session_id}"
    try:
        requests.delete(url, timeout=10)
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not explicitly terminate session on API: {e}")

# --- Streamlit Application Logic ---

def display_chat_message(role: str, content: str):
    """Displays a message in the Streamlit chat format."""
    with st.chat_message(role):
        st.write(content)

def handle_start_click():
    """Starts a new interview session and clears the old state."""
    # Reset internal state
    st.session_state.interview_active = False
    st.session_state.session_id = None
    st.session_state.messages = []
    
    # Get user inputs
    role = st.session_state.job_role_input
    model = st.session_state.model_name_input
    
    if not role:
        st.warning("Please enter a Job Role to begin.")
        return

    # Call the FastAPI /start endpoint
    with st.spinner(f"Starting interview for '{role}' with model '{model}'..."):
        response = start_new_interview(role, model)
    
    if response and response.status_code == 201:
        data = response.json()
        
        # Update Streamlit state
        st.session_state.interview_active = True
        st.session_state.session_id = data['session_id']
        st.session_state.messages.append({"role": "Interviewer", "content": data['interviewer_reply']})
        
        # Display the first message
        st.rerun()

def handle_end_click():
    """Handles the user clicking the End Interview button."""
    if st.session_state.session_id:
        # 1. Send final message to AI
        final_prompt = "END INTERVIEW"
        response = continue_conversation(st.session_state.session_id, final_prompt)
        
        if response and response.status_code == 200:
            data = response.json()
            st.session_state.messages.append({"role": "Interviewer", "content": data['interviewer_reply']})

        # 2. Explicitly clean up session on the API server
        terminate_interview(st.session_state.session_id)
        
    # 3. Update Streamlit state
    st.session_state.interview_active = False
    st.session_state.session_id = None
    st.success("Interview session concluded and resources cleared.")
    st.rerun()

def handle_candidate_reply(candidate_reply: str):
    """Sends candidate reply to API and gets next question."""
    
    # 1. Append candidate message to history
    st.session_state.messages.append({"role": "Candidate", "content": candidate_reply})
    
    # 2. Call API to continue conversation
    with st.spinner("Interviewer is analyzing and preparing the next question..."):
        response = continue_conversation(st.session_state.session_id, candidate_reply)

    if response and response.status_code == 200:
        data = response.json()
        interviewer_reply = data['interviewer_reply']
        
        # 3. Append interviewer's reply to history
        st.session_state.messages.append({"role": "Interviewer", "content": interviewer_reply})
        
        # 4. Check if the AI concluded the interview
        if "interview concluded" in interviewer_reply.lower() or "interview finished" in interviewer_reply.lower():
            st.session_state.interview_active = False
            st.success("The interview has been politely concluded by the interviewer.")
            
        st.rerun()
    else:
        st.error("Failed to get response from API. Please try again.")

def main():
    """Main Streamlit application function."""
    st.set_page_config(page_title="Ollama AI Recruiter Mock Interview", layout="wide")

    st.title("🤖 Ollama AI Recruiter Interviewer")
    st.caption(f"Connected to FastAPI at: `{API_BASE_URL}`")

    # --- Initialize Streamlit Session State ---
    if 'interview_active' not in st.session_state:
        st.session_state.interview_active = False
        st.session_state.session_id = None
        st.session_state.messages = []
        
    # --- Sidebar for Configuration and Actions ---
    with st.sidebar:
        st.header("Interview Setup")
        
        # Input for Job Role
        st.text_input(
            "Job Role (e.g., Senior Data Engineer)", 
            value="Backend Software Engineer specializing in scalable microservices", 
            key="job_role_input"
        )
        
        # Input for LLM Model (Uses the default from your FastAPI CONFIG)
        st.text_input(
            "Ollama Model Name", 
            value="llama3.1", 
            key="model_name_input"
        )

        st.divider()
        
        # Start/End Buttons
        if not st.session_state.interview_active:
            st.button("🚀 Start New Interview", on_click=handle_start_click, type="primary")
            if st.session_state.session_id:
                st.info(f"Last Session ID: {st.session_state.session_id}")
        else:
            st.button("🛑 End Interview Session", on_click=handle_end_click, type="secondary")
            st.info(f"Active Session ID: {st.session_state.session_id}")

    # --- Main Chat Interface ---
    
    # 1. Display chat history
    if not st.session_state.messages and not st.session_state.interview_active:
        st.info("Set the 'Job Role' in the sidebar and click 'Start New Interview' to begin!")
    
    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])

    # 2. Chat input box
    if st.session_state.interview_active:
        candidate_reply = st.chat_input("Your response...", disabled=False)
        if candidate_reply:
            handle_candidate_reply(candidate_reply)
    elif st.session_state.messages:
         st.markdown("---")
         st.success("The interview is complete. Click 'Start New Interview' to begin a new session.")

if __name__ == "__main__":
    main()