from pathlib import Path
from tools import read_claim, validate_codes, lookup_payer_rules, check_eligibility


def precheck(claim_id):
    claim = read_claim(claim_id)
    problems = validate_codes(claim)

    rules = lookup_payer_rules(claim["payer"])
    tag = rules.get("telehealth_modifier")
    if claim["telehealth"] and tag and tag not in claim["modifiers"]:
        problems.append(f"Video session needs modifier {tag}")

    member = check_eligibility(claim["member_id"])
    if not member["active"]:
        return "LIKELY DENIAL", ["Patient's coverage is not active"] + problems

    if problems:
        return "FIX NEEDED", problems
    return "READY", []


if __name__ == "__main__":
    folder = Path(__file__).parent / "data" / "claims"
    for path in sorted(folder.glob("*.json")):
        verdict, reasons = precheck(path.stem)
        print(f"{path.stem}: {verdict}")
        for reason in reasons:
            print(f"    - {reason}")