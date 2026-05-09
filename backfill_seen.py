import re
import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

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
            "transactionDate": cells[3],
            "amount": cells[7],
        })
    return trades

seen = set()

for name, pid in POLITICIANS:
    try:
        trades = fetch_trades(pid)
        for trade in trades:
            trade_id = f"{pid}_{trade['transactionDate']}_{trade['ticker']}_{trade['amount']}"
            seen.add(trade_id)
        print(f"[{name}] Marked {len(trades)} trades as seen.")
    except Exception as e:
        print(f"[{name}] Error: {e}")

save_seen(seen)
print(f"Done. seen_trades.json rebuilt with {len(seen)} entries.")
