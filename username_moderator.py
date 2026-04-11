import re
import requests
from bs4 import BeautifulSoup
from config import OLLAMA_HOST, OLLAMA_MODEL

USERNAME_PATTERN = re.compile(r'@([a-zA-Z0-9_]{4,32})')

async def analyze_usernames(text: str, bot) -> str:
    usernames = USERNAME_PATTERN.findall(text)
    if not usernames:
        return "SAFE"

    for username in usernames:
        try:
            chat = await bot.get_chat(f"@{username}")
            bio = chat.bio or ""
            name = chat.full_name or ""
        except Exception:
            # Fallback: scrape t.me page
            name, bio = _scrape_tme_profile(username)

        if not bio and not name:
            continue

        result = _classify_username(username, name, bio)
        if result == "BAN":
            return "BAN"

    return "SAFE"


def _scrape_tme_profile(username: str) -> tuple:
    """Scrape name and bio from t.me/username as fallback."""
    try:
        response = requests.get(
            f"https://t.me/{username}",
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find("meta", property="og:title")
        bio = soup.find("meta", property="og:description")
        name = name["content"] if name else ""
        bio = bio["content"] if bio else ""
        return name, bio
    except Exception:
        return "", ""
    
def _classify_username(username: str, name: str, bio: str) -> str:
    """Use Gemma4 to classify a Telegram user based on their profile."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "think": False,
            "messages": [
                {
                    "role": "user",
                    "content": f"""You are a Telegram moderator. Classify this user profile as SAFE or BAN.

Classify as BAN if the profile promotes:
- Sexual services or adult content
- Scam job offers or fake income schemes
- Cryptocurrency scams or fake investment returns
- Phishing or malicious links

Username: @{username}
Display name: {name}
Bio: {bio}

Respond with exactly one word: SAFE or BAN"""
                }
            ],
            "stream": False
        },
        timeout=30
    )
    result = response.json()["message"]["content"].strip().upper()
    return result if result in ["SAFE", "BAN"] else "SAFE"