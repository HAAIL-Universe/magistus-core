# voice_output.py

import asyncio
import os
import sys
from edge_tts import Communicate
from config_loader import load_config

try:
    from playsound import playsound
except ImportError:
    playsound = None  # Optional autoplay only works if playsound is installed

# Load runtime config
config = load_config()
VOICE_ENABLED = config.get("voice_output", False)

# Default voice: British male (change if needed)
DEFAULT_VOICE = "en-GB-RyanNeural"

async def _speak_async(text: str, filename: str, voice: str = DEFAULT_VOICE):
    """
    Internal async TTS function using Edge-TTS and saves to file.
    """
    try:
        communicate = Communicate(text=text, voice=voice)
        await communicate.save(filename)
    except Exception as e:
        print(f"[TTS Error] {e}")

def speak_text(text: str, filename: str = "response.mp3", autoplay: bool = False):
    """
    Public function to speak text aloud (respects config toggle).
    Saves output to an MP3 file and optionally autoplays.
    """
    if not VOICE_ENABLED:
        print(f"[TTS Disabled] {text}")
        return

    # Ensure file path is safe to overwrite
    try:
        asyncio.run(_speak_async(text, filename))
        print(f"[TTS] Saved to {filename}")

        if autoplay:
            if playsound:
                playsound(filename)
            else:
                print("[TTS] Autoplay requested, but 'playsound' is not installed.")
    except Exception as e:
        print(f"[TTS Error] {e}")
