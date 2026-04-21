import requests
from config import OLLAMA_HOST, OLLAMA_MODEL
from vector_store import get_similar_examples
import logging
from utils import normalize_text

def classify_message(message: str) -> str:
    """
    Classifies a Telegram message as SAFE or BAN.
    
    Args:
        message: The text content of the Telegram message
        
    Returns:
        "BAN" if the message is a scam/spam, "SAFE" otherwise
    """
    message = normalize_text(message)
    logging.info(f"Normalized text: {message[:300]}")
    examples = get_similar_examples(message)
    system_prompt = """

    You are a Telegram/Discord group moderator. Classify each message as SAFE or BAN. Respond with exactly one word only.

    BAN if the message contains:
    - Financial scams: fake giveaways, guaranteed returns, crypto pump schemes, advance fee fraud
    - Sexual content: explicit solicitation, OnlyFans promotion, adult services
    - Spam: unsolicited mass advertising, bulk messaging services, lists of phone numbers
    - Scam infrastructure: SIP trunking, bulk SMS services, DID numbers, VoIP reselling, anonymous calling — even if phrased as legitimate B2B
    - Academic dishonesty: homework/exam for hire
    - Filter evasion: systematic character substitution (e.g. "fr33", "v!agra") combined with suspicious content
    - Phishing: suspicious links, unknown domains promising rewards or jobs

    SAFE if the message is:
    - Normal conversation, opinions, questions, arguments, humour
    - Lost and found, genuine job posts, community announcements
    - Links to known platforms (github, youtube, linkedin, reddit, etc.)
    - Natural typos, slang, abbreviations, emojis

    Examples:
    {examples}

    Respond with exactly one word: SAFE or BAN


    ## Decision Principle
    Default to SAFE. Only classify as BAN when you are highly confident the message is malicious.
    """

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "think": False,
                "options": {"num_predict": 5, "num_thread": 4},
                "messages": [
                    {"role": "system", "content": system_prompt.format(examples=examples)},
                    {"role": "user", "content": f"<message>{message}</message>"}
                ],
                "stream": False
            },
            timeout=60
        )
        result = response.json()["message"]["content"].strip().upper()
        if result not in ["SAFE", "BAN"]:
            return "SAFE"
        return result
    except requests.Timeout:
        logging.warning("Ollama timeout — defaulting to SAFE")
        return "SAFE"
    except Exception as e:
        logging.error(f"Ollama error: {e}")
        return "SAFE"