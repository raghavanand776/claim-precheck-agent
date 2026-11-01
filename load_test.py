import json
import time
import urllib.request

URL = "http://127.0.0.1:8000/adjudicate"
CLAIMS = json.load(open("rx/sample_claims.json"))
TOTAL = 1000


def send(claim):
    body = json.dumps(claim).encode()
    request = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        return json.load(response)


timings = []
for i in range(TOTAL):
    claim = CLAIMS[i % len(CLAIMS)]
    start = time.perf_counter()
    send(claim)
    timings.append((time.perf_counter() - start) * 1000)

timings.sort()
print(f"Sent {TOTAL} claims")
print(f"Average: {sum(timings) / TOTAL:.1f} ms")
print(f"Fastest: {timings[0]:.1f} ms")
print(f"p95:     {timings[int(TOTAL * 0.95)]:.1f} ms  (95% of claims were faster than this)")
print(f"Slowest: {timings[-1]:.1f} ms")