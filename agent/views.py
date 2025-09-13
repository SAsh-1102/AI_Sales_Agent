from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import json

# 👇 Import memory service
from agent.memory_service import save_message, get_history


# 👇 Homepage
def index(request):
    return render(request, "index.html")


# 👇 Rule-based fallback (improved)
def rule_based_lead_and_emotion(user_message):
    text = user_message.lower()

    # Default
    lead_stage = "cold"
    emotion = "neutral"
    reply_text = "Can you tell me a bit more so I can assist you better?"

    if any(word in text for word in ["price", "cost", "details", "info", "pricing"]):
        lead_stage = "warm"
        emotion = "curious"
        reply_text = "Our pricing starts at $49/month for a basic subscription and goes up to $199/month for enterprise."
    elif any(word in text for word in ["buy", "purchase", "order", "deal"]):
        lead_stage = "hot"
        emotion = "happy"
        reply_text = "Great choice! I can guide you through the purchase process right away."
    elif any(word in text for word in ["thanks", "great", "perfect", "love"]):
        lead_stage = "closed"
        emotion = "satisfied"
        reply_text = "We’re happy to serve you! Thanks for trusting us."
    elif any(word in text for word in ["hello", "hi", "hey"]):
        reply_text = "Hello! How can I help you today?"
    elif "website" in text:
        reply_text = "Yes, we also provide professional website design services. Would you like a demo?"
    elif "demo" in text:
        reply_text = "Sure! I can arrange a free demo for you. When would be a good time?"
    elif "support" in text:
        reply_text = "Our support team is available 24/7. You can always reach us by chat or email."

    return lead_stage, emotion, reply_text


# 👇 Chat API (Groq LLM + DB memory)
@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")

        # ---- Save user message ----
        save_message(session_id, "user", user_message)

        # ---- Defaults ----
        lead_stage, emotion = "cold", "neutral"
        reply_text = "Sorry, LLM not connected."

        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

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
                                "Return response in strict JSON only with keys: reply, lead_stage, emotion. "
                                "Example:\n"
                                "{\"reply\": \"Our product helps you save time!\", \"lead_stage\": \"warm\", \"emotion\": \"curious\"}"
                            )
                        },
                        {"role": "user", "content": user_message}
                    ]
                }
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                resp_json = r.json()
                raw_reply = resp_json["choices"][0]["message"]["content"].strip()

                parsed = json.loads(raw_reply.replace("'", '"'))
                reply_text = parsed.get("reply", "I'm here to assist you.")
                lead_stage = parsed.get("lead_stage", "cold")
                emotion = parsed.get("emotion", "neutral")

            except Exception:
                lead_stage, emotion, reply_text = rule_based_lead_and_emotion(user_message)
        else:
            lead_stage, emotion, reply_text = rule_based_lead_and_emotion(user_message)

        # ---- Save agent reply ----
        save_message(session_id, "agent", reply_text)

        # ---- Get full history ----
        history = get_history(session_id, limit=50)
        history_data = [{"sender": h.sender, "message": h.message, "time": h.timestamp.strftime("%H:%M")} for h in history]

        return JsonResponse({
            "reply": reply_text,
            "lead_stage": lead_stage,
            "emotion": emotion,
            "history": history_data
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
