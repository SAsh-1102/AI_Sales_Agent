# agent/embedding_service.py
import chromadb
from chromadb.utils import embedding_functions
from agent.products_data import products
from .products_data import products

# ---- Chroma Client Setup ----
chroma_client = chromadb.PersistentClient(path="./product_db")

# ---- Embedding Function ----
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ---- Collection Setup ----
collection = chroma_client.get_or_create_collection(
    name="product_embeddings",
    embedding_function=embedding_fn  # type: ignore
)

def build_product_text(p):
    details = [f"{k}: {v}" for k, v in p.items() if k not in ["stripe_price_id", "id"]]
    return f"{p.get('name', p.get('model', 'Unknown Product'))} | " + " | ".join(details)
from .products_data import products

def generate_embeddings():
    print("[EmbeddingService] 🚀 Starting regeneration process...")
    print(f"[EmbeddingService] 📦 Total products loaded: {len(products)}")

    try:
       print("[EmbeddingService] 🗑 Attempting to clear old embeddings...")
       collection.delete()  # ✅ This clears the entire collection safely
       print("[EmbeddingService] ✅ Old embeddings cleared.")
    except Exception as e:
       print(f"[EmbeddingService] ⚠️ Failed to clear embeddings: {e}")


    success_count = 0

    for idx, p in enumerate(products):
        try:
            text = " ".join([f"{k}: {v}" for k, v in p.items()])
            print(f"[EmbeddingService] ➕ Adding product #{idx+1}: {p.get('name', 'Unknown')}")
            
            # Force embedding calculation (help catch errors early)
            emb = embedding_fn([text])
            print(f"[EmbeddingService] 🧠 Embedding shape: {len(emb)}")  # debug

            collection.upsert(
                documents=[text],
                metadatas=[p],
                ids=[f"product-{idx+1}"],
                embeddings=emb
            )
            success_count += 1
            print(f"[EmbeddingService] ✅ Successfully added {p['name']}")

        except Exception as e:
            print(f"[EmbeddingService] ❌ Failed to add {p.get('name', 'Unknown')}: {e}")
            import traceback
            traceback.print_exc()

    try:
        final_count = collection.count()
        print(f"[EmbeddingService] 📊 Final count in collection: {final_count}")
        print(f"[EmbeddingService] ✅ Successfully added {success_count}/{len(products)} products")
    except Exception as e:
        print(f"[EmbeddingService] ⚠️ Could not count final embeddings: {e}")


def query_similar_products(user_query, n_results=5):
    try:
        results = collection.query(
            query_texts=[user_query],
            n_results=n_results,
            include=["documents", "metadatas"]
        ) or {}
    except Exception as e:
        print(f"[EmbeddingService] ❌ Query failed: {e}")
        return []

    docs_list = results.get("documents") or [[]]
    metas_list = results.get("metadatas") or [[]]

    docs = docs_list[0] if docs_list else []
    metas = metas_list[0] if metas_list else []

    return list(zip(docs, metas))
