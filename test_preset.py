"""Self-checks for preset_*.json: quota integrity + exact distribution.

Run: .venv/bin/python test_preset.py [preset.json ...]
No network: builds a throwaway question schema from the pools themselves.
"""
import glob
import json
import sys
from collections import Counter

from core import FormDetails, SubmissionEngine


def check(path: str) -> None:
    preset = json.load(open(path, encoding="utf-8"))
    cfg, count = preset["config"], preset["count"]
    pools = {k[:-6]: v for k, v in cfg.items() if k.endswith("__pool")}
    assert pools, f"{path}: no pools"

    for qid, pool in pools.items():
        total = sum(e["quota"] or 0 for e in pool)
        assert total == count, f"{path}/{qid}: quotas sum {total} != {count}"
        values = [e["value"] for e in pool]
        assert len(values) == len(set(values)), f"{path}/{qid}: duplicate values"

    details = FormDetails(
        url="x",
        form_action_url="x",
        questions={qid: {"text": qid, "type": "Multiple Choice",
                         "options": [e["value"] for e in pool], "required": True}
                   for qid, pool in pools.items()},
        hidden_fields={},
    )
    engine = SubmissionEngine(details)
    seen = {qid: Counter() for qid in pools}
    for _ in range(count):
        response, _release = engine.generate_response(custom_config=cfg)
        for qid, answer in response.items():
            seen[qid][answer] += 1
    for qid, pool in pools.items():
        want = {e["value"]: e["quota"] for e in pool}
        assert dict(seen[qid]) == want, f"{path}/{qid}: {dict(seen[qid])} != {want}"

    if path.endswith("preset_44.json"):
        check_survey_constraints(pools, seen, count)
    if path.endswith("preset_nutrisi11.json"):
        check_nutrisi11_constraints(pools, seen, count)
    print(f"ok: {path} - {len(pools)} pools, {count} responses, exact quotas")

def check_nutrisi11_constraints(pools, seen, count) -> None:
    """Requirements for the 11-respondent digital nutrition literacy survey."""
    age = seen["entry.54350776"]
    assert set(age) <= {"18", "19", "20", "21", "22"}, age
    assert (age["18"] + age["19"] + age["20"] + age["21"]) / count >= 0.85, age

    gender = seen["entry.432669878"]
    assert gender["Laki-Laki"] == 7 and gender["Perempuan"] == 4, gender

    sport = seen["entry.1618293407"]
    assert (sport["Bulu tangkis"] + sport["Bola voli"]) / count >= 0.6, sport
    assert len([k for k in sport if sport[k]]) >= 4, sport

    prodi = seen["entry.849067895"]
    sport_prodi = sum(v for k, v in prodi.items() if any(t in k for t in ("IKOR", "PJKR", "PKO")))
    assert sport_prodi / count >= 0.6, prodi
    assert len([k for k in prodi if prodi[k]]) >= 4, prodi

    kelas = seen["entry.1811204181"]
    assert set(kelas) == {"2026", "2025", "2024"}, kelas

    active = seen["entry.2019424921"]
    assert active["Tidak"] == 1 and active["Ya"] == count - 1, active

    positive = likert = 0
    for qid in seen:
        opts = {e["value"] for e in pools[qid]}
        if {"Sangat Setuju", "Setuju"} <= opts or {"Sangat Penting", "Penting"} <= opts:
            positive += sum(seen[qid][k] for k in ("Sangat Setuju", "Setuju", "Sangat Penting", "Penting"))
            likert += 1
    assert likert >= 20, likert
    assert positive / (likert * count) >= 0.75, positive / (likert * count)


def check_survey_constraints(pools, seen, count) -> None:
    """Requirements for the 44-respondent athlete nutrition survey preset."""
    age = seen["entry.1956238427"]
    assert set(age) <= {"18", "19", "20", "21"}, age
    assert sum(age.values()) == count

    gender = seen["entry.2012857553"]
    assert abs(gender["Laki-Laki"] / gender["Perempuan"] - 7 / 4) < 0.05, gender

    sport = seen["entry.630832652"]
    assert (sport["Bulu tangkis"] + sport["Bola voli"]) / count >= 0.5, sport

    prodi = seen["entry.739856841"]
    sport_prodi = sum(prodi[k] for k in prodi if any(t in k for t in ("IKOR", "PJKR", "PKO")))
    assert sport_prodi / count >= 0.6, prodi
    assert len([k for k in prodi if prodi[k]]) >= 4

    kelas = seen["entry.1211038438"]
    assert set(kelas) == {"2026", "2025", "2024"}, kelas
    assert max(kelas.values()) / count <= 0.45, kelas

    active = seen["entry.452683383"]
    assert active["Tidak"] == 5 and active["Ya"] == count - 5, active

    positive = 0
    likert = 0
    for qid in seen:
        opts = {e["value"] for e in pools[qid]}
        if {"Sangat Setuju", "Setuju"} <= opts:
            positive += seen[qid]["Sangat Setuju"] + seen[qid]["Setuju"]
            likert += 1
        elif {"Sangat Penting", "Penting"} <= opts:
            positive += seen[qid]["Sangat Penting"] + seen[qid]["Penting"]
            likert += 1
    assert positive / (likert * count) >= 0.8, positive / (likert * count)


paths = sys.argv[1:] or sorted(glob.glob("preset_*.json"))
assert paths, "no preset files found"
for path in paths:
    check(path)
