# test_embeddings.py
print("🔄 Regenerating product embeddings...")

from agent.embedding_service import generate_embeddings, collection

try:
    generate_embeddings()
except Exception as e:
    print("❌ generate_embeddings() failed:", e)

# Count check
try:
    count = collection.count()
    print(f"📊 Final count in collection: {count}")
except Exception as e:
    print("❌ Could not get count after regeneration:", e)

# Sample data fetch
try:
    res = collection.get(limit=3)
    print("🔍 Sample from DB:", res)
except Exception as e:
    print("❌ Failed to fetch sample data:", e)
