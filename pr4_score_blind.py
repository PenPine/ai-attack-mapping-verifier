"""
pr4_score_blind.py
Compare one labeler's blind answers with the rule labels and with the model. No API calls.

Usage (from the project root):
    python pr4_score_blind.py results/blind_answers_v1.csv

Inputs
    results/blind_key.csv         item_id, event_uid, cluster_id, rule_label, model_prediction   (private)
    the answers file              item_id, answer, confidence   (answer = a technique ID or NONE)
Nothing is corrected silently: an answer that is not one of the 10 IDs or NONE is reported and counted as no match.
"""
import csv
import sys
from collections import Counter, defaultdict

VALID = {"T1003.001", "T1003.006", "T1021.002", "T1053.005", "T1055",
         "T1059.001", "T1059.003", "T1546.003", "T1547.001", "T1562.002", "NONE"}


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def norm(a):
    a = (a or "").strip().upper()
    return "NONE" if a in ("NONE", "NO", "N/A") else a


path = sys.argv[1] if len(sys.argv) > 1 else "results/blind_answers_v1.csv"
key = {r["item_id"]: r for r in read("results/blind_key.csv")}
ans = {r["item_id"]: r for r in read(path)}
items = [i for i in sorted(key) if i in ans and (ans[i]["answer"] or "").strip()]
print(f"items in the key: {len(key)}   items answered: {len(items)}\n")

rows = []
for i in items:
    lab, rule, model = norm(ans[i]["answer"]), key[i]["rule_label"], norm(key[i]["model_prediction"])
    try:
        conf = int(ans[i]["confidence"])
    except (TypeError, ValueError):
        conf = None
    if lab not in VALID:
        print(f"NOTE: {i} answer '{ans[i]['answer']}' is not one of the 10 IDs or NONE; counted as no match.")
    rows.append((i, rule, lab, model, conf))
n = len(rows)
if not n:
    sys.exit("no answered items found")

lab_ok = [r[2] == r[1] for r in rows]
mod_ok = [r[3] == r[1] for r in rows]
agree_lm = [r[2] == r[3] for r in rows]


def pct(k):
    return f"{k}/{n} ({k / n * 100:.0f}%)"


print(f"labeler = rule label:       {pct(sum(lab_ok))}")
print(f"model   = rule label:       {pct(sum(mod_ok))}   (same {n} items)")
print(f"labeler = model:            {pct(sum(agree_lm))}")
both = sum(a and b for a, b in zip(lab_ok, mod_ok))
only_l = sum(a and not b for a, b in zip(lab_ok, mod_ok))
only_m = sum(b and not a for a, b in zip(lab_ok, mod_ok))
neither = n - both - only_l - only_m
print(f"matching the rule label: both {both}, only labeler {only_l}, only model {only_m}, neither {neither}")


def kappa(x, y):
    po = sum(a == b for a, b in zip(x, y)) / len(x)
    cx, cy = Counter(x), Counter(y)
    pe = sum(cx[c] * cy[c] for c in set(cx) | set(cy)) / len(x) ** 2
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


print(f"Cohen's kappa, labeler vs rule label: {kappa([r[2] for r in rows], [r[1] for r in rows]):.2f}   "
      f"(descriptive only: {n} items and 11 categories)")

print("\nagreement with the rule label by the labeler's confidence")
for name, lo, hi in (("low (1-2)", 1, 2), ("middle (3)", 3, 3), ("high (4-5)", 4, 5)):
    sel = [r for r in rows if r[4] is not None and lo <= r[4] <= hi]
    if sel:
        print(f"  {name:<11} {sum(r[2] == r[1] for r in sel)}/{len(sel)}")

by = defaultdict(lambda: [0, 0, 0])
for _, rule, lab, model, _ in rows:
    by[rule][0] += 1
    by[rule][1] += lab == rule
    by[rule][2] += model == rule
print(f"\n{'rule label':<12}{'items':>6}{'labeler ok':>12}{'model ok':>10}")
for t in sorted(by):
    print(f"{t:<12}{by[t][0]:>6}{by[t][1]:>12}{by[t][2]:>10}")

print(f"\nitems where the labeler differs from the rule label")
print(f"{'item':<6}{'rule label':<12}{'labeler':<12}{'conf':>5}  {'model':<12}")
for i, rule, lab, model, conf in rows:
    if lab != rule:
        print(f"{i:<6}{rule:<12}{lab:<12}{conf if conf is not None else '':>5}  {model:<12}")
print("\nA disagreement is not automatically a labeler error: read each one against the event. "
      "Where the labeler is plausibly right, the rule label is the problem.")