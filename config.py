import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://susmessagebot.commonertech.dev")
USE_POLLING = os.getenv("USE_POLLING", "false").lower() == "true"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 1.0
MAX_EXAMPLES = 5 

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")