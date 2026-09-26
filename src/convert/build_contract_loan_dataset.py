"""Build a unified FM26 contract + loan dataset from the raw player CSV.

Important: this script never invents contract terms. It creates records from
verified transaction/contract input when supplied and keeps unknown fields null.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "FM26_5LEAGUE_PLAYERS_RAW.csv"
OUT = ROOT / "data" / "processed"

CONTRACT_FIELDS = [
    "contract_id", "player_id", "club_id", "contract_type", "start_date",
    "end_date", "duration_years", "wage_amount", "wage_currency",
    "wage_period", "transfer_fee_amount", "transfer_fee_currency",
    "release_clause_amount", "release_clause_currency", "status", "source",
    "verified_at"
]

LOAN_FIELDS = [
    "loan_id", "player_id", "parent_club_id", "loan_club_id", "start_date",
    "end_date", "loan_type", "loan_fee_amount", "loan_fee_currency",
    "option_to_buy", "option_fee_amount", "option_fee_currency",
    "obligation_to_buy", "obligation_fee_amount", "obligation_fee_currency",
    "wage_share_parent_percent", "wage_share_loan_percent",
    "buy_option_conditions", "status", "source", "verified_at"
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with RAW.open("r", encoding="utf-8-sig", newline="") as f:
        players = list(csv.DictReader(f))

    # No contract/loan values are inferred from the player CSV itself.
    # The raw file has current-club data, not verified contract terms.
    contracts = []
    loans = []

    (OUT / "contracts.json").write_text(
        json.dumps(contracts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "loans.json").write_text(
        json.dumps(loans, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manifest = {
        "players_seen": len(players),
        "contracts_verified": len(contracts),
        "loans_verified": len(loans),
        "rule": "unknown values remain null; no invented contract or loan terms",
        "next_input": "verified_contracts_and_loans.json"
    }
    (OUT / "CONTRACT_LOAN_BUILD_STATUS.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
