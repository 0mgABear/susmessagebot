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