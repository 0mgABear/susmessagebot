.PHONY: dev start

dev:
	USE_POLLING=true uv run python bot.py

start:
	uv run python bot.py
