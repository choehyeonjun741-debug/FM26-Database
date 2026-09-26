import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "FM26_5LEAGUE_PLAYERS_RAW.csv"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

players = []
with RAW.open("r", encoding="utf-8-sig", newline="") as f:
    for i, row in enumerate(csv.DictReader(f), 1):
        club = row.get("club_canonical") or row.get("club")
        players.append({
            "player_id": f"P{i:06d}",
            "name": row.get("name"),
            "position": row.get("position"),
            "age": int(row["age"]) if row.get("age") else None,
            "ca": int(row["ca"]) if row.get("ca") else None,
            "pa": int(row["pa"]) if row.get("pa") else None,
            "nationality": row.get("nationality"),
            "league": row.get("league"),
            "current_club": club,
            "contract": {
                "status": "unverified",
                "contract_club": club,
                "start_date": None,
                "end_date": None,
                "wage_weekly": None,
                "currency": "GBP"
            },
            "loan": {
                "status": "unverified",
                "parent_club": None,
                "loan_club": None,
                "start_date": None,
                "end_date": None,
                "option_to_buy": None,
                "option_fee": None,
                "obligation_to_buy": None,
                "obligation_fee": None
            }
        })

with (OUT / "players.json").open("w", encoding="utf-8") as f:
    json.dump(players, f, ensure_ascii=False, indent=2)

for filename in ("contracts.json", "loans.json", "transfers.json"):
    with (OUT / filename).open("w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

print(f"Processed {len(players)} players")
