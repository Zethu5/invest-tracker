import re
import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SEEN_FILE = os.environ.get("SEEN_FILE_PATH", "seen_trades.json")
HEADERS = {"User-Agent": "Mozilla/5.0"}

POLITICIANS = [
    ("Michael McCaul",     "M001157"),
    ("Ro Khanna",          "K000389"),
    ("Jefferson Shreve",   "S001229"),
    ("Josh Gottheimer",    "G000583"),
    ("Darrell Issa",       "I000056"),
    ("Richard Blumenthal", "B001277"),
    ("Nancy Pelosi",       "P000197"),
    ("Dave McCormick",     "M001243"),
    ("Rick Scott",         "S001217"),
    ("David Trone",        "T000483"),
]

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_trades(politician_id):
    url = f"https://www.capitoltrades.com/trades?politician={politician_id}&pageSize=96&page=1"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("tbody > tr")

    trades = []
    for row in rows:
        cells = [c.text.strip() for c in row.find_all("td")]
        if len(cells) < 8:
            continue
        ticker_match = re.search(r'([A-Z.]+):US', cells[1])
        ticker = ticker_match.group(1) if ticker_match else "N/A"
        trades.append({
            "ticker": ticker,
            "asset": cells[1],
            "transactionDate": cells[3],
            "type": cells[6],
            "amount": cells[7],
        })

    return trades

def post_to_discord(name, trade):
    tx_type = trade["type"].upper()
    color = 0x00FF00 if trade["type"] == "buy" else 0xFF0000

    embed = {
        "embeds": [{
            "title": f"🏛️ {name} Trade Alert",
            "color": color,
            "fields": [
                {"name": "Ticker", "value": trade["ticker"],          "inline": True},
                {"name": "Type",   "value": tx_type,                  "inline": True},
                {"name": "Amount", "value": trade["amount"],          "inline": True},
                {"name": "Date",   "value": trade["transactionDate"], "inline": True},
                {"name": "Asset",  "value": trade["asset"],           "inline": False},
            ],
            "footer": {"text": "Source: capitoltrades.com"},
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    requests.post(WEBHOOK_URL, json=embed)

def run():
    seen = load_seen()
    new_count = 0

    for name, pid in POLITICIANS:
        try:
            trades = fetch_trades(pid)
            for trade in trades:
                trade_id = f"{pid}_{trade['transactionDate']}_{trade['ticker']}_{trade['amount']}"
                if trade_id not in seen:
                    post_to_discord(name, trade)
                    seen.add(trade_id)
                    new_count += 1
        except Exception as e:
            print(f"[{name}] Error: {e}")

    save_seen(seen)
    print(f"[{datetime.now()}] Checked. New trades posted: {new_count}")

if __name__ == "__main__":
    run()
