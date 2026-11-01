import json
from pathlib import Path

DATA = Path(__file__).parent / "data"

# Which minutes each therapy code covers: (lowest, highest)
CPT_MINUTES = {
    "90832": (16, 37),
    "90834": (38, 52),
    "90837": (53, 999),
}


def read_claim(claim_id):
    with open(DATA / "claims" / f"{claim_id}.json") as f:
        return json.load(f)


def validate_codes(claim):
    problems = []
    code = claim["cpt_code"]
    minutes = claim["session_minutes"]

    if code not in CPT_MINUTES:
        problems.append(f"Unknown code {code}")
    else:
        low, high = CPT_MINUTES[code]
        if not (low <= minutes <= high):
            right = [c for c, (lo, hi) in CPT_MINUTES.items() if lo <= minutes <= hi]
            tip = f"; use {right[0]}" if right else ""
            problems.append(f"Code {code} doesn't fit a {minutes}-minute session{tip}")

    if not claim.get("diagnosis_code"):
        problems.append("Missing diagnosis code")

    return problems


def lookup_payer_rules(payer):
    with open(DATA / "payer_rules.json") as f:
        return json.load(f).get(payer, {})


def check_eligibility(member_id):
    with open(DATA / "eligibility.json") as f:
        return json.load(f).get(member_id, {"active": False})