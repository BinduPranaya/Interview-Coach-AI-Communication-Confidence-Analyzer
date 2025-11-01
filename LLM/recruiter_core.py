import ollama
import json
from typing import List, Dict, Any

# --- Configuration ---
CONFIG = {
    'MODEL_NAME': 'llama3.1',
    # NOTE: This host MUST be running the Ollama server for the code to function.
    'OLLAMA_HOST': 'http://localhost:11434',
}

SYSTEM_PROMPT = """
You are a highly professional Senior Technical Recruiter and AI Interviewer.

Your role is to conduct **mock technical interviews** for candidates based on the job role provided by the user.
You must act exactly like a real interviewer — professional, concise, and conversational.
Ask one question at a time and wait for the candidate’s response before continuing.
Never generate multiple questions at once.
Never reveal evaluation criteria unless specifically asked.

Follow these rules strictly:

1. Start with a **short professional greeting** confirming the job role and begin the interview.
2. Ask questions that progressively test the candidate’s **communication, technical depth, and problem-solving** skills.
3. After the candidate responds, analyze their answer briefly (in one line) and continue with the **next relevant question**.
4. Maintain a **neutral, respectful, and realistic tone** — no emojis, no friendly chatter.
5. End the interview politely after around 6–8 exchanges or when the candidate indicates completion (e.g., the user types 'END INTERVIEW').
6. **Do not** show explanations, system notes, or instructions to the user.
"""

class AIRecruiter:
    """
    Manages the state and conversation flow for a mock technical interview 
    using a local Ollama LLM service.
    """
    def __init__(self, host: str = CONFIG['OLLAMA_HOST'], model: str = CONFIG['MODEL_NAME']):
        """
        Initializes the Ollama client and sets up the conversation history.

        Args:
            host: The URL for the Ollama server (e.g., 'http://localhost:11434').
            model: The name of the model to use (e.g., 'llama3.1').
        """
        self.host = host
        self.model = model
        self.client = ollama.Client(host=self.host)
        # Initialize conversation with the strict system instruction
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        print(f"--- AIRecruiter Initialized (Host: {self.host}, Model: {self.model}) ---")

    def _get_response(self) -> str:
        """
        Private method to safely call the Ollama chat API and extract the response.
        Handles connection and API errors.
        """
        try:
            response = self.client.chat(model=self.model, messages=self.conversation_history)
            
            # Check if the response structure is valid and extract the content
            interviewer_reply = response.get('message', {}).get('content')
            if interviewer_reply:
                self.conversation_history.append({"role": "assistant", "content": interviewer_reply})
                return interviewer_reply
            else:
                return "Error: Received an empty or malformed response from the LLM."
                
        except ollama.exceptions.RequestError as e:
            # Handle connection errors, model not found, etc.
            return f"Error connecting to Ollama or processing request: {e}. Please ensure Ollama is running at {self.host} and the model '{self.model}' is downloaded."
        except Exception as e:
            return f"An unexpected error occurred during the API call: {e}"

    def start_interview(self, role: str) -> str:
        """
        Initializes the interview for a specific job role and asks the first question.

        Args:
            role: The job title (e.g., 'Senior Python Developer').

        Returns:
            The interviewer's initial greeting and first question, or an error message.
        """
        user_prompt = f"Begin the mock interview for the role: {role}. Start with a greeting and your first question."
        self.conversation_history.append({"role": "user", "content": user_prompt})

        return self._get_response()

    def continue_interview(self, candidate_reply: str) -> str:
        """
        Continues the interview conversation based on the candidate's response.

        Args:
            candidate_reply: The candidate's response to the previous question.

        Returns:
            The interviewer's one-line analysis and next question, or an error message.
        """
        if not candidate_reply.strip():
             return "Please provide a response before continuing the interview."
             
        self.conversation_history.append({"role": "user", "content": candidate_reply})
        
        return self._get_response()

# --- Example Usage ---

def main():
    """
    Runs a demonstration of the AI Recruiter in a command-line environment.
    """
    job_role = "Backend Software Engineer specializing in scalable microservices"
    
    # 1. Initialize the recruiter instance
    recruiter = AIRecruiter(model=CONFIG['MODEL_NAME'])

    # 2. Start the interview
    print("\n=======================================================")
    print(f"Starting Mock Interview for Role: {job_role}")
    print("Type 'END INTERVIEW' at any time to finish.")
    print("=======================================================")

    interviewer_prompt = recruiter.start_interview(job_role)
    print(f"\n[Interviewer]: {interviewer_prompt}")
    
    # 3. Conversation loop
    while True:
        candidate_response = input("\n[Candidate]: ")
        
        if candidate_response.strip().upper() == "END INTERVIEW":
            # Provide a final prompt to the LLM to end the interview politely
            final_prompt = "The candidate has indicated they are finished. Please conclude the interview politely and professionally."
            final_reply = recruiter.continue_interview(final_prompt)
            print(f"\n[Interviewer]: {final_reply}")
            print("\n--- Interview Concluded ---")
            break

        if "error" in interviewer_prompt.lower():
            # Stop if a critical error was returned
            print("\n--- Interview Halted Due to Ollama Error ---")
            break

        interviewer_prompt = recruiter.continue_interview(candidate_response)
        print(f"\n[Interviewer]: {interviewer_prompt}")

if __name__ == "__main__":
    # NOTE: This application requires an Ollama server running locally at 
    # the configured host (http://localhost:11434 by default) and the specified 
    # model (llama3.1) to be downloaded.
    # 
    # To run this, you must have the 'ollama' Python package installed: 
    # pip install ollama
    main()
