# SusMessageBot

Open-source AI Moderation Bot for **Telegram** and **Discord**, designed to protect communities by detecting and banning scammers using semantic AI — not keyword rules.

> ⚠️ This branch runs a **fully self-hosted LLM via Ollama** and requires a capable VPS (recommended: Oracle Cloud free ARM instance — 4 OCPUs, 24GB RAM). If you are unable to provision one, see the [groq-approach](https://github.com/0mgABear/susmessagebot/tree/groq-approach) branch which uses Groq's free API instead and runs on a lightweight e2-micro instance.

## Branding

This is proudly a @commonertech product.

## Why

Singaporeans lost a record S$1.1 billion to scams in 2024 and S$913.1 million in 2025. Telegram is also explicitly named by SPF as one of the top platforms exploited by scammers. Existing moderation tools rely on static keyword rules that scammers trivially bypass with character substitution and deliberate typos. This bot was built to fight back using semantic understanding instead of keyword matching.

## Live Monitoring Dashboard

[susmessagebot.commonertech.dev/dashboard](https://susmessagebot.commonertech.dev/dashboard)

Tested and working on Chrome, Edge, Brave, Safari, and Firefox. Requires localStorage to be enabled — privacy-hardened browsers (e.g. LibreWolf) may need to allow localStorage for the dashboard domain.

## Architecture (Diagram)

coming soon

## Platform Support

| Feature                   | ![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white) | ![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white) |
| ------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Text moderation           | ✅                                                                                      | ✅                                                                                   |
| Image moderation (OCR)    | ✅                                                                                      | ✅                                                                                   |
| URL analysis              | ✅                                                                                      | ✅                                                                                   |
| Username/profile analysis | ✅                                                                                      | ❌                                                                                   |
| HITL feedback buttons     | ✅                                                                                      | ✅                                                                                   |
| /report command           | ✅                                                                                      | ✅ (@ mention + context menu)                                                        |
| /stats command            | ✅                                                                                      | ❌                                                                                   |
| Group/member tracking     | ✅                                                                                      | ✅                                                                                   |

## Technical Implementation

### Telegram (`bot.py`)

1. Every incoming text message is classified by `moderator.py` — converted into an embedding, compared against labelled examples in ChromaDB (RAG), and fed to the local Ollama LLM for a `BAN` or `SAFE` verdict.
2. URLs in the message are extracted and checked against a live malware blocklist (URLhaus) by `url_moderator.py`. Unknown domains are classified by the LLM.
3. If text and URL checks pass, any `@usernames` in the message are scraped from `t.me` by `username_moderator.py` and their bios classified by the LLM.
4. Images are handled by `image_moderator.py` — text is extracted via OCR (pytesseract) and passed to the same text classifier.
5. On every ban, admins are notified with ✅ Correct Ban or ❌ Wrong Ban buttons.
6. Admin feedback updates ChromaDB in real time and syncs `seeds.py` to GitHub via the GitHub API (Human-in-the-Loop).
7. Every classification, ban, and false positive is tracked as a Prometheus metric and visualized in a live Grafana Cloud dashboard.

### Discord (`bot_discord.py`)

1. Every incoming message is classified using the same text, image, and URL classifiers as the Telegram bot.
2. Admins can report missed scams by replying to a message and tagging `@SusMessageBot`, or via right-click → Apps → **Report to SusMessageBot**.
3. HITL feedback buttons (✅ Correct Ban / ❌ Wrong Ban) are sent on every ban for admin review.
4. On joining a new server, the bot sends a setup message with required permissions.

## Tech Stack

| Component              | Technology                                       |
| ---------------------- | ------------------------------------------------ |
| LLM                    | Ollama (`gemma4:e2b`)                            |
| Vector Store           | ChromaDB                                         |
| Embeddings             | sentence-transformers (`all-MiniLM-L6-v2`)       |
| Image OCR              | pytesseract + Pillow                             |
| URL Analysis           | URLhaus blocklist + LLM fallback                 |
| Profile Scraping       | BeautifulSoup (`t.me`)                           |
| Telegram Bot Framework | python-telegram-bot                              |
| Discord Bot Framework  | discord.py                                       |
| Hosting                | Oracle Cloud Free Tier (ARM — 4 OCPUs, 24GB RAM) |
| Tunnel                 | Cloudflare Tunnel                                |
| Example Sync           | GitHub API                                       |
| Observability          | Prometheus + Grafana Alloy + Grafana Cloud       |
| CI/CD                  | GitHub Actions                                   |

## Human-in-the-Loop (HITL) Feedback System

Every time the bot bans a user, admins are presented with two buttons:

- ✅ **Correct Ban** — confirms the ban and adds the message as a BAN example to ChromaDB and `seeds.py`
- ❌ **Wrong Ban** — marks it as a false positive, unbans the user, and adds the message as a SAFE example to ChromaDB and `seeds.py`

The bot gets smarter over time with every admin correction — no manual retraining needed.

Credit: This HITL feedback idea was proposed by Dr Mo Yin, a very close and treasured friend of mine. Thank you for the friendship!

## Telegram: /report Command

- **Admins** — reply to the scam message with `/report`. The user is immediately banned and the message is added to training examples.
- **Non-admins** — reply with `/report` to flag for admin review. Admins are notified with ✅ Confirm Ban or ❌ Dismiss buttons.

## Discord: Reporting

- **Reply + @SusMessageBot** — reply to any suspicious message and tag `@SusMessageBot`. Admins get an immediate ban; non-admins trigger an admin review.
- **Right-click → Apps → Report to SusMessageBot** — context menu report for any message.

## /stats Command (Telegram only)

Admins can type `/stats` in any group to get a live summary:

- Groups protected
- Members protected
- Messages scanned
- Total bans
- Accuracy rate (based on HITL feedback)

Accuracy is calculated as: confirmed correct classifications / (correct + false positives + false negatives).

## Pros

1. Fully self-hosted — messages never leave your server
2. No API costs or rate limits
3. Multi-platform — Telegram and Discord
4. Multimodal — detects scams in text, images, and URLs
5. Self-improving via HITL feedback
6. Full control over the model and infrastructure

## Cons

1. Requires a capable VPS — minimum 10GB RAM recommended
2. Slower inference than cloud APIs when running on CPU
3. Oracle Cloud free ARM instances are frequently out of capacity — workaround: use a PAYG account staying within free tier limits

## Key Caveat

As this bot is in the initial deployment stages, please expect a fair number of false positives. As more people use the bot and admins participate in the HITL review, accuracy will increase over time.

## Data Privacy

All message content is processed entirely on your own server. No message text is ever sent to any third-party API or external service.

The only external calls made are:

- Telegram/Discord API (to receive and act on messages — inherent to any bot)
- GitHub API (to sync labelled examples to your own repository)
- Grafana Cloud (metrics only — message content is never included)
- URLhaus (domain blocklist download only — no message content sent)
- `t.me` (public profile scraping for username analysis — username only, no message content)

## Pre-Requisites

- Python 3.12+
- [Ollama](https://ollama.com) installed and running
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- A Discord Bot Token from the [Discord Developer Portal](https://discord.com/developers/applications)
- `tesseract-ocr` installed on your system (`sudo apt install tesseract-ocr`)

## Setup

1. Clone the repository.

2. Create and activate venv:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements-vps.txt
```

4. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_BOT_TOKEN=your_token_here
DISCORD_BOT_TOKEN=your_token_here
GITHUB_TOKEN=your_github_pat_here
GITHUB_REPO=yourusername/susmessagebot
GITHUB_BRANCH=main
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b
```

5. Pull the LLM model:

```bash
ollama pull gemma4:e2b
```

6. Seed ChromaDB with initial examples:

```bash
python seeds.py
```

7. Run the Telegram bot:

```bash
python bot.py
```

8. Run the Discord bot:

```bash
python bot_discord.py
```

## Roadmap

- [x] RAG example injection into prompt
- [x] Human-in-the-Loop (HITL) feedback system
- [x] Observability dashboard
- [x] CI/CD via GitHub Actions
- [x] Image moderation via OCR
- [x] URL analysis with malware blocklist
- [x] Username/profile analysis via t.me scraping
- [x] Discord support
- [ ] Voice message moderation
- [ ] Multi-language support
- [ ] Video moderation
- [ ] Full multimodal image RAG
- [ ] Agentic workflows with native function calling

## Contributing

Contributions are welcome! If you have real-world scam/spam examples to add, or want to improve the prompt or architecture, feel free to open a pull request.

Please ensure:

- New examples are added via `seeds.py`
- Code follows the existing structure and includes docstrings
- No API keys or tokens are committed

## Sponsorship

Running this bot at scale requires paid infrastructure. If this project has been useful to you, consider supporting:

- ⭐ Star the repo to show support
- ❤️ [GitHub Sponsors](https://github.com/sponsors/0mgABear)
- 💬 Reach out via Telegram: @commonertech
- 📧 Contact: hello@commonertech.dev
- ☕ [Ko-fi](https://ko-fi.com/commonertech)

Every contribution helps keep the bot running and the project maintained. Thank you! 🙏
