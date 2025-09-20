# load_embeddings.py
import os
import django
from typing import List

# IMPORTANT: set settings module before importing Django models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website_sale_agent.settings")
django.setup()

from agent.models import Product
from agent.embedding_service import collection, embedding_fn

def build_product_text_from_model(p: Product) -> str:
    # Use getattr to avoid static analysis errors and to gracefully handle missing attrs
    parts = [
        f"Name: {getattr(p, 'name', '') or ''}",
        f"Model: {getattr(p, 'model', '') or ''}",
        f"Category: {getattr(p, 'category', '') or ''}",
        f"Processor: {getattr(p, 'processor', '') or ''}",
        f"Memory: {getattr(p, 'memory', '') or ''}",
        f"Storage: {getattr(p, 'storage', '') or ''}",
        f"Display: {getattr(p, 'display', '') or ''}",
        f"Graphics: {getattr(p, 'graphics', '') or ''}",
        f"Cooling: {getattr(p, 'cooling', '') or ''}",
        f"Features: {getattr(p, 'features', '') or ''}",
        f"Price: {getattr(p, 'price', '') or ''}",
    ]
    # Remove empty segments and join
    return " | ".join([seg for seg in parts if seg.split(": ", 1)[1].strip() != ""])

def main():
    products = Product.objects.all()
    if not products.exists():
        print("❌ No products found in the database. Insert products first (e.g. run your load_products.py).")
        return

    print(f"Found {products.count()} products. Generating embeddings and upserting into ChromaDB...")

    for p in products:
        # build text for embedding
        text = build_product_text_from_model(p)

        # generate embedding (embedding_fn expects a list)
        emb = embedding_fn([text])[0]

        # choose an id for chroma: prefer DB pk if exists, else fallback to model string
        pk = getattr(p, "pk", None) or getattr(p, "id", None) or getattr(p, "model", None) or str(hash(text))

        collection.upsert(
            ids=[str(pk)],
            embeddings=[emb],
            metadatas=[{
                "name": getattr(p, "name", ""),
                "model": getattr(p, "model", ""),
                "price": getattr(p, "price", "")
            }],
            documents=[text]
        )

        print(f"Embedded and upserted: {getattr(p, 'name', getattr(p, 'model', str(pk)))} (id={pk})")

    print("All done.")
    try:
        print("Total items in collection:", collection.count())
    except Exception as e:
        print("Could not read collection count:", e)

if __name__ == "__main__":
    main()
