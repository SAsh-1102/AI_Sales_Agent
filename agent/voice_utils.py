# agent/voice_utils.py
import tempfile
import os
import whisper
from gtts import gTTS

# Load Whisper model once at module level (base model is small & fast)
whisper_model = whisper.load_model("base")  # you can change to "small" or "medium" for better accuracy

def text_to_speech(text, lang='en'):
    """
    Convert text to speech using gTTS.
    Returns path to the temporary MP3 file.
    """
    tts = gTTS(text=text, lang=lang)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

def speech_to_text(audio_file_path):
    """
    Convert audio file to text using OpenAI Whisper.
    Supports wav, mp3, m4a, etc.
    """
    try:
        result = whisper_model.transcribe(audio_file_path)
        text = str(result.get("text", "")).strip()  # force to string to avoid PyLance warning
        if not text:
            return "Sorry, I could not understand the audio."
        return text
    except Exception as e:
        return f"STT service failed: {str(e)}"

