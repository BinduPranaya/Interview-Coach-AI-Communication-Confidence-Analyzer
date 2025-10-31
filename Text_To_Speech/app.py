import os
import sys
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# --- Configuration & Initialization ---

# 1. Load environment variables from a .env file (if present)
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

# Define file paths and constants
# Use a more descriptive file name and place it in the same directory as the script
OUTPUT_FILENAME = "synthesized_speech.wav"
# Path(_file_).parent gets the directory of the current script
output_file_path = Path(__file__).parent / OUTPUT_FILENAME

# TTS Model and Voice
TTS_MODEL = "playai-tts"
TTS_VOICE = "Aaliyah-PlayAI"
RESPONSE_FORMAT = "wav" # Groq API defaults to 'mp3', but 'wav' is requested here

# --- Main Logic ---

def synthesize_text_to_speech():
    """Prompts the user for text, calls the Groq TTS API, and saves the audio."""
    try:
        # Get input from the user
        text_input = input("🗣 Enter text to synthesize: ").strip()

        if not text_input:
            print("🛑 Input cannot be empty. Exiting.")
            return

        print(f"\n✨ Generating speech with {TTS_VOICE} via {TTS_MODEL}...")
        print(f'   -> Input: "{text_input}"')
        
        # 4. API Call
        response = client.audio.speech.create(
          model=TTS_MODEL,
          voice=TTS_VOICE,
          response_format=RESPONSE_FORMAT,
          input=text_input
        )

        # 5. File Writing and Success Message
        print(f"💾 Saving audio to {output_file_path}...")
        response.write_to_file(output_file_path)
        
        print("\n✅ Success!")
        print(f"   The synthesized speech has been saved to: *{output_file_path.resolve()}*")

    except Exception as e:
        # 6. Comprehensive Error Handling
        print(f"\n❌ An error occurred during synthesis or file writing: {e}", file=sys.stderr)
        if hasattr(e, 'status_code') and e.status_code == 401:
             print("   -> Check if your GROQ_API_KEY is valid.", file=sys.stderr)
        elif 'rate limit' in str(e).lower():
             print("   -> You may have hit a rate limit. Try again shortly.", file=sys.stderr)

if __name__ == "__main__":
    synthesize_text_to_speech()