"""
pr4_t1059_distinct.py
Many of the 23 review events are the same script repeated in different clusters. This groups them, so you read each
distinct script once. Short scripts are printed in full. No API calls.
Reads results/t1059_review.csv and results/pool_clean.jsonl.
"""
import csv
import json
from collections import defaultdict

SHOW = 400            # scripts up to this many characters are printed in full

pool = {}
with open("results/pool_clean.jsonl", encoding="utf-8") as f:
    for l in f:
        if l.strip():
            p = json.loads(l)
            pool[p["event_uid"]] = p
with open("results/t1059_review.csv", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

groups = defaultdict(list)
for r in rows:
    text = " ".join(str(pool[r["event_uid"]]["event"].get("ScriptBlockText") or "").split())
    groups[(r["model_answer"], text)].append(r["review_id"])

print(f"{len(rows)} events, {len(groups)} distinct scripts\n")
for i, ((ans, text), ids) in enumerate(sorted(groups.items(), key=lambda kv: (kv[0][0], -len(kv[1]))), 1):
    shown = text if len(text) <= SHOW else text[:SHOW] + f" [... {len(text)} characters in total]"
    print(f"#{i}  model answered {ans}   events: {', '.join(ids)}  ({len(ids)})")
    print(f"    {shown}\n")