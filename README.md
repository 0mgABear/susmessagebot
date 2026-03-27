# Sus Message Bot

Open-source Telegram Bot that is designed to protect the community by banning bad actors who send spam / scam messages.

## Technical Implementation:

1. bot.py will scan any incoming text message (Version 1).
2. Incoming text is sent to moderator.py, where it's first converted into embedding (defined in vector_store.py).
3. Input text embedding is then compared with current existing labelled examples to retrieve most similar examples. (Retrieval-Augmented Generation)
4. Examples and system prompt are in tandem fed to the model, which will return a singular classification: BAN or SAFE.
5. BAN or SAFE will be passed on to bot.py

## Tech Stack:

1. Ollama LLM
   a. LLM model: qwen2.5:3b
   b. Embedding Model: all-MiniLM-L6-v2
2. ChromaDB (for vector storage)
3. Oracle VPS - for 24/7 availability and the generous free tier.

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

## Contributing

Contributions are welcome! If you have real-world scam/spam examples to add, or want to improve the prompt or architecture, feel free to open a pull request.

Please ensure:

- New examples are added via `seeds.py`
- Code follows the existing structure and includes docstrings
- No API keys or tokens are committed

## Roadmap

- [ ] V2: Image moderation (multimodal model support)
- [ ] V2: Batch example ingestion
- [ ] V2: Similarity threshold tuning interface
