from tools import validate_codes, check_eligibility, lookup_payer_rules


def make_claim(code, minutes, diagnosis="F41.1"):
    return {"cpt_code": code, "session_minutes": minutes, "diagnosis_code": diagnosis}


def test_correct_claim_has_no_problems():
    assert validate_codes(make_claim("90834", 45)) == []


def test_wrong_code_suggests_the_right_one():
    problems = validate_codes(make_claim("90837", 40))
    assert len(problems) == 1
    assert "90834" in problems[0]


def test_missing_diagnosis_is_flagged():
    problems = validate_codes(make_claim("90834", 45, diagnosis=""))
    assert problems == ["Missing diagnosis code"]


def test_edge_of_range():
    assert validate_codes(make_claim("90834", 38)) == []
    assert validate_codes(make_claim("90834", 37)) != []


def test_unknown_member_is_treated_as_not_covered():
    assert check_eligibility("M999") == {"active": False}


def test_bluesky_requires_modifier_95():
    assert lookup_payer_rules("BlueSky Health")["telehealth_modifier"] == "95"