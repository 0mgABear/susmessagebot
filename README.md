# Branch: groq-approach

Contingency Plan in the event that there is insufficient capacity on Oracle to provision a VPS.

# Technical Implementation:

1. bot.py will scan any incoming text message (Version 1).
2. Incoming text is sent to moderator.py, where it's first converted into embedding (defined in vector_store.py).
3. Input text embedding is then compared with current existing labelled examples to retrieve most similar examples. (Retrieval-Augmented Generation)
4. Examples and system prompt are in tandem fed to Groq, which will return a singular classification: BAN or SAFE.
5. BAN or SAFE will be passed on to bot.py

# Tech Stack:

1. Groq Model/LLM: llama-3.1-8b-instant
2. ChromaDB (vector storage)
3. Google free VPS - e2 micro instance
4. Webhooks (via python-telegram-bot built-in)

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

## Setup Differences from Main Branch:

- Replace `OLLAMA_MODEL` and `OLLAMA_HOST` in config with `GROQ_API_KEY` and `GROQ_MODEL`
- No `ollama pull` step required
- Add `GROQ_API_KEY` to your `.env` file (obtain from console.groq.com)

## Model Used:

`llama-3.1-8b-instant` — chosen for its best balance of rate limits (14,400 requests/day) and classification capability on Groq's free tier.
