import json
import re
from collections import Counter, defaultdict
import sys

sys.path.insert(0, ".")          # run from the project root: python dev_checks/check_leaks_and_clusters.py
from extraction.clean_event import clean_event

ID_RE = re.compile(r"\bT1\d{3}(?:\.\d{3})?\b")
pool = [json.loads(l) for l in open("results/pool_clean.jsonl") if l.strip()]

# 1) ATT&CK IDs visible in what the model saw
hits = defaultdict(list)
for p in pool:
    for field, val in clean_event(p["event"]).items():
        text = str(val)
        for m in ID_RE.finditer(text):
            snippet = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
            hits[p["technique_label"]].append((p["event_uid"], m.group(0), field, snippet))

print("1) ATT&CK technique IDs visible in model inputs")
if not hits:
    print("   none found")
for tech, items in sorted(hits.items()):
    n_events = len({h[0] for h in items})
    print(f"   {tech}: {n_events} events affected")
    for h in items[:3]:
        print(f"      {h[1]} in field {h[2]}: ...{h[3]}...")

# 2) cluster sizes per technique
size = Counter(p["cluster_id"] for p in pool)
tech_of = {p["cluster_id"]: p["technique_label"] for p in pool}
table = defaultdict(Counter)
for cid, n in size.items():
    table[tech_of[cid]]["1 event" if n == 1 else "2-3 events" if n <= 3 else "4+ events"] += 1

print()
print("2) clusters by size")
print(f"   {'Technique':<11}{'1 event':>9}{'2-3':>6}{'4+':>6}")
for t in sorted(table):
    c = table[t]
    print(f"   {t:<11}{c['1 event']:>9}{c['2-3 events']:>6}{c['4+ events']:>6}")
single = sum(c["1 event"] for c in table.values())
print(f"   single-event clusters: {single} of {len(size)}")