import re
import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

SEEN_FILE = os.environ.get("SEEN_FILE_PATH", "seen_trades.json")
HEADERS = {"User-Agent": "Mozilla/5.0"}

NEW_POLITICIANS = [
    ("Lisa McClain",     "M001136"),
    ("Gil Cisneros",     "C001123"),
    ("Rob Bresnahan",    "B001327"),
    ("Julie Johnson",    "J000310"),
    ("Markwayne Mullin", "M001190"),
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
            "transactionDate": cells[3],
            "amount": cells[7],
        })
    return trades

seen = load_seen()

for name, pid in NEW_POLITICIANS:
    try:
        trades = fetch_trades(pid)
        for trade in trades:
            trade_id = f"{pid}_{trade['transactionDate']}_{trade['ticker']}_{trade['amount']}"
            seen.add(trade_id)
        print(f"[{name}] Marked {len(trades)} trades as seen.")
    except Exception as e:
        print(f"[{name}] Error: {e}")

save_seen(seen)
print("Done. seen_trades.json updated.")
