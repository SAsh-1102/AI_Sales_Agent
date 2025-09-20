from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .voice_utils import text_to_speech, speech_to_text
from agent.casual_responses import casual_responses
from datetime import datetime
from agent.embedding_service import collection, embedding_fn
import pytz
import os
import json
import tempfile
import base64
import requests
import random

from agent.memory_service import save_message, get_history
from agent.prompts import SALES_CHATBOT_PROMPT

# Pakistan timezone
PAKISTAN_TZ = pytz.timezone("Asia/Karachi")

def index(request):
    return render(request, "index.html")

def query_similar_products_rag(user_message, n_results=3):
    """
    Generate embeddings for the user message and query ChromaDB
    to retrieve similar products safely.
    """
    query_emb = embedding_fn([user_message])[0]
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results,
        include=['documents', 'metadatas']
    )

    similar_products = []

    # Ensure results and inner lists exist
    documents_list = results.get('documents')
    metadatas_list = results.get('metadatas')

    if documents_list and metadatas_list:
        docs_list = documents_list[0] if len(documents_list) > 0 and documents_list[0] else []
        metas_list = metadatas_list[0] if len(metadatas_list) > 0 and metadatas_list[0] else []

        for doc, meta in zip(docs_list, metas_list):
            similar_products.append((doc, meta))

    return similar_products




def fallback_response(user_message):
    """
    Simple fallback: try casual responses or generic message
    """
    lower_msg = user_message.lower()
    for keyword, response in casual_responses.items():
        if keyword in lower_msg:
            return response
    return "Sorry, I don't have information about that product. Please ask about available products or categories."


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body.decode("utf-8"))
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    save_message(session_id, "user", user_message)

    reply_text = None
    lead_stage, emotion = "cold", "neutral"

    # --- Step 1: Use RAG to fetch similar products ---
    try:
        similar_products = query_similar_products_rag(user_message, n_results=3)
        if similar_products:
            product_context = "\n".join([f"{meta['name']}: {doc}" for doc, meta in similar_products])
        else:
            product_context = ""
    except Exception:
        product_context = ""

    # --- Step 2: Call LLM if context is available ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    if GROQ_API_KEY and product_context:
        try:
            history = get_history(session_id, limit=5)
            history_text = "\n".join([f"{getattr(h, 'sender', 'unknown')}: {getattr(h, 'message', '')}" for h in history])

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
                    lead_stage = parsed.get("lead_stage", "warm")
                    emotion = parsed.get("emotion", "happy")
                except json.JSONDecodeError:
                    reply_text = raw_reply

        except Exception:
            reply_text = None

    # --- Step 3: Fallback if no LLM or empty context ---
    if not reply_text:
        if product_context:
            # If RAG returned products but LLM failed, list them
            reply_text = "Here are some products that might match your query:\n"
            for doc, meta in similar_products:
                reply_text += f"- {meta['name']} ({meta.get('model', 'N/A')}): ${meta.get('price', 'N/A')}\n"
        else:
            # Casual/fallback response
            reply_text = fallback_response(user_message)

    save_message(session_id, "agent", reply_text)

    history = get_history(session_id, limit=50)
    history_data = [
        {"sender": getattr(h, "sender", "unknown"),
         "message": getattr(h, "message", ""),
         "timestamp": getattr(h, "timestamp", datetime.now()).astimezone(PAKISTAN_TZ).strftime("%d-%m-%Y %I:%M:%S %p")}
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
