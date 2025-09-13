import whisper

model = whisper.load_model("small")  # "small" / "medium" / "large"

def speech_to_text(audio_file_path: str) -> str:
    try:
        result = model.transcribe(audio_file_path)
        text = result.get("text", "")
        if isinstance(text, str):
            text = text.strip()
        else:
            text = ""
        return text
    except Exception as e:
        print("STT Error:", e)
        return ""
