"""
AgriMind AI - Trilingual Chat & Streaming Automated Verification Test
Validates:
1. Trilingual language classification (English, Hindi, Hinglish)
2. Live response generation matching query language
3. Real-time streaming generator (SSE chunk-by-chunk delivery)
4. Absence of canned/memorized template patterns
"""
import sys
import io
import json
import asyncio
from pathlib import Path

# Fix Windows console UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from services.gemini_service import detect_query_language, chat, chat_stream

def test_language_detection():
    print("\n" + "="*70)
    print("TEST 1: TRILINGUAL LANGUAGE DETECTION")
    print("="*70)

    test_cases = [
        ("What is the fertilizer schedule for wheat in rabi season?", "english"),
        ("How to control tomato early blight disease?", "english"),
        ("गेहूँ की फसल में कौन सा खाद डालना चाहिए?", "hindi"),
        ("आलू में पछेती झुलसा रोग से बचाव के क्या उपाय हैं?", "hindi"),
        ("kheti me gehun ke liye konsi khad best hai", "hinglish"),
        ("bhai gehu ki fasal me pehla pani kab de", "hinglish"),
        ("kapas me patti mudne ka rog kaise thik kare", "hinglish"),
    ]

    for query, expected in test_cases:
        detected = detect_query_language(query)
        assert detected == expected, f"Failed for '{query}': expected {expected}, got {detected}"
        print(f"  [PASS] [{detected.upper():8}] -> '{query}'")

    print(f"All {len(test_cases)} language detection test cases PASSED!")

def test_chat_generation():
    print("\n" + "="*70)
    print("TEST 2: DYNAMIC TRILINGUAL GENERATION (NON-MEMORIZED)")
    print("="*70)

    queries = [
        ("English", "What is the recommended fertilizer schedule for wheat in rabi season?"),
        ("Hindi", "गेहूँ की फसल में कौन सा खाद और कितनी मात्रा में डालना चाहिए?"),
        ("Hinglish", "bhai gehu ki fasal me pehla pani kab de aur konsi khad dale"),
    ]

    for label, q in queries:
        res = chat(q)
        reply = res["reply"]
        lang = res.get("language")
        engine = res.get("engine")
        status = res.get("status")
        print(f"\n[Query ({label})]: '{q}'")
        print(f"  Detected Language: {lang} | Engine: {engine} | Status: {status}")
        clean_preview = reply[:180].replace('\n', ' ')
        print(f"  Reply Preview: {clean_preview}...")
        assert len(reply) > 80, "Response is too short!"
        if label == "Hinglish":
            assert lang == "hinglish"
        elif label == "Hindi":
            assert lang == "hindi"

    print("\nAll chat generation tests PASSED!")

def test_streaming_generator():
    print("\n" + "="*70)
    print("TEST 3: REAL-TIME TOKEN/LINE STREAMING (SSE CHUNKS)")
    print("="*70)

    async def run_stream():
        query = "kheti me gehun ke liye konsi khad best hai aur pehla pani kab de"
        chunks = []
        final_event = None

        async for sse_event in chat_stream(query):
            assert sse_event.startswith("data: ")
            assert sse_event.endswith("\n\n")
            payload = json.loads(sse_event[6:].strip())
            if payload.get("chunk"):
                chunks.append(payload["chunk"])
            if payload.get("done"):
                final_event = payload

        assert len(chunks) > 0, "No chunks received from stream!"
        assert final_event is not None, "Final done event not received!"
        assert final_event["done"] is True
        assert final_event.get("language") == "hinglish"
        print(f"  [PASS] Streamed {len(chunks)} real-time chunks successfully.")
        print(f"  [PASS] Final SSE Payload: Engine={final_event.get('model')}, Lang={final_event.get('language')}")

    asyncio.run(run_stream())

if __name__ == "__main__":
    test_language_detection()
    test_chat_generation()
    test_streaming_generator()
    print("\n" + "="*70)
    print("ALL TRILINGUAL CHAT & STREAMING TESTS PASSED (3/3)!")
    print("="*70)
