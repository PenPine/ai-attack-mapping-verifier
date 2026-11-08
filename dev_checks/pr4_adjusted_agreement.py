"""
pr4_adjusted_agreement.py
Agreement with the rule label when the T1059.001 events judged 'defensible_alternative' (or 'both') in
results/t1059_review.csv are counted as acceptable. No API calls; the pool and the baseline are not changed.

Three views:
  1. current                        agreement with the rule label, as reported so far
  2. defensible counted             the same, with the reviewed defensible alternatives counted as agreement
  3. defensible + no dsregcmd       as 2, also without the 3 T1059.003 events whose parent is not cmd.exe
Views 2 and 3 are sensitivity analyses on one reviewer's judgments; the main numbers stay those of view 1.
"""
import csv
import json
import re
from collections import defaultdict

ACCEPT = {"defensible_alternative", "both"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def basename(v):
    return re.split(r"[\\/]", str(v or ""))[-1].lower()


pool = load("results/pool_clean.jsonl")
pred = {b["event_uid"]: b["prediction"] for b in load("results/baseline_clean.jsonl")}
with open("results/t1059_review.csv", newline="", encoding="utf-8-sig") as f:
    review = list(csv.DictReader(f))
counts = defaultdict(int)
for r in review:
    counts[(r["judgment"] or "(blank)").strip()] += 1
print("judgments in t1059_review.csv:", dict(counts))
if counts.get("(blank)"):
    print(f"WARNING: {counts['(blank)']} events have no judgment yet; they are treated as not acceptable.")
accepted = {r["event_uid"] for r in review if (r["judgment"] or "").strip() in ACCEPT}
drop = {p["event_uid"] for p in pool if p["technique_label"] == "T1059.003" and basename(p["event"].get("ParentImage")) != "cmd.exe"}


def view(accept, skip):
    ev_ok = ev_n = 0
    t1_ok = t1_n = 0
    cl = defaultdict(list)
    for p in pool:
        uid = p["event_uid"]
        if uid in skip:
            continue
        pr = pred.get(uid, {})
        if "predicted_technique" not in pr:
            continue
        ok = int(pr["predicted_technique"] == p["technique_label"] or uid in accept)
        ev_ok, ev_n = ev_ok + ok, ev_n + 1
        if p["technique_label"] == "T1059.001":
            t1_ok, t1_n = t1_ok + ok, t1_n + 1
        cl[(p["cluster_id"], p["technique_label"])].append(ok)
    shares = [(t, sum(v) / len(v)) for (_, t), v in cl.items()]
    ex = [s for t, s in shares if t != "T1059.001"]
    t1 = [s for t, s in shares if t == "T1059.001"]
    return dict(ev=(ev_ok, ev_n), cl=(sum(s for _, s in shares) / len(shares), len(shares)),
                ex=(sum(ex) / len(ex), len(ex)), t1e=(t1_ok, t1_n), t1c=(sum(t1) / len(t1), len(t1)))


print(f"\n{'':<38}{'events':>8}{'event %':>9}{'clusters':>10}{'cluster %':>11}{'excl 1059.001':>15}"
      f"{'T1059.001 event':>17}{'T1059.001 cluster':>19}")
for name, acc, skip in (("1. current", set(), set()),
                        ("2. defensible counted", accepted, set()),
                        ("3. defensible + no dsregcmd", accepted, drop)):
    v = view(acc, skip)
    print(f"{name:<38}{v['ev'][1]:>8}{v['ev'][0] / v['ev'][1] * 100:>8.1f}%{v['cl'][1]:>10}{v['cl'][0] * 100:>10.1f}%"
          f"{v['ex'][0] * 100:>10.1f}% ({v['ex'][1]}){v['t1e'][0] / v['t1e'][1] * 100:>9.1f}% ({v['t1e'][0]}/{v['t1e'][1]})"
          f"{v['t1c'][0] * 100:>11.1f}% ({v['t1c'][1]})")
print("\nOne reviewer, AI-assisted reading: descriptive only. The main numbers remain those in row 1.")