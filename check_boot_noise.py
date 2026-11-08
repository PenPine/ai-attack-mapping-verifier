import glob
import json
from collections import Counter, defaultdict
from datetime import datetime

from extraction.extract_pool import load_events


def ts(e):
    v = e.get("EventTime") or e.get("TimeCreated")   # one consistent clock for everything
    if not v:
        return None
    s = str(v).replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


raw = load_events(glob.glob("data/raw/apt29_evals_day1_manual/*.json")[0])

print("Boot/shutdown markers in the raw apt29 file:")
markers = []
for e in raw:
    eid, src = e.get("EventID"), str(e.get("SourceName", ""))
    if eid in (6005, 6006, 6009, 6013) or ("Kernel-General" in src and eid == 12) \
            or ("Kernel-Boot" in src and eid == 20):
        markers.append((ts(e), eid, src))
for t, eid, src in sorted(markers, key=lambda m: (m[0] is None, m[0])):
    print("  ", t, eid, src)

boots = [t for t, eid, src in markers if t and eid in (6005, 6009)]
boot = min(boots) if boots else None
print("\nassumed boot time:", boot)

pool = [json.loads(l) for l in open("results/pool_clean.jsonl") if l.strip()]
apt = [p for p in pool if p["source_file"].startswith("apt29")]

print("\napt29-sourced events per technique, and how many fall in [boot-60s, boot+300s]:")
tot, win = Counter(), Counter()
win_clusters = defaultdict(set)
for p in apt:
    t = ts(p["event"])
    tot[p["technique_label"]] += 1
    if boot and t and -60 <= (t - boot).total_seconds() <= 300:
        win[p["technique_label"]] += 1
        win_clusters[p["technique_label"]].add(p["cluster_id"])
for tech in sorted(tot):
    print(f"  {tech:<11}{tot[tech]:>5} apt29 events, {win[tech]:>4} in boot window "
          f"({len(win_clusters[tech])} clusters)")

print("\napt29 T1055: top SourceImage -> TargetImage")
c = Counter()
for p in apt:
    if p["technique_label"] == "T1055":
        e = p["event"]
        c[(str(e.get("SourceImage", "")).split("\\")[-1].lower(),
           str(e.get("TargetImage", "")).split("\\")[-1].lower())] += 1
for (s, t), n in c.most_common(8):
    print(f"  {n:4d}  {s} -> {t}")

print("\napt29 T1003.001: top SourceImage")
c = Counter(str(p["event"].get("SourceImage", "")).split("\\")[-1].lower()
            for p in apt if p["technique_label"] == "T1003.001")
for s, n in c.most_common(6):
    print(f"  {n:4d}  {s}")