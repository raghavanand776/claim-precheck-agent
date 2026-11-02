# Rx adjudicator: sample results

Output of `POST /adjudicate` for each claim in `sample_claims.json` (synthetic data).

| Claim | Result | Reject code | Detail |
| --- | --- | --- | --- |
| rx_001 | APPROVED | | Price $12.00, patient pays $10.00, plan pays $2.00 |
| rx_002 | REJECTED | 79 | Refill too soon: 10 days since last fill, earliest is day 23 |
| rx_003 | REJECTED | 75 | Prior authorization required |
| rx_004 | APPROVED | | Price $950.00, patient pays $90.00, plan pays $860.00 |
| rx_005 | REJECTED | 65 | Patient is not covered |
| rx_006 | REJECTED | 70 | Drug is not covered by this plan |
| rx_007 | APPROVED | | Price $8.00, patient pays $8.00, plan pays $0.00 |
