# Claim Pre-Check Agent & Rx Adjudication API

A learning project exploring where AI helps, and where it doesn't, in healthcare claims.

It has two parts:

1. **Claim pre-check agent** – reviews therapy insurance claims *before* submission and flags what would get them denied.
2. **Rx adjudication API** – a small model of how a pharmacy benefit manager approves or rejects a prescription in real time.

All data is synthetic. No real patient information is used.

---

## Part 1: Claim pre-check agent

**The problem:** a claim with a wrong procedure code, a missing telehealth modifier, or inactive coverage gets denied, and the provider waits weeks to fix and resubmit it. Many of these errors can be caught before submission.

**How it evolved:**

| Version | How it works | Result |
| --- | --- | --- |
| Rules (`check_claims.py`) | Plain Python checks: code vs. session length, diagnosis present, payer telehealth modifier, eligibility | 4/4 on clean claims, but **1/3** when the real problem was only in the free-text session note |
| Agent (`agent.py`) | Claude (Haiku) gets the same four checks as tools, decides which to call, and explains the fix | **7/7**, including problems hidden in session notes |

**Design principle:** rules for structured fields (fast, free, exact); the model for messy human text (understands meaning). The agent only advises – a human submits.

**How it's tested:**

- **Eval set** – 7 labeled claims. Each must get the right verdict *and* name the right fix (e.g. "use 90832"). I verified the eval can fail by requiring a wrong answer on purpose.
- **Unit tests** (`test_tools.py`) – 6 tests for the rules, including a boundary case. A planted one-digit bug was caught immediately.

**Lessons:**

- The first eval run scored 6/7 – the miss was a typo in my answer key, not the model. Check the test first.
- A perfect verdict score hid a quality gap: one reason was correct but not actionable. Two sentences added to the instructions made every reason say exactly what to change.

---

## Part 2: Rx adjudication API

At the pharmacy counter, a claim is decided in seconds. `rx_adjudicator.py` runs the checks in order and stops at the first failure:

| Check | Reject code if it fails |
| --- | --- |
| Patient covered? | 65 |
| Drug on the plan's formulary? | 70 |
| Prior authorization on file (if required)? | 75 |
| Too soon to refill (before 75% of last supply)? | 79 |
| Approved → patient pays the tier copay, never more than the drug's price | – |

`rx_api.py` puts it behind a **FastAPI** service:

- `POST /adjudicate` – send a claim, get approved (with amounts) or rejected (with code and reason)
- `GET /health` – for monitoring
- Malformed requests are rejected with **422** before reaching the logic

**Load test** (`load_test.py`, 1,000 sequential claims, one laptop, no network): **~1.3 ms average and p95.** Not a production number – the point is measuring p95, because the slow tail is the customer waiting at the counter. It's also why AI stays off the real-time path here.

---

### Sample request and response

```bash
curl -s -X POST localhost:8000/adjudicate \
  -H "Content-Type: application/json" \
  -d '{"claim_id":"rx_001","member_id":"M200","drug":"atorvastatin 20mg","fill_date":"2026-10-31"}'
```

```json
{"status": "APPROVED", "price": 12.0, "patient_pays": 10, "plan_pays": 2.0}
```

A rejected claim returns a standard reject code and a plain-language reason:

```json
{"status": "REJECTED", "reject_code": "79", "message": "Refill too soon: 10 days since last fill, earliest is day 23"}
```

Results for all 7 sample claims are in [`rx/sample_results.md`](rx/sample_results.md).

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 check_claims.py          # rules version
python3 -m pytest -v             # unit tests
python3 rx_adjudicator.py        # pharmacy adjudicator on sample claims

uvicorn rx_api:app --reload      # start the API, then open http://127.0.0.1:8000/docs
python3 load_test.py             # in a second terminal, while the API runs
```

The agent needs an Anthropic API key in a `.env` file:

```
ANTHROPIC_API_KEY=your-key-here
```

```bash
python3 agent.py                 # all claims, with score
python3 agent.py claim_006       # one claim
```

---

## What I'd do next

- Grow the eval set from real denial patterns, and track false flags as well as misses
- Run rules first on every claim, and send only note-bearing claims to the model, to control cost and latency
- Add a reviewer step for high-risk claims
- Add network, database and concurrency to the load test for a more realistic latency picture

Built with Python, the Claude API (tool use), FastAPI and pytest.

## License

MIT. See [LICENSE](LICENSE).
