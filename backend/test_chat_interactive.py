import sys
import io
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.gemini_service import chat

print("="*60)
print("TEST 1: English Agronomic Question")
print("="*60)
r1 = chat("What is the recommended fertilizer schedule for wheat in rabi season?")
print(f"Engine: {r1['engine']}")
print(f"Live Gemini: {r1['is_live_gemini']}")
print(f"Context Topics: {r1['context_topics']}")
print(f"Reply:\n{r1['reply'][:350]}...\n")

print("="*60)
print("TEST 2: Hindi Agronomic Question")
print("="*60)
r2 = chat("गेहूँ की फसल में कौन सा खाद और कितनी मात्रा में डालना चाहिए?")
print(f"Engine: {r2['engine']}")
print(f"Live Gemini: {r2['is_live_gemini']}")
print(f"Context Topics: {r2['context_topics']}")
print(f"Reply:\n{r2['reply'][:350]}...\n")
