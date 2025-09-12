from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests

# 👇 Homepage
def index(request):
    # index.html file render karega
    return render(request, "index.html")

# 👇 Chat API (Groq LLM se connected)
@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body.decode("utf-8"))
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")

        # ---- Dummy memory/lead stage logic (Phase 2) ----
        memory = {"session": session_id, "history": [user_message]}
        lead_stage = "warm"
        emotion = "neutral"

        # ---- Groq API Call (Phase 3) ----
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        reply_text = "Sorry, LLM not connected."

        if GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "You are an AI sales assistant."},
                        {"role": "user", "content": user_message}
                    ]
                }
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                  headers=headers, json=payload)
                resp_json = r.json()
                reply_text = resp_json["choices"][0]["message"]["content"].strip()
            except Exception as e:
                reply_text = f"LLM error: {str(e)}"

        return JsonResponse({
            "reply": reply_text,
            "lead_stage": lead_stage,
            "emotion": emotion,
            "memory": memory
        })
    return JsonResponse({"error": "Invalid request"}, status=400)

# 👇 Voice API placeholder
@csrf_exempt
def voice_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    return JsonResponse({
        "status": "ok",
        "message": "Voice API placeholder. Will be implemented in Phase 4."
    })
