# Branch: groq-approach

## Branding

This is proudly a @commonertech product.

Contingency Plan in the event that there is insufficient capacity on Oracle to provision a VPS.

# Technical Implementation:

1. `bot.py` scans every incoming text message (Version 1 — exploring image moderation in V2).
2. Incoming text is sent to `moderator.py`, where it is first converted into an embedding (defined in `vector_store.py`).
3. Input text embedding is then compared with current existing labelled examples to retrieve most similar examples. (Retrieval-Augmented Generation)
4. Examples and system prompt are in tandem fed to Groq, which will return a singular classification: `BAN` or `SAFE`.
5. `bot.py` acts on the classification — deleting the message and banning the user if `BAN`, doing nothing if `SAFE`.
6. On every ban, admins are notified in the group with two inline buttons: **✅ Correct Ban** or **❌ Wrong Ban**.
7. Admin feedback is used to update ChromaDB in real time and sync `seeds.py` to the GitHub repository via the GitHub API — keeping the repository as the source of truth for all labelled examples. (Human-in-the-Loop)

# Tech Stack:

1. **LLM:** Groq (`llama-3.1-8b-instant`)
2. **Vector Store:** ChromaDB
3. **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
4. **Bot Framework:** python-telegram-bot
5. **Hosting:** Google Cloud Free Tier (e2-micro instance)
6. **Webhooks:** python-telegram-bot built-in + Cloudflare (HTTPS termination)
7. **Example Sync:** GitHub API
8. **Observability & Monitoring:** Prometheus (`prometheus_client`) + Grafana Alloy + Grafana Cloud

## Human-in-the-Loop (HITL) Feedback System

Every time the bot bans a user, admins are presented with two buttons in the group:

- **✅ Correct Ban** — confirms the ban and adds the message as a `BAN` example to ChromaDB and `seeds.py`
- **❌ Wrong Ban** — marks it as a false positive, unbans the user, and adds the message as a `SAFE` example to ChromaDB and `seeds.py`

This means the bot gets smarter over time with every admin correction, without any manual retraining.

_Credit: This HITL feedback idea was proposed by Dr Mo Yin, a very close and treasured friend of mine. Thank you for the the friendship!_

## Additional Details:

As of date of creation (30 March 2026), I have yet been unable to provision an Oracle Cloud VPS Instance due to consistently meeting "Host Out of Capacity" errors.
This is expected as it's understandable that everyone would want to sign up for their generous free tier.
As such, this is an interim workaround to use Groq API instead of self-hosting an LLM (which will be attempted until succeeding).

## Pros:

1. Lightweight, able to be run on a smaller free VPS instance (such as Google Cloud e2-micro instance)
2. No GPU/CPU overhead - faster inference than self-hosted on CPU
3. Easier setup - no Ollama installation required

## Cons:

1. Not fully self-hosted - messages are sent to Groq's servers (potential privacy consideration)
2. Dependency on Groq's availability and free tier continuity
3. Not suitable for high-volume multi-group deployments

## Key Caveat:

As this bot is in the initial deployment stages, please do expect a fair number of false positives. As more people use the bot and admins participate in the HITL review, the accuracy of the bot will increase over time.
I seek your kind understanding for any teething issues.

## Setup Differences from Main Branch:

- Replace `OLLAMA_MODEL` and `OLLAMA_HOST` in config with `GROQ_API_KEY` and `GROQ_MODEL`
- No `ollama pull` step required
- Add the following to your `.env` file:
  - `GROQ_API_KEY` — obtain from [console.groq.com](https://console.groq.com)
  - `GITHUB_TOKEN` — GitHub Personal Access Token with `Contents: Read and Write` permission
  - `GITHUB_REPO` — your forked repository (e.g. `yourusername/susmessagebot`)
  - `GITHUB_BRANCH` — branch to sync examples to (e.g. `groq-approach`)

## Model Used:

`llama-3.1-8b-instant` — chosen for its best balance of rate limits (14,400 requests/day) and classification capability on Groq's free tier.

## Sponsorship

Running this bot at scale requires paid infrastructure. If this project has been useful to you and you'd like to help cover hosting costs or support further development, consider sponsoring:

- ⭐ Star the repo to show support
- ❤️ [GitHub Sponsors](https://github.com/sponsors/0mgABear)
- 💬 Reach out via Telegram: @commonertech
- 📧 Contact: hello@commonertech.dev
- ☕ [Ko-fi](https://ko-fi.com/commonertech)

Every contribution helps keep the bot running and the project maintained. Thank you! 🙏
