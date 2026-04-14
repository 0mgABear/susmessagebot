# SusMessageBot

Open-source Telegram AI Moderation Bot that is designed to protect the community by banning bad actors who send spam / scam messages.

> ⚠️ This branch runs a **fully self-hosted LLM via Ollama** and requires a capable VPS (recommended: Oracle Cloud free ARM instance — 4 OCPUs, 24GB RAM). If you are unable to provision one, see the [groq-approach](https://github.com/0mgABear/susmessagebot/tree/groq-approach) branch which uses Groq's free API instead and runs on a lightweight e2-micro instance.

## Branding

This is proudly a @commonertech product.

## Why

Singaporeans lost a record S$1.1 billion to scams in 2024 and S$913.1 million in 2025. Telegram is also explicitly named by SPF as one of the top platforms exploited by scammers. Existing moderation tools rely on static keyword rules that scammers trivially bypass with character substitution and deliberate typos. This bot was built to fight back using semantic understanding instead of keyword matching.

## Live Monitoring Dashboard

[susmessagebot.commonertech.dev/dashboard](https://susmessagebot.commonertech.dev/dashboard)

## Architecture (Diagram)

coming soon

## Technical Implementation:

1. `bot.py` scans every incoming text message.
2. Incoming text is sent to `moderator.py`, where it is first converted into an embedding (defined in `vector_store.py`).
3. Input text embedding is then compared with existing labelled examples in ChromaDB to retrieve the most similar ones. (Retrieval-Augmented Generation)
4. Retrieved examples and the system prompt are fed together to the local Ollama LLM, which returns a single classification: `BAN` or `SAFE`.
5. URLs in the message are extracted and checked against a live malware blocklist (URLhaus) by `url_moderator.py`. Unknown domains are classified by the LLM.
6. If text and URL checks pass, any `@usernames` in the message are scraped from `t.me` by `username_moderator.py` and their bios classified by the LLM.
7. `bot.py` acts on the final classification — deleting the message and banning the user if `BAN`, doing nothing if `SAFE`.
8. Images are handled separately by `image_moderator.py` — text is extracted via OCR (pytesseract) and passed to the same text classifier. Scammers who post screenshots don't get a free pass.
9. On every ban, admins are notified in the group with two inline buttons: ✅ Correct Ban or ❌ Wrong Ban.
10. Admin feedback is used to update ChromaDB in real time and sync `seeds.py` to the GitHub repository via the GitHub API — keeping the repository as the source of truth for all labelled examples. (Human-in-the-Loop)
11. Every classification, ban, and false positive is tracked as a Prometheus metric, scraped by Grafana Alloy, and visualized in a live Grafana Cloud dashboard.
12. Admins (or users pending admin approval) can use `/report` to flag missed scams — adding them to ChromaDB, syncing to GitHub, and tracking as false negatives in the monitoring dashboard.
13. Group and member counts are tracked automatically — every new group the bot is added to is recorded, with member counts updated daily.

## Tech Stack:

1. **LLM:** Ollama (`gemma4:e2b`)
2. **Vector Store:** ChromaDB
3. **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
4. **Image OCR:** pytesseract + Pillow
5. **URL Analysis:** URLhaus blocklist + LLM fallback
6. **Profile Scraping:** BeautifulSoup (`t.me`)
7. **Bot Framework:** python-telegram-bot
8. **Hosting:** Oracle Cloud Free Tier (ARM instance — 4 OCPUs, 24GB RAM)
9. **Tunnel:** Cloudflare Tunnel
10. **Example Sync:** GitHub API
11. **Observability & Monitoring:** Prometheus + Grafana Alloy + Grafana Cloud
12. **CI/CD:** GitHub Actions

## Human-in-the-Loop (HITL) Feedback System

Every time the bot bans a user, admins are presented with two buttons in the group:

- ✅ **Correct Ban** — confirms the ban and adds the message as a BAN example to ChromaDB and `seeds.py`
- ❌ **Wrong Ban** — marks it as a false positive, unbans the user, and adds the message as a SAFE example to ChromaDB and `seeds.py`

This means the bot gets smarter over time with every admin correction, without any manual retraining.

Credit: This HITL feedback idea was proposed by Dr Mo Yin, a very close and treasured friend of mine. Thank you for the friendship!

## /report Command

If the bot misses a scam (false negative), it can be manually reported:

- **Admins** — reply to the scam message with `/report`. The user is immediately banned and the message is added to training examples.
- **Non-admins** — reply with `/report` to flag for admin review. Admins are notified with ✅ Confirm Ban or ❌ Dismiss buttons.

False negatives are tracked separately in the monitoring dashboard.

## /stats Command

Admins can type `/stats` in any group to get a summary:

- Groups protected
- Members protected
- Messages scanned
- Total bans
- Accuracy rate (based on human-in-the-loop feedback)

Accuracy is calculated as: confirmed correct classifications / (correct + false positives + false negatives). All safe classifications are assumed correct until an admin uses `/report` to flag a missed scam.

## Pros

1. Fully self-hosted — messages never leave your server
2. No API costs or rate limits
3. Multimodal — detects scams in text, images, URLs, and user profiles
4. Self-improving via HITL feedback
5. Full control over the model and infrastructure

## Cons

1. Requires a capable VPS — minimum 10GB RAM recommended
2. Slower inference than cloud APIs when running on CPU
3. Oracle Cloud free ARM instances are frequently out of capacity — workaround: use a PAYG account staying within free tier limits

## Key Caveat

As this bot is in the initial deployment stages, please expect a fair number of false positives. As more people use the bot and admins participate in the HITL review, accuracy will increase over time.

## Data Privacy

All message content is processed entirely on your own server. No message text is ever sent to any third-party API or external service. The LLM runs locally via Ollama, embeddings are generated locally via sentence-transformers, and all data stays within your infrastructure.

The only external calls made are:

- Telegram API (to receive and act on messages — inherent to any Telegram bot)
- GitHub API (to sync labelled examples to your own repository)
- Grafana Cloud (metrics only — message content is never included in metrics)
- URLhaus (domain blocklist download only — no message content sent)
- `t.me` (public profile scraping for username analysis — username only, no message content)

## Pre-Requisite:

- Python 3.12+
- [Ollama](https://ollama.com) installed and running
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- `tesseract-ocr` installed on your system (`sudo apt install tesseract-ocr`)

## Setup

1. Clone the repository.

2. Create and activate venv

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements-vps.txt
```

4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
TELEGRAM_BOT_TOKEN=your_token_here
GITHUB_TOKEN=your_github_pat_here
GITHUB_REPO=yourusername/susmessagebot
GITHUB_BRANCH=main
OLLAMA_HOST=http://localhost:port
OLLAMA_MODEL=gemma4:e2b
```

5. Pull the LLM model

```bash
ollama pull gemma4:e2b
```

6. Seed ChromaDB with initial examples

```bash
python seeds.py
```

7. Run the bot

```bash
python bot.py
```

## Roadmap

- [x] RAG example injection into prompt
- [x] Human-in-the-Loop (HITL) feedback system
- [x] Observability dashboard
- [x] CI/CD via GitHub Actions
- [x] Image moderation via OCR
- [x] URL analysis with malware blocklist
- [x] Username/profile analysis via t.me scraping
- [ ] Voice message moderation
- [ ] Multi-language support
- [ ] Video moderation
- [ ] Full multimodal image RAG
- [ ] Agentic workflows with native function calling
- [ ] Discord support

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

Every contribution helps keep the bot running and the project maintained. Thank you! 🙏
