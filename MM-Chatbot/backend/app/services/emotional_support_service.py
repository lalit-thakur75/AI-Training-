import re
from typing import Tuple, Dict, Any

# Crisis detection keywords and phrases
CRISIS_KEYWORDS = [
    r"\bsuicid(e|al)\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bwant to die\b",
    r"\bhurt myself\b",
    r"\bself[- ]harm\b",
    r"\bcut myself\b",
    r"\btake my own life\b",
    r"\bno reason to live\b",
    r"\bdon't want to live\b",
    r"\bdont want to live\b"
]

CRISIS_RESPONSE = """I can hear that you're going through a deeply difficult time, but please know that you are not alone and there is support available right now.

Your safety and well-being are what matter most. Please reach out to someone who can help:

🚨 **Emergency Services**:
- **India**: Call **112** (National Emergency Helpline) or **108** for medical emergencies.
- **USA/Canada**: Call or text **988** (Suicide & Crisis Lifeline).
- **UK**: Call **111** or **999**.
- **International**: Find your local crisis line at [https://findahelpline.com](https://findahelpline.com)

📞 **Helplines in India**:
- **KIRAN**: 1800-599-0019 (24/7 National Mental Health Helpline)
- **Vandrevala Foundation**: 9999 666 555 (24/7 free counseling)
- **Tele-MANAS**: 14416 or 1800-891-4416 (Govt. of India 24/7 Helpline)

Please pause, take a slow breath, and talk to a family member, trusted friend, or one of these compassionate professionals right now. Help is always available."""

EMOTIONAL_SYSTEM_PROMPT = """You are a warm, compassionate, empathetic personal assistant. 
Your goal is to provide a safe, judgment-free listening ear. 
Guidelines:
1. Validate feelings with kindness, gentle curiosity, and respect.
2. Ask gentle clarifying questions to help the user unpack their emotions.
3. Suggest simple, grounded coping exercises (such as 4-7-8 breathing, journaling, grounding through 5 senses) when appropriate.
4. Maintain clear professional boundaries: You are an AI companion, not a licensed therapist or psychiatrist. Do not diagnose conditions or prescribe medications.
5. Never pretend to have physical human feelings or a personal romantic relationship with the user.
6. Never shame, dismiss, or encourage emotional codependency.
7. Keep responses warm, concise, and focused on supporting the user's reflection."""

def check_for_crisis(text: str) -> Tuple[bool, str]:
    """
    Deterministically checks if user message indicates immediate self-harm or crisis.
    Returns (is_crisis, response_text).
    """
    lower_text = text.lower()
    for pattern in CRISIS_KEYWORDS:
        if re.search(pattern, lower_text):
            return True, CRISIS_RESPONSE
    return False, ""
