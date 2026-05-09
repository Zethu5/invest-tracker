# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-file Python bot that scrapes congressional stock trades from [capitoltrades.com](https://capitoltrades.com), deduplicates them, and posts new trades to a Discord channel via webhook. Runs hourly on Railway.app.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires .env with DISCORD_WEBHOOK_URL)
python main.py
```

No test suite or linter is configured.

## Architecture

All logic lives in `main.py` (~105 lines). The flow is:

1. **`run()`** — top-level orchestrator; iterates over `POLITICIANS` list
2. **`fetch_trades(politician_id)`** — GETs `capitoltrades.com/politician/{id}` and parses HTML with BeautifulSoup; returns list of `{ticker, date, type, amount}` dicts
3. **`post_to_discord(name, trade)`** — POSTs a styled embed to the Discord webhook (green for buys, red for sells)
4. **`load_seen()` / `save_seen()`** — read/write `seen_trades.json` to deduplicate across runs; trade IDs are `"{politician_id}_{date}_{ticker}_{amount}"`

## Configuration

Environment variables (`.env`, excluded from git):
- `DISCORD_WEBHOOK_URL` — required; Discord bot webhook URL
- `SEEN_FILE_PATH` — optional; override path to `seen_trades.json` (defaults to `seen_trades.json`)
- `FMP_API_KEY`, `FINNHUB_API_KEY` — present but unused (legacy from prior implementations)

## Deployment

Railway.app (`railway.toml`):
- Build: Nixpacks (auto-detects Python)
- Start: `python main.py`
- Schedule: `0 * * * *` (top of every hour)

## State

`seen_trades.json` persists the set of already-posted trade IDs between runs. It is gitignored and lives alongside `main.py` locally; on Railway it persists on the deployment volume.

## Politician List

`POLITICIANS` in `main.py` is a list of `(name, capitol_trades_id)` tuples for the 10 highest-volume congressional traders. Capitol Trades assigns numeric IDs to politicians — update this list by finding the ID in the URL on their profile page.
