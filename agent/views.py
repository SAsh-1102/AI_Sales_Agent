from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import json

from agent.memory_service import save_message, get_history
from agent.products_data import products


def index(request):
    return render(request, "index.html")


def build_product_context():
    product_lines = []
    for p in products:
        details = []
        for key, value in p.items():
            if key not in ["stripe_price_id"]:
                details.append(f"{key}: {value}")
        product_lines.append(f"Product: {p.get('name', p.get('model'))} | " + " | ".join(details))
    return "\n".join(product_lines)


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body.decode("utf-8"))
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    save_message(session_id, "user", user_message)

    reply_text, lead_stage, emotion = "Sorry, I don't have an answer yet.", "cold", "neutral"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    if GROQ_API_KEY:
        try:
            product_context = build_product_context()
            history = get_history(session_id, limit=5)
            history_text = "\n".join([f"{h.sender}: {h.message}" for h in history])

            system_prompt = f"""
            You are a strict AI Sales Assistant for TechNerds.

            RULES:
            - ALWAYS check the following dataset first before answering: 
              {product_context}
            - NEVER ask for clarification.
            - NEVER say "Can you tell me a bit more".
            - If the user asks about products that are not in the dataset, respond exactly:
              "Sorry, I don't have information about that product. Please ask about available products or categories."
            - If comparing products, list clear differences in specs, price, and category.
            - If the user is ready to buy, encourage them.
            - Keep answers short, professional, and confident.
            - Reply STRICTLY in JSON:
              {{"reply": "...", "lead_stage": "cold|warm|hot|closed", "emotion": "neutral|curious|happy|satisfied"}}
            """

            payload = {
                "model": "mixtral-8x7b-32768",  # ✅ switched model
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": history_text}
                ]
            }

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers=headers, json=payload, timeout=20)
            resp_json = r.json()
            raw_reply = resp_json["choices"][0]["message"]["content"].strip()

            try:
                parsed = json.loads(raw_reply.replace("'", '"'))
                reply_text = parsed.get("reply", raw_reply)
                lead_stage = parsed.get("lead_stage", "cold")
                emotion = parsed.get("emotion", "neutral")
            except json.JSONDecodeError:
                reply_text = raw_reply

            # ✅ Post-processing filter: Remove "Can you tell me..." or clarification prompts
            if "can you tell me a bit more" in reply_text.lower():
                reply_text = "Sorry, I don't have information about that product. Please ask about available products or categories."
                lead_stage = "cold"
                emotion = "neutral"

        except Exception as e:
            reply_text = f"Sorry, I had an issue: {str(e)}"

    save_message(session_id, "agent", reply_text)

    history = get_history(session_id, limit=50)
    history_data = [
        {"sender": h.sender, "message": h.message, "time": h.timestamp.strftime("%H:%M")}
        for h in history
    ]

    return JsonResponse({
        "reply": reply_text,
        "lead_stage": lead_stage,
        "emotion": emotion,
        "history": history_data
    })


@csrf_exempt
def voice_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    return JsonResponse({"status": "ok", "message": "Voice API placeholder."})
