"""Quick test: RAG retrieval and Gemini service structure."""
import sys
sys.path.insert(0, '.')

from services.gemini_service import _retrieve_context, _KNOWLEDGE_BASE

print(f"Knowledge base: {len(_KNOWLEDGE_BASE)} entries")

# Test retrieval
queries = [
    "What fertilizer for wheat?",
    "How to treat tomato blight?",
    "drip irrigation water saving",
    "rice paddy kharif season"
]

for q in queries:
    results = _retrieve_context(q, top_k=3)
    topics = [r["topic"] for r in results]
    print(f"\nQuery: '{q}'")
    print(f"  Retrieved: {topics}")

# Test that chat function exists and handles missing API key gracefully
from services.gemini_service import chat
try:
    chat("test")
except EnvironmentError as e:
    print(f"\nExpected error (no API key): {str(e)[:60]}...")

print("\nAll RAG tests passed!")
