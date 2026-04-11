import re
import requests
from urllib.parse import urlparse
from config import OLLAMA_HOST, OLLAMA_MODEL

# Blocklist cache
_blocklist: set = set()

BLOCKLIST_URL = "https://malware-filter.gitlab.io/malware-filter/urlhaus-filter-domains-online.txt"

URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')

SAFE_DOMAINS = {
    "github.com", "youtube.com", "google.com", "linkedin.com",
    "reddit.com", "twitter.com", "instagram.com", "facebook.com",
    "tiktok.com", "t.me", "telegram.org", "wikipedia.org"
}

def load_blocklist() -> None:
    """Download and cache the malware domain blocklist."""
    global _blocklist
    try:
        response = requests.get(BLOCKLIST_URL, timeout=10)
        domains = set()
        for line in response.text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                domains.add(line.lower())
        _blocklist = domains
    except Exception as e:
        import logging
        logging.error(f"Failed to load blocklist: {e}")

def _extract_urls(text: str) -> list:
    """Extract all URLs from a message."""
    return URL_PATTERN.findall(text)

def _get_final_url(url: str) -> str:
    """Follow redirects to get the final destination URL."""
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except Exception:
        return url

def _get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""

def _is_on_blocklist(domain: str) -> bool:
    """Check if domain is in the cached blocklist."""
    return domain in _blocklist

def _classify_url_with_llm(url: str) -> str:
    """Use Gemma4 to classify a URL as SAFE or BAN."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "think": False,
            "messages": [
                {
                    "role": "user",
                    "content": f"""You are a security analyst. Classify this URL as SAFE or BAN.

Classify as BAN if the URL looks like:
- A phishing or scam site
- A suspicious unknown domain promising rewards, prizes or jobs
- A URL shortener hiding a suspicious destination
- A domain with random characters suggesting auto-generation

Classify as SAFE if it's a well-known legitimate site or looks like a normal website.

URL: {url}

Respond with exactly one word: SAFE or BAN"""
                }
            ],
            "stream": False
        },
        timeout=30
    )
    result = response.json()["message"]["content"].strip().upper()
    return result if result in ["SAFE", "BAN"] else "SAFE"

def analyze_urls(text: str) -> str:
    """
    Extract and analyze all URLs in a message.

    Returns "BAN" if any URL is suspicious, "SAFE" otherwise.
    """
    urls = _extract_urls(text)
    if not urls:
        return "SAFE"

    for url in urls:
        final_url = _get_final_url(url)
        domain = _get_domain(final_url)

        if not domain:
            continue

        # Skip known safe domains
        if domain in SAFE_DOMAINS:
            continue

        # Check blocklist first (fast)
        if _is_on_blocklist(domain):
            return "BAN"

        # Fall back to LLM classification
        result = _classify_url_with_llm(final_url)
        if result == "BAN":
            return "BAN"

    return "SAFE"