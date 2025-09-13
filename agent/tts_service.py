import os
import requests
import base64
from gtts import gTTS
from io import BytesIO

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")  # ElevenLabs key

def text_to_speech(text: str, voice: str = "alloy") -> str:
    """
    Convert text → audio base64.
    Uses ElevenLabs if API key is available, else gTTS fallback.
    """
    try:
        if ELEVEN_API_KEY:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
            headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"}
            payload = {"text": text, "voice_settings": {"stability":0.5,"similarity_boost":0.7}}
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                return base64.b64encode(r.content).decode("utf-8")
            else:
                print("ElevenLabs TTS error:", r.text)
        # Fallback to gTTS
        tts = gTTS(text)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode("utf-8")
    except Exception as e:
        print("TTS Error:", e)
        return ""
