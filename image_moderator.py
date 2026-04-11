import requests
import base64
from config import OLLAMA_HOST, OLLAMA_MODEL

def classify_image(image_bytes: bytes) -> str:
    """
    Classifies a Telegram image as SAFE or BAN using Ollama's multimodal capabilities.

    Args:
        image_bytes: Raw image bytes downloaded from Telegram

    Returns:
        "BAN" if the image is a scam/spam, "SAFE" otherwise
    """
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """You are a moderator for Telegram group chats.

Classify this image as either SAFE or BAN. Respond with exactly one word: SAFE or BAN. No explanation, punctuation, or additional text.

Classify as BAN if the image contains:
- Scam job offers or fake income schemes
- Sexual or explicit content
- QR codes or links to suspicious sites
- Fake receipts or payment proofs used in scams
- Unsolicited advertisements or spam
- Content promoting sexual services

Default to SAFE if unsure. A false positive (banning a legitimate user) is worse than a false negative.

Respond with exactly one word: SAFE or BAN"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "think": False,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64]
                }
            ],
            "stream": False
        }
    )
    result = response.json()["message"]["content"].strip().upper()
    if result not in ["SAFE", "BAN"]:
        return "SAFE"
    return result