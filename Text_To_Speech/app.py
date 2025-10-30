
import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
speech_file_path = Path(__file__).parent / "speech.wav"
text_input = input("Enter text to synthesize: ")
print("Generating speech...\n", text_input)
response = client.audio.speech.create(
  model="playai-tts",
  voice="Aaliyah-PlayAI",
  response_format="wav",
  input=text_input
)
response.write_to_file(speech_file_path)



print(f"Speech audio saved to {speech_file_path}")
      