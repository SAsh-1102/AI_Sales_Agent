from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import random
import json

# 👇 Homepage
def index(request):
    return render(request, "index.html")

# 👇 Chat API (Groq LLM se connected)
@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")

        # ---- Dummy memory/lead stage logic ----
        memory = {"session": session_id, "history": [user_message]}

        # Random lead stage selection (just for demo, aap isko apni logic se replace kar sakte ho)
        lead_stages = ["cold", "warm", "hot", "closed"]
        emotions = ["neutral", "curious", "happy", "satisfied"]
        lead_stage = random.choice(lead_stages)
        emotion = random.choice(emotions)

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
                        {
                            "role": "system",
                            "content": (
                                "You are an AI sales assistant. "
                                "Always return reply as plain text only (no JSON). "
                                "Decide lead_stage (cold, warm, hot, closed) "
                                "and emotion (neutral, curious, happy, satisfied) internally, "
                                "but do NOT include them in the reply text."
                            )
                        },
                        {"role": "user", "content": user_message}
                    ]
                }
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers, json=payload
                )
                resp_json = r.json()
                raw_reply = resp_json["choices"][0]["message"]["content"].strip()

                # 👇 Sirf reply text user ko show hoga
                reply_text = raw_reply

            except Exception as e:
                reply_text = f"LLM error: {str(e)}"

        # 👇 Response frontend ke liye (chat + header update)
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
