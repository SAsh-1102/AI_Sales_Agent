# agent/memory_manager.py

import chromadb
from chromadb.utils import embedding_functions

# ---- Chroma Client Setup ----
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# ---- Embedding Function ----
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ---- Get or Create Collection ----
collection = chroma_client.get_or_create_collection(
    name="conversation_memory",
    embedding_function=embedding_fn  # type: ignore[arg-type]
)

def add_memory(user_message: str, bot_reply: str, session_id: str):
    """Add user and bot messages to Chroma."""
    try:
        existing = collection.get(where={"session_id": session_id})
        next_id = len(existing["ids"]) + 1

        collection.add(
            documents=[f"User: {user_message}\nBot: {bot_reply}"],
            metadatas=[{"session_id": session_id}],
            ids=[f"{session_id}-{next_id}"]
        )
    except Exception as e:
        print(f"[MemoryManager] Error while adding memory: {e}")

def get_memory(session_id: str, n_results: int = 5):
    """Fetch recent conversation history for a session."""
    try:
        results = collection.query(
            query_texts=["recent conversation"],
            where={"session_id": session_id},
            n_results=n_results
        )
        docs = results.get("documents")
        if not docs:  # handle None or empty
            return []
        # flatten nested list
        return [doc for sublist in docs for doc in sublist]
    except Exception as e:
        print(f"[MemoryManager] Error while fetching memory: {e}")
        return []


