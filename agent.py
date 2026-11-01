import json
import sys

import anthropic
from dotenv import load_dotenv

from tools import read_claim, validate_codes, lookup_payer_rules, check_eligibility

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

# 1. The menu: what each tool is called, what it does, what it needs
TOOLS = [
    {
        "name": "read_claim",
        "description": "Read one claim. Returns its codes, minutes, payer, member ID and modifiers.",
        "input_schema": {"type": "object", "properties": {"claim_id": {"type": "string"}}, "required": ["claim_id"]},
    },
    {
        "name": "validate_codes",
        "description": "Check the claim's procedure code fits the session length and a diagnosis code is present. Returns a list of problems; empty means fine.",
        "input_schema": {"type": "object", "properties": {"claim_id": {"type": "string"}}, "required": ["claim_id"]},
    },
    {
        "name": "lookup_payer_rules",
        "description": "Get an insurance company's billing rules, such as the modifier required on video (telehealth) sessions.",
        "input_schema": {"type": "object", "properties": {"payer": {"type": "string"}}, "required": ["payer"]},
    },
    {
        "name": "check_eligibility",
        "description": "Check whether a member's insurance coverage is active.",
        "input_schema": {"type": "object", "properties": {"member_id": {"type": "string"}}, "required": ["member_id"]},
    },
]

# 2. The job description
SYSTEM = """You pre-check therapy insurance claims before a human submits them.
Use the tools to check the codes, the payer's rules and the member's coverage. Never guess a fact you can look up.
Always read the session_note. If it contradicts the claim's fields (for example, a different session length, or a video visit marked as in-person), trust the note.
Every reason must say exactly what to change, including the correct code or modifier. Code ranges: 90832 = 16-37 min, 90834 = 38-52 min, 90837 = 53+ min.
Verdict rules: coverage not active = LIKELY DENIAL. Any other problem = FIX NEEDED. No problems = READY.
When done, reply with only JSON: {"verdict": "...", "reasons": ["..."]}"""


# 3. The switchboard: turns Claude's tool request into a real function call
def run_tool(name, args):
    if name == "read_claim":
        return read_claim(args["claim_id"])
    if name == "validate_codes":
        return validate_codes(read_claim(args["claim_id"]))
    if name == "lookup_payer_rules":
        return lookup_payer_rules(args["payer"])
    if name == "check_eligibility":
        return check_eligibility(args["member_id"])
    return {"error": f"unknown tool {name}"}


# 4. The agent loop: ask, run the tools Claude asks for, repeat until it answers
def precheck(claim_id):
    messages = [{"role": "user", "content": f"Pre-check claim {claim_id}."}]
    for _ in range(10):
        response = client.messages.create(
            model=MODEL, max_tokens=1024, system=SYSTEM, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            text = "".join(block.text for block in response.content if block.type == "text")
            return json.loads(text[text.find("{"): text.rfind("}") + 1])

        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"    Claude calls {block.name}({block.input})")
                output = run_tool(block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output)})
        messages.append({"role": "user", "content": results})
    raise RuntimeError("Agent took too many steps")


# 5. The answer key, for the score
EXPECTED = {
    "claim_001": "READY",
    "claim_002": "FIX NEEDED",
    "claim_003": "FIX NEEDED",
    "claim_004": "LIKELY DENIAL",
    "claim_005": "FIX NEEDED",
    "claim_006": "FIX NEEDED",
    "claim_007": "READY",
        
}
MUST_MENTION = {
    "claim_002": "90834",
    "claim_003": "95",
    "claim_005": "95",
    "claim_006": "90832",
}
if __name__ == "__main__":
    claim_ids = sys.argv[1:] or list(EXPECTED)
    correct = 0
    for claim_id in claim_ids:
        print(f"\n{claim_id}")
        result = precheck(claim_id)
        # ok = result["verdict"] == EXPECTED.get(claim_id)
        ok = result["verdict"] == EXPECTED.get(claim_id)
        needed = MUST_MENTION.get(claim_id)
        if needed and needed not in " ".join(result["reasons"]):
            ok = False
            print(f"  Reason doesn't mention {needed}")

        correct += ok
        print(f"  Verdict: {result['verdict']}  {'(correct)' if ok else '(expected ' + EXPECTED.get(claim_id, '?') + ')'}")
        for reason in result["reasons"]:
            print(f"    - {reason}")
    print(f"\nScore: {correct}/{len(claim_ids)}")