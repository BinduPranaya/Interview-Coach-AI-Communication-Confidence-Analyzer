# modules/text_to_speech.py
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

def speak_text(text: str):
    """
    Try to speak using pyttsx3. If unavailable or if it errors,
    fall back to printing the text (so 'repeat' still works).
    """
    if pyttsx3:
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            try:
                engine.stop()
            except Exception:
                pass
            return
        except Exception as e:
            # fallback to print if TTS errors
            print("[speak_text fallback due to pyttsx3 error]:", e)
    # fallback print
    print("[speak_text fallback] " + text)
