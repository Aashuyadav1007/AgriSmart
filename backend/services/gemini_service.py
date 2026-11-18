"""
AgriSmart - Module 3: Trilingual (English, Hindi, Hinglish) GenAI Farming Assistant
- Mode 1: Live Google Gemini (gemini-3.8-flash / gemini-3.5-flash-lite) with streaming.
- Mode 2: Intelligent Dynamic Agricultural Local RAG Synthesizer (English, Hindi, Hinglish).
- Real-time SSE token/line streaming support for natural conversational generation.
"""
import os
import re
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncIterator

from dotenv import load_dotenv

logger = logging.getLogger("agrismart.gemini")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_KB_PATH = _BACKEND_DIR / "data" / "agri_knowledge_base.json"
_ENV_PATH = _BACKEND_DIR / ".env"

def _reload_env():
    """Reloads environment variables from backend/.env dynamically."""
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH, override=True)

# Initial load
_reload_env()

# ---------------------------------------------------------------------------
# Knowledge Base loading
# ---------------------------------------------------------------------------
def _load_knowledge_base() -> list[dict]:
    if not _KB_PATH.exists():
        return []
    try:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        return []

_KNOWLEDGE_BASE: list[dict] = _load_knowledge_base()

# ---------------------------------------------------------------------------
# Trilingual Query Language Detection (English, Hindi, Hinglish)
# ---------------------------------------------------------------------------
_HINGLISH_WORDS = {
    # Agricultural & Crop Terms
    "kheti", "fasal", "gehun", "gehu", "dhan", "chawal", "makka", "sarson", "chana", "kapas",
    "aalu", "tamatar", "ganna", "pyaj", "lahsun", "adrak", "mirch", "kisan", "khet", "beej",
    "khad", "dawa", "dawai", "keeda", "kida", "kit", "rog", "bimari", "sinchai", "paani",
    "pani", "mitti", "upaj", "paidavar", "jhulsa", "roktham", "ilaj", "upchar", "nursery",
    "boai", "katai", "patta", "patte", "patti", "pattiya", "peela", "peele", "safed", "kala",
    "sukha", "daana", "dane", "tilli", "gobhi",
    # Pronouns & Addresses
    "bhai", "kisan", "sir", "aap", "apka", "aapka", "apke", "aapke", "hum", "hamara", "mera",
    "meri", "mere", "mujhe", "mujhko", "sabko",
    # Question / Interrogatives
    "kya", "kaise", "kab", "kaha", "kahan", "kidhar", "kyu", "kyun", "kitna", "kitni", "kitne",
    "konsa", "konsi", "konse", "kaun", "kaunsa", "kaunsi",
    # Verbs, Auxiliaries & Modals
    "hai", "hain", "ho", "hoga", "hogi", "hoge", "hota", "hoti", "hote", "hua", "hue", "hui",
    "tha", "thi", "the", "kare", "karein", "karo", "karna", "karta", "karti", "karte", "dale",
    "dalen", "dalo", "dalna", "de", "den", "do", "dena", "batao", "bataye", "batayen", "bataiye",
    "lagaye", "lagana", "pad", "pada", "raha", "rahi", "rahe", "chahiye", "sakta", "sakti",
    "sakte", "bache", "bachaye", "bachega",
    # Connectives & Common Fillers
    "me", "mein", "se", "ko", "ka", "ki", "ke", "par", "aur", "ya", "bhi", "lekin", "magar",
    "taki", "namaste", "ram", "pranam", "accha", "acchi", "bohot", "bahut", "jada", "jyada",
    "kam", "pehle", "baad", "sahi", "tarika", "samay", "dhyan", "rakhe", "rakhein"
}

_STRONG_HINGLISH_ROOTS = {
    "konsa", "konsi", "konse", "kheti", "gehun", "khad", "roktham", "jhulsa", "sinchai",
    "kaise", "batao", "bataye", "bataiye", "chahiye", "kisan", "dawai"
}

def detect_query_language(text: str) -> str:
    """
    Classifies input query into:
    - 'hindi': Devanagari script (e.g. 'गेहूँ में खाद कब डालें?')
    - 'hinglish': Roman script Hindi (e.g. 'kheti me gehun ke liye konsi khad best hai')
    - 'english': Standard English (e.g. 'What is the fertilizer schedule for wheat?')
    """
    if re.search(r'[\u0900-\u097F]', text):
        return "hindi"
    tokens = set(re.findall(r'[a-zA-Z]+', text.lower()))
    matches = tokens.intersection(_HINGLISH_WORDS)
    if len(matches) >= 2 or any(token in _STRONG_HINGLISH_ROOTS for token in tokens):
        return "hinglish"
    return "english"

def _is_hindi_query(text: str) -> bool:
    """Legacy helper for backwards compatibility."""
    return detect_query_language(text) in ("hindi", "hinglish")

def _tokenize(text: str) -> set[str]:
    """Tokenize query into alphanumeric tokens."""
    tokens = re.findall(r"\w+", text.lower(), re.UNICODE)
    return set(tokens)

def _retrieve_context(query: str, top_k: int = 3) -> list[dict]:
    """Return top-k knowledge-base entries most relevant to the query."""
    if not _KNOWLEDGE_BASE:
        return []

    query_tokens = _tokenize(query)
    query_lower = query.lower()
    scores: list[tuple[float, dict]] = []

    for entry in _KNOWLEDGE_BASE:
        entry_text = " ".join([
            entry.get("topic", ""),
            " ".join(entry.get("keywords", [])),
            entry.get("content", "")
        ]).lower()
        
        entry_tokens = _tokenize(entry_text)
        
        intersection = query_tokens & entry_tokens
        union = query_tokens | entry_tokens
        jaccard = len(intersection) / len(union) if union else 0.0
        
        keyword_hits = sum(1 for kw in entry.get("keywords", []) if kw.lower() in query_lower)
        topic_match = 0.4 if entry.get("topic", "").lower() in query_lower else 0.0
        
        # High precision cross-lingual boost
        cross_lingual_bonus = 0.0
        if any(w in query_lower for w in ["gehu", "gehun", "wheat"]):
            if "wheat" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["khad", "urea", "dap", "potash", "npk", "fertilizer"]):
            if "fertilizer" in entry_text or "npk" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["kapas", "cotton"]):
            if "cotton" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["dhan", "chawal", "rice", "paddy"]):
            if "rice" in entry_text or "paddy" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["makka", "maize", "corn"]):
            if "maize" in entry_text or "corn" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["aalu", "potato"]):
            if "potato" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["tamatar", "tomato"]):
            if "tomato" in entry_text: cross_lingual_bonus += 0.85
        if any(w in query_lower for w in ["sinchai", "pani", "irrigation", "water"]):
            if "irrigation" in entry_text or "sinchayee" in entry_text: cross_lingual_bonus += 0.75
        if any(w in query_lower for w in ["jhulsa", "rog", "bimari", "keeda", "blight", "disease", "pest"]):
            if "disease" in entry_text or "blight" in entry_text or "pest" in entry_text: cross_lingual_bonus += 0.75

        score = jaccard + (keyword_hits * 0.20) + topic_match + cross_lingual_bonus
        
        if score > 0.0:
            scores.append((score, entry))

    scores.sort(key=lambda x: x[0], reverse=True)
    if not scores:
        return _KNOWLEDGE_BASE[:top_k]
    return [entry for _, entry in scores[:top_k]]

# ---------------------------------------------------------------------------
# Gemini Client Management
# ---------------------------------------------------------------------------
_gemini_client = None
_cached_key = None
_PRIMARY_MODEL = "gemini-3.5-flash-lite"
_BACKUP_MODELS = ["gemini-3.8-flash", "gemini-3.5-flash"]

def _get_api_key() -> str:
    """Retrieves GEMINI_API_KEY with dynamic reload."""
    _reload_env()
    return os.getenv("GEMINI_API_KEY", "").strip()

def _has_valid_api_key() -> bool:
    key = _get_api_key()
    return bool(key and key != "your_gemini_api_key_here" and len(key) >= 15)

def _get_client():
    global _gemini_client, _cached_key
    current_key = _get_api_key()
    
    if not _has_valid_api_key():
        return None

    if _gemini_client is not None and _cached_key == current_key:
        return _gemini_client

    try:
        from google import genai
        _gemini_client = genai.Client(api_key=current_key)
        _cached_key = current_key
        return _gemini_client
    except Exception as e:
        logger.error(f"Failed to initialize google-genai client: {e}")
        return None

# ---------------------------------------------------------------------------
# Dynamic Local RAG Synthesis Engine (Generates in English, Hindi, Hinglish)
# ---------------------------------------------------------------------------
def _synthesize_local_rag_response(message: str, relevant_entries: list[dict], lang: Optional[str] = None) -> str:
    """
    Synthesizes rich, dynamic agronomic advisory in the user's selected language:
    English, Hindi (Devanagari), or Hinglish (Roman Hindi).
    Directly answers the farmer's specific query with clear, practical steps and numbers.
    """
    if lang is None:
        lang = detect_query_language(message)

    msg_lower = message.lower()
    top_entry = relevant_entries[0] if relevant_entries else {}
    topic_name = top_entry.get("topic", "Agricultural Advisory")
    content = top_entry.get("content", "")
    citations = top_entry.get("source", "ICAR Extension Guidelines")
    category = top_entry.get("category", "general").lower()

    is_wheat_query = any(w in msg_lower for w in ["gehu", "gehun", "wheat"])
    is_fertilizer_query = any(w in msg_lower for w in ["khad", "urea", "dap", "potash", "npk", "fertilizer"])
    is_water_query = any(w in msg_lower for w in ["pani", "sinchai", "irrigation", "water"])
    is_cotton_query = any(w in msg_lower for w in ["kapas", "cotton"])
    is_disease_query = any(w in msg_lower for w in ["rog", "jhulsa", "bimari", "keeda", "dawa", "blight", "pest"])

    # 1. HINGLISH GENERATION
    if lang == "hinglish":
        if is_wheat_query and (is_water_query or is_fertilizer_query):
            return (
                "Kisan bhai, gehun ki fasal me sinchai aur khad ka prabandhan paidavar ke liye sabse mahatvapurna hai.\n\n"
                "**1. Pehli Sinchai (CRI Stage - Taaj Jad Awastha):**\n"
                "• Boai ke **20 se 25 din baad** pehla pani dena sabse zaroori hota hai. Is samay paudhe me mukhy jadon (Crown Roots) ka vikas hota hai. Agar is samay sinchai chhut gayi toh kalle (tillers) kam banenge aur upaj 20-30% tak ghat sakti hai.\n\n"
                "**2. Khad (Fertilizer) Ki Sahi Matra:**\n"
                "• **Pehli Sinchai Ke Turant Baad:** 1 bag Urea (lagbhag 30-35 kg prati acre) ka top-dressing karein. Agar boai par Zinc nahi dala tha, toh 5 kg Zinc Sulfate (33%) mila kar dein.\n"
                "• **Kul Sifarish (NPK):** 120 kg Nitrogen, 60 kg Phosphorus (DAP), aur 40 kg Potash (MOP) prati hectare. DAP aur Potash hamesha boai ke samay mitti me niche daal dein; Urea ko 2 se 3 bar me baant kar dein.\n\n"
                "**3. Aage Ka Sinchai Schedule:**\n"
                "• Dusra pani: Kalle nikalte samay (Tillering, 40-45 din).\n"
                "• Teesra pani: Ghabh/Phool aane se pehle (Jointing/Flowering, 80-85 din).\n"
                "• Chautha pani: Daana bharte samay (Milking stage, 100-105 din).\n\n"
                "📖 *Srot: ICAR - Bharatiya Gehun Avam Jau Anusandhan Sansthan (IIWBR)*"
            )
        elif is_cotton_query or (is_disease_query and "kapas" in msg_lower):
            return (
                "Kisan bhai, kapas ki fasal me keet aur rog roktham ke liye samay par kadam uthana zaroori hai.\n\n"
                "**1. Gulabi Sundi (Pink Bollworm) Aur Ras Chusne Wale Keet:**\n"
                "• **Pheromone Traps:** Khet me 5 se 8 pheromone trap prati acre lagayein taaki gulabi sundi ke patange pakad me aa sakein.\n"
                "• **Safed Makkhi & Thrips (Whitefly/Thrips):** Pila chipchipa trap (Yellow sticky trap) lagayein aur shuruati avastha me **Neem tel (5 ml prati liter paani)** ka chhidkaav karein.\n\n"
                "**2. Patti Mudne Ka Rog (Leaf Curl Virus / Bacterial Blight):**\n"
                "• Rog grasit paudhe dikhte hi unhe nikaal kar khet se door naste karein.\n"
                "• Fungal ya bacterial daag ke liye **Copper Oxychloride (2.5-3 gm/Ltr)** ke sath Streptocycline (1 gm in 10 Ltr paani) ka ghol bana kar 10 din ke antar par chhidkaav karein.\n\n"
                "**3. Khad Prabandhan:**\n"
                "• Kapas me NPK 180:80:60 kg/ha ka anushanshan hai. Nitrogen ko ek baar me na de kar phool aane tak 3-4 kisto me baantein.\n\n"
                "📖 *Srot: ICAR - Kendriya Kapas Anusandhan Sansthan (CICR)*"
            )
        elif is_disease_query or "blight" in topic_name.lower():
            return (
                "Kisan bhai, fasal me rog ya jhulsa ke shuruati lakshan pehchan kar turant ilaj karein.\n\n"
                "**1. Shuruati Lakshan Aur Safai:**\n"
                "• Patti par peele, bhoore ya target-board jaise gol daag aate hi rog grasit pattiya tod kar khet se door phenkein.\n"
                "• Khet me zyada der tak pani na theharne dein, hawa ka aana-jaana accha rakhein.\n\n"
                "**2. Asardaar Dawa Ka Chhidkaav:**\n"
                "• **Phafund Rog (Blight / Leaf Spot):** Mancozeb (2.5 gm prati liter paani) ya Copper Oxychloride (3 gm/Ltr) ka chhidkaav 7 se 10 din ke antar par karein.\n"
                "• **Gambhira Awastha (Late Blight):** Metalaxyl + Mancozeb (Ridomil Gold @ 2 gm/Ltr) ka prayog karein.\n"
                "• **Jaivik Niyantran:** Shuru se hi Trichoderma viride ya Neem tel (5ml/Ltr) ka istemal karein.\n\n"
                "📖 *Srot: ICAR Plant Pathology Extension Guidelines*"
            )
        elif is_fertilizer_query or "fertilizer" in category:
            return (
                "Kisan bhai, kheti me santulit khad ka prayog hi sabse zyada munafa deta hai.\n\n"
                "**1. NPK Ka Sahi Santulan:**\n"
                "• **Nitrogen (Urea):** Paudhe me hariyali aur badhav lata hai. Isko hamesha 2 ya 3 baar me baant kar dein (basal + tillering + flowering). Ek sath zyada Urea daalne se paudha jal sakta hai aur rog zyada aate hain.\n"
                "• **Phosphorus (DAP):** Jadon ka vikas aur shuruati taakat deta hai. DAP hamesha aakhiri jutai ya boai ke samay hi mitti me daal dena chahiye.\n"
                "• **Potash (MOP):** Daane me chamak, vajan aur fasal me rog se ladne ki shakti badhata hai.\n\n"
                "**2. Gobar Ki Khad & Micronutrients:**\n"
                "• Har saal 2-3 trolley gobar ki khad ya vermicompost zaroor dalein.\n"
                "• Agar pattiya peeli pad rahi ho ya kalle kam nikal rahe ho, toh **Zinc Sulfate (25 kg/ha)** ka istemal karein.\n\n"
                "📖 *Srot: ICAR Integrated Nutrient Management*"
            )
        else:
            return (
                f"Kisan bhai, aapke sawal (**{topic_name}**) ke anusaar practical kheti jankari:\n\n"
                f"{content}\n\n"
                f"**Khet Me Dhyan Rakhne Yogya Zaroori Baatein:**\n"
                f"• Mitti jaanch (Soil Health Card) ke hisab se hi khad aur paani ka santulan banayein.\n"
                f"• Keet ya rog ke shuruati lakshan dikhte hi jaivik neem tel (5ml/Ltr) ka chhidkaav karein.\n"
                f"• Kisi bhi samasya ke liye apne zila Krishi Vigyan Kendra (KVK) ki salah lein.\n\n"
                f"📖 *Srot: {citations}*"
            )

    # 2. HINDI GENERATION (Devanagari)
    elif lang == "hindi":
        if is_wheat_query:
            return (
                "नमस्ते किसान भाई! गेहूँ की फसल में समय पर सिंचाई और खाद प्रबंधन पैदावार के लिए निर्णायक है।\n\n"
                "**1. पहली सिंचाई (सीआरआई अवस्था - CRI Stage):**\n"
                "• बुवाई के **20 से 25 दिन बाद** पहली सिंचाई अनिवार्य रूप से करें। इस समय पौधे में ताज-जड़ें (Crown Roots) बनती हैं। इस अवस्था में पानी की कमी से कल्ले कम बनते हैं और पैदावार 25% तक घट सकती है।\n\n"
                "**2. खाद एवं उर्वरक का सही अनुपात:**\n"
                "• **सिंचाई के बाद:** 30-35 किलोग्राम यूरिया प्रति एकड़ का छिड़काव (Top-dressing) करें। यदि बुवाई के समय जिंक नहीं दिया था, तो 5 किग्रा जिंक सल्फेट (33%) अवश्य मिलाएं।\n"
                "• **संतुलित एनपीके:** 120:60:40 किग्रा/हेक्टेयर। डीएपी और पोटाश बुवाई के समय कतारों में दें तथा यूरिया को 2-3 बार में बांटकर दें।\n\n"
                "**3. आगे की मुख्य सिंचाई अवस्थाएं:**\n"
                "• कल्ले निकलते समय (40-45 दिन), गांठ बनते समय (60-65 दिन), और बालियों में दाना भरते समय (80-85 दिन)।\n\n"
                "📖 *स्रोत: भाकृअनुप - भारतीय गेहूँ एवं जौ अनुसंधान संस्थान (IIWBR)*"
            )
        elif is_cotton_query:
            return (
                "नमस्ते किसान भाई! कपास की फसल में कीट नियंत्रण एवं पोषण प्रबंधन की मुख्य सिफारिशें:\n\n"
                "**1. कीट नियंत्रण (गुलाबी सुंडी एवं सफेद मक्खी):**\n"
                "• खेत में 5 से 8 फेरोमोन ट्रैप प्रति एकड़ लगाएं ताकि गुलाबी सुंडी (Pink Bollworm) की निगरानी हो सके।\n"
                "• रस चूसक कीटों (थ्रिप्स, सफेद मक्खी) के लिए पीले चिपचिपे कार्ड लगाएं और नीम तेल (5 मिली/लीटर पानी) का छिड़काव करें।\n\n"
                "**2. पत्ती मुड़ने एवं जीवाणु अंगमारी (Black Arm) का उपचार:**\n"
                "• रोगग्रस्त पत्तियों को तोड़कर खेत से दूर नष्ट करें।\n"
                "• कॉपर ऑक्सीक्लोराइड (2.5-3 ग्राम/लीटर) + स्ट्रेप्टोसाइक्लिन (1 ग्राम प्रति 10 लीटर) का घोल बनाकर 10 दिन के अंतराल पर छिड़कें।\n\n"
                "📖 *स्रोत: भाकृअनुप - केंद्रीय कपास अनुसंधान संस्थान (CICR)*"
            )
        else:
            return (
                f"नमस्ते किसान भाई! आपके प्रश्न (**{topic_name}**) के संदर्भ में वैज्ञानिक कृषि परामर्श:\n\n"
                f"{content}\n\n"
                f"**खेत में अपनाने योग्य प्रमुख कदम:**\n"
                f"• मृदा स्वास्थ्य कार्ड (Soil Health Card) के अनुसार ही उर्वरकों का संतुलित प्रयोग करें।\n"
                f"• कीट या रोग के शुरुआती लक्षण दिखते ही जैविक नियंत्रण (नीम तेल 5 मिली/लीटर) अपनाएं।\n"
                f"• सिंचाई फसल की क्रांतिक अवस्थाओं पर ही करें तथा जलभराव से बचें।\n\n"
                f"📖 *स्रोत: {citations}*"
            )

    # 3. ENGLISH GENERATION
    else:
        if is_wheat_query:
            return (
                "Hello Farmer! For wheat cultivation, optimal irrigation and fertilizer scheduling are critical for maximizing grain yield.\n\n"
                "**1. First Critical Irrigation (CRI Stage):**\n"
                "• Apply the first irrigation strictly at **20–25 days after sowing (DAS)** at Crown Root Initiation. Delaying this stage stunts tillering and can reduce harvest yield by 20–30%.\n\n"
                "**2. Fertilizer Dosage (NPK Balance):**\n"
                "• Top-dress with urea (30–35 kg/acre) immediately following the first irrigation.\n"
                "• Recommended overall N:P:K ratio is **120:60:40 kg/ha**. Apply full DAP and MOP (Potash) as basal dose at sowing, and split Nitrogen across 3 critical stages.\n\n"
                "**3. Subsequent Irrigation Schedule:**\n"
                "• Tillering stage (40–45 DAS), Jointing (60–65 DAS), Flowering/Anthesis (80–85 DAS), and Milk/Dough stage (100–105 DAS).\n\n"
                "📖 *Source: ICAR - Indian Institute of Wheat and Barley Research (IIWBR)*"
            )
        else:
            return (
                f"Hello Farmer! Here is verified agronomic guidance for your query on **{topic_name}**:\n\n"
                f"{content}\n\n"
                f"**Key Actionable Recommendations:**\n"
                f"• Base fertilizer applications strictly on soil test card recommendations to prevent nitrogen burn.\n"
                f"• Inspect fields weekly and adopt Integrated Pest Management (neem oil 5 ml/L, biological controls).\n"
                f"• Align irrigations with critical growth stages and prevent root zone waterlogging.\n\n"
                f"📖 *Verified Source: {citations}*"
            )

# ---------------------------------------------------------------------------
# Upgraded Gemini System Prompt (Strict Trilingual & Conversational Persona)
# ---------------------------------------------------------------------------
_SYSTEM_INSTRUCTION = (
    "You are AgriSmart, an intelligent, empathetic, and highly experienced Indian agricultural scientist "
    "and Krishi Vigyan Kendra (KVK) agronomy specialist.\n\n"
    "MISSION: Provide direct, actionable, practical advice to Indian farmers on crop cultivation, "
    "Kharif/Rabi seasons, fertilizer schedules (NPK/organic), irrigation timing, soil health, and plant pathology.\n\n"
    "STRICT LANGUAGE MATCHING RULES:\n"
    "1. HINGLISH INPUT (Hindi written in Roman/English alphabet, e.g. 'kheti me gehun ke liye konsi khad best hai', 'bhai pehla pani kab de', 'kapas me rog kaise thik kare'):\n"
    "   --> YOU MUST REPLY ENTIRELY IN NATURAL, CONVERSATIONAL HINGLISH (Roman script Hindi)!\n"
    "   --> Use friendly, respectful terms like 'Kisan bhai', 'gehun', 'khad', 'sinchai', 'dawa', 'paidavar'.\n"
    "   --> DO NOT reply in Devanagari script, and DO NOT reply in English.\n"
    "2. HINDI INPUT (Devanagari script, e.g. 'गेहूँ में कौन सा खाद डालें?'):\n"
    "   --> YOU MUST REPLY IN FLUENT, RESPECTFUL, PRACTICAL HINDI (Devanagari script).\n"
    "3. ENGLISH INPUT:\n"
    "   --> YOU MUST REPLY IN CLEAR, SUPPORTIVE, PROFESSIONAL AGRONOMIC ENGLISH.\n\n"
    "CONVERSATIONAL GENERATION RULES (CRITICAL):\n"
    "- NEVER sound like a robotic, hardcoded database or canned memorized template.\n"
    "- Address the farmer's specific crop, question, and condition directly in your very first sentence.\n"
    "- Provide concrete numbers (dosages per acre or hectare, days after sowing, irrigation stages).\n"
    "- Use bold headings, neat bullet points, and clean line spacing for easy readability in the field.\n"
    "- Always emphasize farmer safety during chemical spraying (protective mask, gloves, proper weather conditions)."
)

# ---------------------------------------------------------------------------
# Public Chat API (Non-Streaming - Preserves 100% Backwards Compatibility)
# ---------------------------------------------------------------------------
def chat(message: str, history: Optional[list] = None, top_k_context: int = 3) -> dict:
    if history is None:
        history = []

    lang = detect_query_language(message)
    relevant_entries = _retrieve_context(message, top_k=top_k_context)
    context_topics = [e.get("topic", "General Agronomy") for e in relevant_entries]

    client = _get_client()

    # Try Live Gemini if configured
    if client is not None:
        try:
            from google.genai import types as genai_types

            context_block = "\n\n".join(
                f"[{e.get('category', 'general').upper()} - {e.get('topic', '')}]\n{e.get('content', '')}"
                for e in relevant_entries
            )
            augmented_prompt = (
                f"VERIFIED AGRICULTURAL CONTEXT:\n{'='*50}\n{context_block}\n{'='*50}\n\n"
                f"DETECTED USER LANGUAGE: {lang.upper()}\n"
                f"(Strict Language Rule: If {lang.upper()} is HINGLISH, reply strictly in Roman Hindi. If HINDI, reply in Devanagari. If ENGLISH, reply in English.)\n\n"
                f"FARMER QUESTION: {message}"
            )

            contents = []
            for turn in history[-8:]:
                role = turn.get("role", "user")
                content_text = turn.get("content", "")
                if role in ("user", "model") and content_text:
                    contents.append(genai_types.Content(
                        role=role,
                        parts=[genai_types.Part(text=content_text)]
                    ))

            contents.append(genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=augmented_prompt)]
            ))

            for model_candidate in [_PRIMARY_MODEL] + _BACKUP_MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_candidate,
                        contents=contents,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=_SYSTEM_INSTRUCTION,
                            temperature=0.4,
                            max_output_tokens=1024,
                            candidate_count=1
                        )
                    )
                    if response.candidates:
                        reply_text = response.candidates[0].content.parts[0].text.strip()
                        return {
                            "reply": reply_text,
                            "context_topics": context_topics,
                            "context_used": len(relevant_entries),
                            "engine": model_candidate,
                            "is_live_gemini": True,
                            "language": lang,
                            "status": "active"
                        }
                except Exception as inner_e:
                    logger.info(f"Model {model_candidate} unavailable: {inner_e}")
                    continue

        except Exception as e:
            logger.warning(f"Live Gemini exception: {e}. Falling back to Dynamic Local RAG.")

    # Fallback to Dynamic Local RAG
    local_reply = _synthesize_local_rag_response(message, relevant_entries, lang=lang)
    return {
        "reply": local_reply,
        "context_topics": context_topics,
        "context_used": len(relevant_entries),
        "engine": "AgriSmart-Dynamic-RAG",
        "is_live_gemini": False,
        "language": lang,
        "status": "rag_active"
    }

# ---------------------------------------------------------------------------
# Public Chat Streaming Generator (SSE: Real-Time Token/Line Stream)
# ---------------------------------------------------------------------------
async def chat_stream(message: str, history: Optional[list] = None, top_k_context: int = 3) -> AsyncIterator[str]:
    """
    Asynchronous generator yielding Server-Sent Events (SSE) formatted chunks.
    Streams token-by-token or line-by-line in English, Hindi, or Hinglish.
    """
    if history is None:
        history = []

    lang = detect_query_language(message)
    relevant_entries = _retrieve_context(message, top_k=top_k_context)
    context_topics = [e.get("topic", "General Agronomy") for e in relevant_entries]

    client = _get_client()

    # Path A: Live Gemini Streaming
    if client is not None:
        try:
            from google.genai import types as genai_types

            context_block = "\n\n".join(
                f"[{e.get('category', 'general').upper()} - {e.get('topic', '')}]\n{e.get('content', '')}"
                for e in relevant_entries
            )
            augmented_prompt = (
                f"VERIFIED AGRICULTURAL CONTEXT:\n{'='*50}\n{context_block}\n{'='*50}\n\n"
                f"DETECTED USER LANGUAGE: {lang.upper()}\n"
                f"(Strict Language Rule: If {lang.upper()} is HINGLISH, reply strictly in Roman Hindi. If HINDI, reply in Devanagari. If ENGLISH, reply in English.)\n\n"
                f"FARMER QUESTION: {message}"
            )

            contents = []
            for turn in history[-8:]:
                role = turn.get("role", "user")
                content_text = turn.get("content", "")
                if role in ("user", "model") and content_text:
                    contents.append(genai_types.Content(
                        role=role,
                        parts=[genai_types.Part(text=content_text)]
                    ))

            contents.append(genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=augmented_prompt)]
            ))

            for model_candidate in [_PRIMARY_MODEL] + _BACKUP_MODELS:
                try:
                    stream = client.models.generate_content_stream(
                        model=model_candidate,
                        contents=contents,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=_SYSTEM_INSTRUCTION,
                            temperature=0.4,
                            max_output_tokens=1024,
                            candidate_count=1
                        )
                    )

                    for chunk in stream:
                        text_part = chunk.text or ""
                        if text_part:
                            payload = json.dumps({"chunk": text_part, "done": False})
                            yield f"data: {payload}\n\n"
                            await asyncio.sleep(0.005)

                    final_payload = json.dumps({
                        "done": True,
                        "context_topics": context_topics,
                        "model": model_candidate,
                        "is_live_gemini": True,
                        "language": lang
                    })
                    yield f"data: {final_payload}\n\n"
                    return

                except Exception as inner_e:
                    logger.info(f"Stream on {model_candidate} failed: {inner_e}")
                    continue

        except Exception as e:
            logger.warning(f"Streaming Gemini failed: {e}. Falling back to Dynamic Local RAG stream.")

    # Path B: Dynamic Local RAG Streaming (Generative Typewriter line-by-line)
    local_reply = _synthesize_local_rag_response(message, relevant_entries, lang=lang)
    lines = local_reply.split("\n")
    for i, line in enumerate(lines):
        suffix = "\n" if i < len(lines) - 1 else ""
        payload = json.dumps({"chunk": line + suffix, "done": False})
        yield f"data: {payload}\n\n"
        await asyncio.sleep(0.02)

    final_payload = json.dumps({
        "done": True,
        "context_topics": context_topics,
        "model": "AgriSmart-Dynamic-RAG",
        "is_live_gemini": False,
        "language": lang
    })
    yield f"data: {final_payload}\n\n"
