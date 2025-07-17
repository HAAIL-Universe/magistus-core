# voice_input.py

import os
import traceback

try:
    import speech_recognition as sr
except ImportError:
    raise ImportError(
        "Missing dependency: Please install SpeechRecognition via `pip install SpeechRecognition`"
    )

# Optional: log errors if debug_logger is available
try:
    from debug_logger import log_error
except ImportError:
    def log_error(msg): pass  # fallback no-op if logger isn't present


def get_user_voice_input(timeout: int = 5, phrase_time_limit: int = 10) -> str:
    """
    Captures microphone input and transcribes it into text using SpeechRecognition.
    
    Args:
        timeout (int): Max seconds to wait for speech.
        phrase_time_limit (int): Max duration of phrase in seconds.
    
    Returns:
        str: Transcribed text, or empty string if failed.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Listening... (Speak now)")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            transcript = recognizer.recognize_whisper(audio)  # Using Whisper backend
            print(f"🗣️  You said: {transcript}")
            return transcript
        except sr.UnknownValueError:
            log_error("Voice input failed: Audio could not be understood.")
            print("❌ Could not understand audio.")
        except sr.RequestError as e:
            log_error(f"Voice input request error: {e}")
            print("❌ Could not request results from transcription service.")
        except Exception as e:
            log_error(f"Unexpected voice input error: {traceback.format_exc()}")
            print("❌ An unexpected error occurred during voice capture.")

    return ""


# Optional: allow this to be used as a quick test utility
if __name__ == "__main__":
    transcript = get_user_voice_input()
    if transcript:
        print(f"📝 Transcription: {transcript}")
    else:
        print("⚠️ No input captured.")
