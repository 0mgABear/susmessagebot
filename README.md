# SusMessageBot

Open-source Telegram AI Moderation Bot that is designed to protect the community by banning bad actors who send spam / scam messages.

> ⚠️ This branch runs a **fully self-hosted LLM via Ollama** and requires a capable VPS (recommended: Oracle Cloud free ARM instance — 4 cores, 24GB RAM). If you are unable to provision one, see the [groq-approach](https://github.com/0mgABear/susmessagebot/tree/groq-approach) branch which uses Groq's free API instead and runs on a lightweight e2-micro instance.

## Why

Singaporeans lost a record S$1.1 billion to scams in 2024 and $913.1 million in 2025. Telegram is also explicitly named by SPF as one of the top platforms exploited by scammers. Existing moderation tools rely on static keyword rules that scammers trivially bypass with character substitution and deliberate typos. This bot was built to fight back using semantic understanding instead of keyword matching.

## Technical Implementation:

1. `bot.py` scans every incoming text message (Version 1 — exploring image moderation in V2).
2. Incoming text is sent to `moderator.py`, where it is first converted into an embedding (defined in `vector_store.py`).
3. Input text embedding is then compared with current existing labelled examples to retrieve most similar examples. (Retrieval-Augmented Generation)
4. Examples and system prompt are in tandem fed to the local Ollama LLM, which will return a singular classification: `BAN` or `SAFE`.
5. `bot.py` acts on the classification — deleting the message and banning the user if `BAN`, doing nothing if `SAFE`.

## Tech Stack:

1. **LLM:** Ollama (`qwen2.5:3b`)
2. **Vector Store:** ChromaDB
3. **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
4. **Bot Framework:** python-telegram-bot
5. **Hosting:** Oracle Cloud Free Tier (ARM instance recommended)

## Pros

1. Fully self-hosted — messages never leave your server
2. No API costs or external dependencies
3. Full control over the model

## Cons

1. Requires a capable VPS — won't run well on e2-micro
2. Slower inference than cloud APIs when running on CPU
3. Oracle Cloud free ARM instances are frequently out of capacity

## Pre-Requisite:

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

## Setup

1. Clone the repository.

2. Create and activate venv

```bash
python3.10 -m venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Telegram Bot Token:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

5. Pull the LLM model

```bash
ollama pull qwen2.5:3b
```

6. Seed ChromaDB with initial examples

```bash
python seeds.py
```

7. Run the bot

```bash
python bot.py
```

## Known Issue

The RAG examples are currently not being passed into the moderator prompt. This is a known bug that will be fixed in a future update. The bot still classifies messages using the LLM's base knowledge.

## Roadmap

- [ ] Fix RAG example injection into prompt
- [ ] V2: Human-in-the-Loop (HITL) feedback system _(implemented in groq-approach branch)_
- [ ] V2: Observability dashboard _(implemented in groq-approach branch)_
- [ ] V2: Image moderation (multimodal model support)
- [ ] V2: Batch example ingestion
- [ ] V2: Similarity threshold tuning interface

## Contributing

Contributions are welcome! If you have real-world scam/spam examples to add, or want to improve the prompt or architecture, feel free to open a pull request.

Please ensure:

- New examples are added via `seeds.py`
- Code follows the existing structure and includes docstrings
- No API keys or tokens are committed

## Sponsorship

Running this bot at scale requires paid infrastructure. If this project has been useful to you and you'd like to help cover hosting costs or support further development, consider sponsoring:

- ⭐ Star the repo to show support
- ❤️ [GitHub Sponsors](https://github.com/sponsors/0mgABear)
- 💬 Reach out via Telegram: @commonertech
- 📧 Contact: hello@commonertech.dev
- ☕ [Ko-fi](https://ko-fi.com/commonertech)
