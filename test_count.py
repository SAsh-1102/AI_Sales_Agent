print("✅ test_count.py is running...")

from agent.embedding_service import collection

try:
    result = collection.count()
    print("⚡ Raw result type:", type(result))
    print("📊 Total embeddings count in DB:", result)
except Exception as e:
    print("❌ Failed to fetch count:", e)

# Optional: Direct query test
try:
    res = collection.get(limit=3)
    print("🔍 Sample documents:", res)
except Exception as e:
    print("❌ Could not fetch sample docs:", e)
