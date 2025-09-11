# views.py - AI Sales Agent (Whisper + ElevenLabs TTS + Groq GPT)
import os
import json
import tempfile
import base64
import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import whisper
import requests
import imageio_ffmpeg
from dotenv import load_dotenv
load_dotenv()  # loads environment variables from .env
 
# ---- FFmpeg path ----
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

# ---- GPT (Groq) ----
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---- Whisper model ----
whisper_model = whisper.load_model("base")

# ---- Conversation memory ----
conversation_memory = {}

# ---- ElevenLabs API ----
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY") 
ELEVEN_VOICE_EN = "EXAVITQu4vr4xnSDxMaL"
ELEVEN_VOICE_UR = "21m00Tcm4TlvDq8ikWAM"

# ---- Home page ----
def home(request):
    return render(request, "index.html")

# ---- Emotion detection ----
def detect_emotion(text: str) -> str:
    t = text.lower()
    positive = ["love","great","awesome","good","like","perfect","happy","interested"]
    negative = ["hate","bad","angry","upset","disappointed","not happy","frustrat"]
    if any(w in t for w in positive): return "positive"
    if any(w in t for w in negative): return "negative"
    return "neutral"

# ---- Lead-stage progression ----
def get_lead_stage(latest_message: str, current_stage: str) -> str:
    text = latest_message.lower()
    warm_keys = ["interested","price","demo","details","info","tell me","more about","maloomat","kya"]
    hot_keys = ["buy","purchase","sign up","signup","subscribe","order","pay","payment","kharidna","lena"]
    closed_keys = ["done","deal","contract","payment received","paid","completed","ho gaya","tay ho gaya"]

    if current_stage=="cold" and any(k in text for k in warm_keys): return "warm"
    if current_stage in ["cold","warm"] and any(k in text for k in hot_keys): return "hot"
    if current_stage in ["warm","hot"] and any(k in text for k in closed_keys): return "closed"
    return current_stage

# ---- Language detection ----
def detect_language(text: str) -> str:
    urdu_chars = set("اآبپتٹثجچحخدڈذرزژسشصضطظعغفقکگلمنوہی")
    if any(ch in urdu_chars for ch in text): return "ur"
    return "en"

# ---- GPT reply ----
def generate_groq_reply(user_message, conversation_history, lang="en"):
    sys_prompt = "You are a helpful AI sales agent. Reply concisely in 1-2 sentences."
    if lang=="ur": sys_prompt += " Reply in Roman Urdu."
    else: sys_prompt += " Reply in English."

    messages = [
        {"role":"system","content":sys_prompt},
        {"role":"user","content":conversation_history + "\nUser: " + user_message}
    ]
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_completion_tokens=180,
            stream=True
        )
        reply_text = ""
        for chunk in completion:
            reply_text += chunk.choices[0].delta.content or ""
        return reply_text.strip()
    except Exception as e:
        print("Groq error:", e)
        return f"Sorry, I am having trouble responding. ({e})"

# ---- ElevenLabs TTS ----
def generate_eleven_tts(text: str, lang="en") -> str:
    voice_id = ELEVEN_VOICE_EN if lang.startswith("en") else ELEVEN_VOICE_UR
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVEN_API_KEY,"Content-Type":"application/json"}
    data = {"text":text,"voice_settings":{"stability":0.5,"similarity_boost":0.75}}
    response = requests.post(url,json=data)
    if response.status_code==200:
        return base64.b64encode(response.content).decode("utf-8")
    else:
        print("ElevenLabs TTS error:", response.text)
        return ""

# ---- Process message ----
def process_message(user_message, session_id, lang="en"):
    if session_id not in conversation_memory:
        conversation_memory[session_id] = {"messages":[],"lead_stage":"cold","emotion":"neutral","lang":"en"}

    conversation_memory[session_id]["messages"].append(user_message)
    current_stage = conversation_memory[session_id]["lead_stage"]
    new_stage = get_lead_stage(user_message, current_stage)
    emo = detect_emotion(user_message)
    lang = detect_language(user_message)

    conversation_memory[session_id].update({"lead_stage":new_stage,"emotion":emo,"lang":lang})
    history_text = " ".join(conversation_memory[session_id]["messages"][-8:])
    bot_reply = generate_groq_reply(user_message, history_text, lang)
    audio_base64 = generate_eleven_tts(bot_reply, lang)

    return bot_reply, new_stage, emo, audio_base64, conversation_memory[session_id]

# ---- Text chat endpoint ----
@csrf_exempt
def chat_api(request):
    if request.method!="POST": return JsonResponse({"error":"Invalid request"},status=400)
    try:
        data = json.loads(request.body.decode("utf-8"))
        user_message = data.get("message","").strip()
        session_id = data.get("session_id","default")
    except Exception as e:
        return JsonResponse({"error":f"Invalid JSON: {e}"},status=400)
    if not user_message:
        return JsonResponse({"error":"Empty message"},status=400)

    bot_reply, stage, emo, audio, memory = process_message(user_message, session_id)
    return JsonResponse({
        "reply": bot_reply,
        "lead_stage": stage,
        "emotion": emo,
        "audio": audio,
        "memory": memory
    })

# ---- Voice chat endpoint ----
@csrf_exempt
def voice_api(request):
    if request.method != "POST" or "audio" not in request.FILES:
        return JsonResponse({"error": "Invalid request"}, status=400)

    session_id = request.POST.get("session_id", "default")
    audio_file = request.FILES["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp:
        tmp.write(audio_file.read())
        tmp_input = tmp.name
    tmp_wav = tmp_input + ".wav"

    try:
        # ---- Convert to WAV for Whisper using imageio-ffmpeg ----
        cmd = f'"{FFMPEG_BIN}" -y -i "{tmp_input}" -ar 16000 -ac 1 -c:a pcm_s16le "{tmp_wav}"'
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)

        # ---- Whisper transcription ----
        result = whisper_model.transcribe(tmp_wav, task="transcribe")
        if isinstance(result, dict):
            raw_text = result.get("text", "")
            detected_lang = result.get("language", "en")
        else:
            raw_text = ""
            detected_lang = "en"

        # Ensure user_message is string
        user_message = raw_text.strip() if isinstance(raw_text, str) else ""

        # Ensure detected_lang is string
        if isinstance(detected_lang, list):
            detected_lang = detected_lang[0] if detected_lang else "en"
        elif not isinstance(detected_lang, str):
            detected_lang = "en"

    except Exception as e:
        return JsonResponse({"error": f"Whisper or ffmpeg error: {e}"}, status=500)
    finally:
        if os.path.exists(tmp_input): os.remove(tmp_input)
        if os.path.exists(tmp_wav): os.remove(tmp_wav)

    if not user_message:
        return JsonResponse({"error": "No speech detected"}, status=400)

    bot_reply, stage, emo, audio_base64, memory = process_message(user_message, session_id, lang=detected_lang)

    return JsonResponse({
        "reply": bot_reply,
        "lead_stage": stage,
        "emotion": emo,
        "audio": audio_base64,
        "memory": memory,
        "detected_lang": detected_lang
    })
