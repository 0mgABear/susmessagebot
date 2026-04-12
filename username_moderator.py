import re
import requests
from bs4 import BeautifulSoup
from config import OLLAMA_HOST, OLLAMA_MODEL
import logging
import asyncio

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
            name, bio = _scrape_tme_profile(username)

        if not bio and not name:
            continue

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _classify_username, username, name, bio)
        if result == "BAN":
            return "BAN"

    return "SAFE"



def _scrape_tme_profile(username: str) -> tuple:
    """Scrape name and bio from t.me/username as fallback."""
    try:
        logging.info(f"Scraping t.me/{username}...")
        response = requests.get(
            f"https://t.me/{username}",
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.find(class_="tgme_page_title")
        bio = soup.find(class_="tgme_page_description")
        name = name.get_text(strip=True) if name else ""
        bio = bio.get_text(strip=True) if bio else ""
        logging.info(f"Scraped @{username} — name: '{name}', bio: '{bio}'")
        return name, bio
    except Exception as e:
        logging.error(f"Failed to scrape t.me/{username}: {e}")
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
                    "content": f"""You are a moderator for Singapore Telegram group chats protecting members from scams.

                In Singapore, common scam patterns include fake investment schemes, trading signal scams, and job scams. Be conservative — when in doubt, classify as BAN.

                Classify as BAN if the profile promotes:
                - Investment trading, forex, crypto, or financial returns
                - Sexual services or adult content  
                - Job offers or income schemes
                - Any unsolicited commercial service

                Classify as SAFE only if the profile is clearly a personal account, legitimate business, or community group with no commercial solicitation.

                Username: @{username}
                Display name: {name}
                Bio: {bio}

                Respond with exactly one word: SAFE or BAN"""
                }
            ],
            "stream": False
        },
        timeout=120
    )
    result = response.json()["message"]["content"].strip().upper()
    return result if result in ["SAFE", "BAN"] else "SAFE"