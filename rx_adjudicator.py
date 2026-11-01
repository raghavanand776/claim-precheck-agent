import json
import math
from datetime import date
from pathlib import Path

RX = Path(__file__).parent / "rx"
REFILL_PERCENT = 0.75


def load(name):
    with open(RX / name) as f:
        return json.load(f)


def reject(code, message):
    return {"status": "REJECTED", "reject_code": code, "message": message}


def adjudicate(claim):
    members = load("members.json")
    formulary = load("formulary.json")
    history = load("fill_history.json")

    # 1. Is the patient covered?
    member = members.get(claim["member_id"])
    if not member or not member["active"]:
        return reject("65", "Patient is not covered")

    # 2. Is the drug on the plan's list?
    drug = formulary.get(claim["drug"])
    if not drug:
        return reject("70", "Drug is not covered by this plan")

    # 3. Does it need prior authorization?
    if drug["prior_auth"] and claim["drug"] not in member["prior_auths"]:
        return reject("75", "Prior authorization required")

    # 4. Is it too soon to refill?
    last = history.get(claim["member_id"], {}).get(claim["drug"])
    if last:
        days_since = (date.fromisoformat(claim["fill_date"]) - date.fromisoformat(last["last_fill"])).days
        earliest = math.ceil(last["days_supply"] * REFILL_PERCENT)
        if days_since < earliest:
            return reject("79", f"Refill too soon: {days_since} days since last fill, earliest is day {earliest}")

    # 5. Approved: work out who pays what
    copay = member["copays"][str(drug["tier"])]
    patient_pays = min(copay, drug["price"])
    return {
        "status": "APPROVED",
        "price": drug["price"],
        "patient_pays": patient_pays,
        "plan_pays": round(drug["price"] - patient_pays, 2),
    }


if __name__ == "__main__":
    for claim in load("sample_claims.json"):
        result = adjudicate(claim)
        print(f"{claim['claim_id']}: {claim['member_id']} {claim['drug']}")
        if result["status"] == "APPROVED":
            print(f"    APPROVED  patient pays ${result['patient_pays']:.2f}, plan pays ${result['plan_pays']:.2f}")
        else:
            print(f"    REJECTED {result['reject_code']}  {result['message']}")