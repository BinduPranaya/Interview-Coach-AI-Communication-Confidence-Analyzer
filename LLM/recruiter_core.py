#LLM recruiter_core.py
from groq import Groq
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# ------------------ Groq API Key -----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --- Configuration ---
CONFIG = {
    "MODEL_NAME": "llama-3.1-8b-instant"
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
    def __init__(self, model: str = CONFIG["MODEL_NAME"]):
        self.model = model
        self.client = Groq(api_key=GROQ_API_KEY)
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def _get_response(self) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history
            )

            # FIXED new SDK: dot-notation
            reply = response.choices[0].message.content

            self.conversation_history.append(
                {"role": "assistant", "content": reply}
            )
            return reply

        except Exception as e:
            return f"Error calling Groq API: {e}"

    def start_interview(self, role: str) -> str:
        user_prompt = f"Begin the mock interview for the role: {role}. Start with a greeting and your first question."
        self.conversation_history.append({"role": "user", "content": user_prompt})
        return self._get_response()

    def continue_interview(self, candidate_reply: str) -> str:
        if not candidate_reply.strip():
            return "Please provide a response before continuing the interview."

        self.conversation_history.append(
            {"role": "user", "content": candidate_reply}
        )
        return self._get_response()


# ------------------ CLI Demo ------------------

def main():
    job_role = "Backend Software Engineer specializing in scalable microservices"
    recruiter = AIRecruiter(model=CONFIG["MODEL_NAME"])

    print("\n=======================================================")
    print(f"Starting Mock Interview for Role: {job_role}")
    print("Type 'END INTERVIEW' at any time to finish.")
    print("=======================================================")

    interviewer_reply = recruiter.start_interview(job_role)
    print(f"\n[Interviewer]: {interviewer_reply}")

    while True:
        candidate_response = input("\n[Candidate]: ")

        if candidate_response.strip().upper() == "END INTERVIEW":
            final_prompt = "The candidate has indicated they are finished. Please conclude the interview politely."
            closing_reply = recruiter.continue_interview(final_prompt)
            print(f"\n[Interviewer]: {closing_reply}")
            print("\n--- Interview Concluded ---")
            break

        interviewer_reply = recruiter.continue_interview(candidate_response)
        print(f"\n[Interviewer]: {interviewer_reply}")


if __name__ == "__main__":
    main()
