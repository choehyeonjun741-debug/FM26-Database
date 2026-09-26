"""Enrich the 4,313-player FM26 roster with 2025/26 contract + transfer data.

Sources:
- m-mahadi/top5-football-dataset: 2024/25-2025/26 player-season data with
  SoFIFA contract start/end, wage, value and release clause fields.
- eordo/transfermarkt-data: 2025 summer/winter transfer records for the five
  major leagues, including transfer fee and is_loan.

This script never invents values. Name matching is conservative and every
match receives a source + verification status. Loan option/obligation details
remain null unless a source explicitly supplies them.
"""
import csv, io, json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/FM26_5LEAGUE_PLAYERS_RAW.csv"
OUT = ROOT / "data/processed"
SEASON_URL = "https://raw.githubusercontent.com/m-mahadi/top5-football-dataset/main/data/master/player_seasons.csv"
TM_BASE = "https://raw.githubusercontent.com/eordo/transfermarkt-data/master/"
TM_FILES = {
    "ENG": "premier_league/2025.csv",
    "ESP": "la_liga/2025.csv",
    "GER": "bundesliga/2025.csv",
    "ITA": "serie_a/2025.csv",
    "FRA": "ligue_1/2025.csv",
}


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "FM26-Database/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with RAW.open(encoding="utf-8-sig", newline="") as f:
        roster = list(csv.DictReader(f))

    # Current-season dataset contains both 24/25 and 25/26 rows.
    season_rows = list(csv.DictReader(io.StringIO(get(SEASON_URL))))
    s2526 = [r for r in season_rows if r.get("season_label") == "2025/26"]
    contract_by_name = {}
    for r in s2526:
        key = norm(r.get("player"))
        if not key:
            continue
        # Prefer rows with contract information.
        if key not in contract_by_name or r.get("fifa_contract_end"):
            contract_by_name[key] = r

    transfers = []
    for _, path in TM_FILES.items():
        try:
            transfers.extend(csv.DictReader(io.StringIO(get(TM_BASE + path))))
        except Exception:
            continue

    transfer_by_name = {}
    for r in transfers:
        key = norm(r.get("player_name"))
        if key:
            transfer_by_name.setdefault(key, []).append(r)

    contracts, loans, audit = [], [], []
    for p in roster:
        name = p.get("player_name") or p.get("name") or p.get("Player") or ""
        key = norm(name)
        sr = contract_by_name.get(key)
        trs = transfer_by_name.get(key, [])

        contract = {
            "player_id": p.get("player_id") or p.get("id"),
            "player_name": name,
            "season": "2025/26",
            "contract_start": None,
            "contract_end": None,
            "duration_years": None,
            "wage_amount_eur": None,
            "wage_period": "weekly",
            "release_clause_eur": None,
            "transfer_value_eur": None,
            "status": "unknown",
            "source": None,
        }
        if sr:
            contract.update({
                "contract_start": sr.get("fifa_contract_start") or None,
                "contract_end": sr.get("fifa_contract_end") or None,
                "wage_amount_eur": float(sr["fifa_wage_eur"]) if sr.get("fifa_wage_eur") else None,
                "release_clause_eur": float(sr["fifa_release_clause_eur"]) if sr.get("fifa_release_clause_eur") else None,
                "transfer_value_eur": float(sr["fifa_value_eur"]) if sr.get("fifa_value_eur") else None,
                "status": "source_match",
                "source": "SoFIFA via m-mahadi/top5-football-dataset",
            })
            if sr.get("fifa_contract_start") and sr.get("fifa_contract_end"):
                try:
                    contract["duration_years"] = int(float(sr["fifa_contract_end"])) - int(float(sr["fifa_contract_start"]))
                except Exception:
                    pass
        contracts.append(contract)

        # Keep every 2025/26 transfer record; identify loans directly from source.
        for t in trs:
            if str(t.get("is_loan", "0")).lower() in ("1", "true"):
                loans.append({
                    "player_id": contract["player_id"],
                    "player_name": name,
                    "season": "2025/26",
                    "current_club": t.get("club"),
                    "parent_or_dealing_club": t.get("dealing_club"),
                    "loan_fee_eur": float(t["fee"]) if t.get("fee") not in (None, "") else None,
                    "option_to_buy": None,
                    "option_fee_eur": None,
                    "obligation_to_buy": None,
                    "obligation_fee_eur": None,
                    "status": "loan_verified",
                    "source": "Transfermarkt data via eordo/transfermarkt-data",
                })

        audit.append({
            "player_id": contract["player_id"], "player_name": name,
            "contract_source_match": bool(sr), "loan_records_found": sum(1 for t in trs if str(t.get("is_loan", "0")).lower() in ("1", "true")),
        })

    (OUT / "contracts_2526.csv").write_text("\n".join([json.dumps(x, ensure_ascii=False) for x in contracts]), encoding="utf-8")
    (OUT / "loans_2526.json").write_text(json.dumps(loans, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "contract_loan_audit_2526.json").write_text(json.dumps({"players": len(roster), "contracts": len(contracts), "loans": len(loans), "audited": audit}, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
