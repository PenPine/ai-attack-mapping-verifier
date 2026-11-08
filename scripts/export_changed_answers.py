"""
scripts/export_changed_answers.py
Read-only on the results (2026-11-08), no API calls. Writes results/stage3_v3/changed_answers.csv: the 17 Stage 3
answers whose correctness changed (misleading: 11 regressions; genuine: 4 regressions and 2 corrections), with
the baseline and new answers, the full reasoning, pair facts, and three hand-coded columns.

Hand-coded columns (HAND_CODES). acknowledges_original and describes_evidence_as_classified_event were coded by
hand by the author after reading the reasoning (2026-11-08). other_environment comes from the 2026-11-01 listing
of the misleading regressions (domain and user names on both sides compared; NT AUTHORITY, SYSTEM, machine
accounts and masked values ignored; "unknown" when a side names none), adopted by the author. The genuine rows
are "n/a" in all three.

Run from the project root:  python scripts/export_changed_answers.py
"""
import csv
import json
import sys

sys.path.insert(0, ".")
import run_stage3 as S

OUT = "results/stage3_v3/changed_answers.csv"
RESULTS = "results/stage3_v3/stage3_results.jsonl"
HAND_CODE_COLUMNS = ["acknowledges_original", "describes_evidence_as_classified_event", "other_environment"]
# (acknowledges_original, describes_evidence_as_classified_event, other_environment) for the misleading regressions
HAND_CODES = {
    "15a2624605c9e3d3": ("no", "no", "yes"),
    "691ea664af0c6825": ("no", "no", "yes"),
    "ac42058f1cdd3ac1": ("yes", "no", "unknown"),
    "0793212750e00b04": ("yes", "no", "unknown"),
    "b7d819458bfa1246": ("yes", "yes", "unknown"),
    "30f8bc022db8378b": ("yes", "no", "no"),
    "ae4b62e1857e1a39": ("yes", "no", "yes"),
    "6b4c661df59e892b": ("yes", "no", "no"),
    "243e55d798340ba4": ("yes", "no", "no"),
    "235415a4e63aed89": ("yes", "no", "unknown"),
    "57ef63e46ffa0e1f": ("yes", "no", "unknown"),
}

evals = {e["event_uid"]: e for e in S.load(S.EVAL)}
pairs = {r["pair_id"]: r for r in S.load(S.PAIRS)}
with open(S.SENSITIVITY, encoding="utf-8") as f:
    sens = {c["cluster_id"] for c in json.load(f)["clusters"]}

rows = []
for r in S.load(RESULTS):
    if r["condition"] == "neutral":
        continue
    e = evals[r["event_uid"]]
    p = S.parse_lenient(r["raw"])
    now = p.get("predicted_technique") == e["technique_label"]
    if bool(e["baseline_correct"]) == now:
        continue
    pr = pairs[r["pair_id"]]
    outcome = "regression" if e["baseline_correct"] else "correction"
    if r["condition"] == "misleading":
        codes = HAND_CODES[r["event_uid"]]
    else:
        codes = ("n/a",) * 3
    rows.append({
        "condition": r["condition"], "outcome": outcome, "pair_id": r["pair_id"], "event_uid": r["event_uid"],
        "cluster_id": e["cluster_id"], "technique_label": e["technique_label"],
        "decoy_technique": e["decoy_technique"] or "",
        "baseline_prediction": e["baseline"]["predicted_technique"], "baseline_confidence": e["baseline"]["confidence"],
        "baseline_reasoning": e["baseline"]["reasoning"],
        "new_prediction": p.get("predicted_technique", "NOT JSON"), "new_confidence": p.get("confidence"),
        "new_reasoning": p.get("reasoning", r["raw"]),
        "new_equals_decoy": "n/a" if r["condition"] == "genuine" else ("yes" if p.get("predicted_technique") == e["decoy_technique"] else "no"),
        "t1059_001": "yes" if e["technique_label"] == "T1059.001" else "no",
        "sensitivity_cluster": "yes" if e["cluster_id"] in sens else "no",
        "same_channel": "yes" if pr.get("same_channel") else "no",
        "link_type": pr.get("link_type") or "",
        "original_event_id": pr.get("original_event_id"), "evidence_event_id": pr.get("evidence_event_id"),
        "strict_parse_valid": "yes" if "predicted_technique" in S.parse_strict(r["raw"]) else "no",
        "stop_reason": r["stop_reason"], "request_id": r["request_id"], "prompt_sha1": r["prompt_sha1"],
        **dict(zip(HAND_CODE_COLUMNS, codes)),
    })

order = {("misleading", "regression"): 0, ("genuine", "regression"): 1, ("genuine", "correction"): 2}
rows.sort(key=lambda x: (order[(x["condition"], x["outcome"])], x["technique_label"], x["event_uid"]))
assert len(rows) == 17 and set(HAND_CODES) == {x["event_uid"] for x in rows if x["condition"] == "misleading"}
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:      # BOM so that Excel reads UTF-8
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"{OUT}: {len(rows)} rows")
for x in rows:
    print(f"  {x['condition']:<11}{x['outcome']:<11}{x['event_uid']}  {x['technique_label']:<10}-> {x['new_prediction']:<10}"
          f"  {x['acknowledges_original']:<4}{x['describes_evidence_as_classified_event']:<4}{x['other_environment']}")
