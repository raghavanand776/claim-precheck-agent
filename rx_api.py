from fastapi import FastAPI
from pydantic import BaseModel

from rx_adjudicator import adjudicate

app = FastAPI(title="Rx Adjudication API")


class Claim(BaseModel):
    claim_id: str
    member_id: str
    drug: str
    fill_date: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/adjudicate")
def adjudicate_claim(claim: Claim):
    return adjudicate(claim.model_dump())