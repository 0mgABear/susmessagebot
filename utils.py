import unicodedata
import re

def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

INSTANT_BAN_PATTERNS = [
    r'\bsip\s*trunk\b',
    r'\bbulk\s*sms\b',
    r'\bdid\s*numbers?\b',
    r'\bvoip\s*resell',
    r'\bspoofing\b',
    r'\bonlyfans\b',
    r'\bhomework\s*for\s*hire\b',
    r'\bexam\s*cheat',
    r'\badvance\s*fee\b',
    r'\bpassive\s*income\b',
    r'\bguaranteed\s*(return|profit|income)\b',
]

def pre_filter(text: str) -> bool:
    """Returns True if message should be instantly banned without LLM."""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in INSTANT_BAN_PATTERNS)