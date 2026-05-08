import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FMP_API_KEY = os.environ.get("FMP_API_KEY")
SEEN_FILE = os.environ.get("SEEN_FILE_PATH", "seen_trades.json")
POLITICIAN = "Nancy Pelosi"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_trades():
    url = f"https://financialmodelingprep.com/api/v4/house-disclosure?page=0&apikey={FMP_API_KEY}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

def post_to_discord(trade):
    ticker = trade.get("ticker", "N/A")
    tx_type = trade.get("type", "N/A").upper()
    amount = trade.get("amount", "N/A")
    date = trade.get("transactionDate", "N/A")
    asset = trade.get("assetDescription", "N/A")

    color = 0x00FF00 if "purchase" in tx_type.lower() else 0xFF0000

    embed = {
        "embeds": [{
            "title": "🏛️ Nancy Pelosi Trade Alert",
            "color": color,
            "fields": [
                {"name": "Ticker", "value": ticker, "inline": True},
                {"name": "Type",   "value": tx_type, "inline": True},
                {"name": "Amount", "value": amount,  "inline": True},
                {"name": "Date",   "value": date,    "inline": True},
                {"name": "Asset",  "value": asset,   "inline": False},
            ],
            "footer": {"text": "Source: financialmodelingprep.com"},
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    requests.post(WEBHOOK_URL, json=embed)

def run():
    seen = load_seen()
    trades = fetch_trades()

    new_count = 0
    for trade in trades:
        if POLITICIAN not in trade.get("representative", ""):
            continue

        trade_id = f"{trade.get('transactionDate') or trade.get('transaction_date')}_{trade.get('ticker')}_{trade.get('amount')}"

        if trade_id not in seen:
            post_to_discord(trade)
            seen.add(trade_id)
            new_count += 1

    save_seen(seen)
    print(f"[{datetime.now()}] Checked. New trades posted: {new_count}")

if __name__ == "__main__":
    run()
