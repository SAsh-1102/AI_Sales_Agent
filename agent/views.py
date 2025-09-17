from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .voice_utils import text_to_speech, speech_to_text
from agent.casual_responses import casual_responses
from datetime import datetime
import pytz
import re
import os
import json
import tempfile
import base64
import requests

from agent.memory_service import save_message, get_history
from agent.products_data import products
from agent.prompts import SALES_CHATBOT_PROMPT

# Pakistan timezone
PAKISTAN_TZ = pytz.timezone("Asia/Karachi")


def index(request):
    return render(request, "index.html")


def build_product_context():
    product_lines = []
    for p in products:
        details = []
        for key, value in p.items():
            if key != "stripe_price_id":
                details.append(f"{key}: {value}")
        product_lines.append(f"{p.get('name', p.get('model'))} | " + " | ".join(details))
    return "\n".join(product_lines)


def find_product_answer(user_message):
    message_lower = user_message.lower()
    replies = []

    # 1) Casual greetings
    for key, resp in casual_responses.items():
        if re.search(r'\b' + re.escape(key) + r'\b', message_lower):
            replies.append(resp)
            message_lower = re.sub(r'\b' + re.escape(key) + r'\b', '', message_lower)

    # 2) Detect comparison intent
    comparison_keywords = ['compare', ' vs ', ' vs.', 'versus', 'which is better', 'compare between']
    is_compare_intent = any(k in message_lower for k in comparison_keywords)

    # 3) Find mentioned products
    mentioned = []
    for p in products:
        name = (p.get('name') or p.get('model') or "").lower()
        model = (p.get('model') or "").lower()
        if name and re.search(r'\b' + re.escape(name) + r'\b', message_lower):
            mentioned.append(p)
        elif model and re.search(r'\b' + re.escape(model) + r'\b', message_lower):
            mentioned.append(p)

    if not is_compare_intent and len(mentioned) >= 2:
        is_compare_intent = True

    # 4) Build comparison table
    if is_compare_intent and len(mentioned) >= 2:
        all_keys = set().union(*(set(p.keys()) for p in mentioned))
        ignore_keys = {"stripe_price_id", "name", "model"}

        table_rows = ""
        for key in sorted(all_keys):
            if key in ignore_keys:
                continue
            values = [p.get(key, "N/A") for p in mentioned]

            # Always include key specs even if they are equal
            if key in ["price", "processor", "memory", "storage", "graphics", "display", "cooling", "category"] \
               or len(set(values)) > 1:
                table_rows += "<tr><td><b>{}</b></td>{}</tr>".format(
                    key.capitalize(), "".join(f"<td>{v}</td>" for v in values)
                )

        table_html = f"""
        __TABLE__<table class='comparison-table'>
            <thead><tr><th>Spec</th>{"".join(f"<th>{p.get('name')}</th>" for p in mentioned)}</tr></thead>
            <tbody>{table_rows or "<tr><td colspan='3'>No specs available.</td></tr>"}</tbody>
        </table>
        """

        reply_text = " ".join(replies) + " " + table_html if replies else table_html
        return {"reply": reply_text, "lead_stage": "curious", "emotion": "neutral"}

    # 5) Single product found
    if len(mentioned) == 1:
        p = mentioned[0]
        specs = ", ".join(
            f"{k}: {v}" for k, v in p.items()
            if k not in ["name", "model", "category", "price", "stripe_price_id"]
        )
        reply_text = f"{p.get('name', p.get('model'))} ({p.get('category')}): Price ${p.get('price')}, Specs: {specs}"
        if replies:
            reply_text = " ".join(replies) + " " + reply_text
        return {"reply": reply_text, "lead_stage": "warm", "emotion": "happy"}

    if replies:
        return {"reply": " ".join(replies), "lead_stage": "cold", "emotion": "neutral"}

    return None


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body.decode("utf-8"))
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    save_message(session_id, "user", user_message)

    answer = find_product_answer(user_message)
    if answer:
        reply_text, lead_stage, emotion = answer["reply"], answer["lead_stage"], answer["emotion"]
    else:
        reply_text = "Sorry, I don't have information about that product. Please ask about available products or categories."
        lead_stage, emotion = "cold", "neutral"

        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        if GROQ_API_KEY:
            try:
                product_context = build_product_context()
                history = get_history(session_id, limit=5)
                history_text = "\n".join([f"{h.sender}: {h.message}" for h in history])

                system_prompt = SALES_CHATBOT_PROMPT.replace("{product_context}", product_context)
                payload = {
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": history_text}
                    ]
                }
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
                resp_json = r.json()

                if "choices" in resp_json:
                    raw_reply = resp_json["choices"][0]["message"]["content"].strip()
                    try:
                        parsed = json.loads(raw_reply.replace("'", '"'))
                        reply_text = parsed.get("reply", raw_reply)
                        lead_stage = parsed.get("lead_stage", "cold")
                        emotion = parsed.get("emotion", "neutral")
                    except json.JSONDecodeError:
                        reply_text = raw_reply

            except Exception as e:
                reply_text = f"Sorry, I had an issue: {str(e)}"

    save_message(session_id, "agent", reply_text)

    history = get_history(session_id, limit=50)
    history_data = [
        {"sender": h.sender, "message": h.message,
         "timestamp": h.timestamp.astimezone(PAKISTAN_TZ).strftime("%d-%m-%Y %I:%M:%S %p")}
        for h in history
    ]

    return JsonResponse({"reply": reply_text, "lead_stage": lead_stage, "emotion": emotion, "history": history_data})


@csrf_exempt
def voice_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    action = request.GET.get("action", "tts")

    if action == "tts":
        data = json.loads(request.body.decode("utf-8"))
        text = data.get("text", "")
        audio_path = text_to_speech(text)
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        os.remove(audio_path)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return JsonResponse({"audio_base64": audio_base64})

    elif action == "stt":
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"error": "No audio file provided"}, status=400)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        text = speech_to_text(temp_path)
        os.remove(temp_path)
        return JsonResponse({"text": text})

    return JsonResponse({"error": "Invalid action. Use ?action=tts or ?action=stt"}, status=400)
