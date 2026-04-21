import requests
from config import OLLAMA_HOST, OLLAMA_MODEL
from vector_store import get_similar_examples
import unicodedata
import logging

def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def classify_message(message: str) -> str:
    """
    Classifies a Telegram message as SAFE or BAN.
    
    Args:
        message: The text content of the Telegram message
        
    Returns:
        "BAN" if the message is a scam/spam, "SAFE" otherwise
    """
    message = normalize_text(message)
    logging.info(f"Normalized text: {message[:100]}")
    examples = get_similar_examples(message)
    system_prompt = """

    ## Role 
    You are a moderator for Telegram group chats.

    ## Task
    Classify each message as either SAFE or BAN. Respond with exactly one word: SAFE or BAN. No explanation, punctuation, or additional text.

    ## Decision Principle
    Default to SAFE. Only classify as BAN when you are highly confident the message is malicious. A false positive (banning a legitimate user) is worse than a false negative (missing a scammer).

    ## BAN Categories
    Classify as BAN only if the message clearly falls into one or more of these categories:
    
    **Financial scams**
    - Fake giveaways or prize announcements (e.g. "You have been selected to receive...")
    - Guaranteed investment returns or passive income schemes
    - Pump-and-dump crypto schemes or fake trading signals
    - Advance fee fraud (e.g. "Send $50 to unlock your $5,000 reward")

    **Sexual content**
    - Pornographic content or explicit sexual solicitation
    - Links to adult content platforms or OnlyFans solicitation
    - Soliciting intimate images or services for payment
    - Tagging a username that is suggestive, promoting sexual services and/or content.

    **Spam and advertising**
    - Unsolicited mass advertising with no relevance to the group (e.g. promotion of marketing for crypto groups)
    - Repeated promotional messages for commercial services
    - Bulk messaging patterns (e.g. lists of phone numbers, country codes for sale)

    **Academic dishonesty**
    - Assignment completion services, homework for hire
    - Exam cheating services, paid coursework

    **Filter evasion**
    - Deliberate character substitution to evade keyword filters (e.g. "fr33", "stiII", "v!agra", "gi ving away")
    - Intentional word splitting to bypass detection (e.g. "give a way", "bit co in")
    - Note: Distinguish between evasion attempts and natural typos. Evasion involves systematic substitution of specific characters, usually in combination with other suspicious content.

    **Suspicious links**
    - Links to unknown domains promising rewards, prizes, jobs, or services
    - Phishing links disguised as legitimate platforms
    - URL shorteners leading to suspicious destinations

    ## SAFE Categories
    The following must always be classified as SAFE, even if they seem unusual:

    **Normal conversation**
    - Any genuine discussion, question, or opinion on any topic (politics, health, finance, technology, relationships)
    - Venting, complaints, debates, or arguments between members
    - Satire, sarcasm, humour, and memes
    - Messages containing profanity or strong language without malicious intent

    **Legitimate posts**
    - Lost and found announcements
    - Genuine job or recruitment posts, even if they mention blockchain, AI, crypto, or remote work
    - Community announcements or event sharing
    - Personal sharing (achievements, life updates, news)

    **Legitimate links**
    - Well-known platforms: github.com, youtube.com, google.com, linkedin.com, reddit.com, twitter.com, instagram.com, facebook.com, tiktok.com, news sites, government sites
    - Links shared in the context of a genuine discussion

    **Natural language patterns**
    - Common typos and autocorrect errors (e.g. "teh", "wiht", "ur", "u", "gonna", "wanna")
    - Local slang, dialect, or code-switching (e.g. Singlish: "lah", "lor", "sia", "bro")
    - Occasional repeating of letters (e.g. "frfr", "yeaa", "ikik")
    - Abbreviations common in casual texting (e.g. "tbh", "imo", "lol", "omg", "ngl")
    - Possible representation of emojis in text (e.g. ":)", ":D")
    - Tone indicators commonly used online (e.g. "/j" for joking, "/s" for sarcasm, "/hj" for half-joking)
    - Informal grammar and punctuation

    ## Examples
    {examples}

    ## Output Format
    Respond with exactly one word: SAFE or BAN
    """

    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "think": False,
            "messages": [
                {"role": "system", "content": system_prompt.format(examples=examples)},
                {"role": "user", "content": f"<message>{message}</message>"}
            ],
            "stream": False
        }
    )
    result = response.json()["message"]["content"].strip().upper()
    if result not in ["SAFE", "BAN"]:
        return "SAFE"
    return result