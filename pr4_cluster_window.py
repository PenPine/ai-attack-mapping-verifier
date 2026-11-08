"""
pr4_cluster_window.py
Sensitivity of the cluster definition to the time window (answers the reviewer question about how the
66 clusters were formed). No API calls. Reads results/pool_clean.jsonl and results/baseline_clean.jsonl.

Cluster = same technique label + same source file + same time bucket of W seconds. W = 60 is the original
definition (the "same minute" rule in clean_pool.py) and must reproduce the current cluster count.
The main analysis stays at 60 s; this only shows whether the picture changes with W.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone

WINDOWS = [30, 60, 120, 300]
TECHS = ["T1003.001", "T1003.006", "T1021.002", "T1053.005", "T1055",
         "T1059.001", "T1059.003", "T1546.003", "T1547.001", "T1562.002"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def ts_of(e):
    # same field priority as clean_pool.py: UtcTime, then TimeCreated, then EventTime
    v = e.get("UtcTime") or e.get("TimeCreated") or e.get("EventTime")
    if not v:
        return None
    s = str(v).replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    return None


pool = load("results/pool_clean.jsonl")
pred = {b["event_uid"]: b["prediction"] for b in load("results/baseline_clean.jsonl")}
original_clusters = len({p["cluster_id"] for p in pool})
no_time = sum(1 for p in pool if ts_of(p["event"]) is None)
print(f"events in pool: {len(pool)}   clusters in pool_clean (original, 60 s): {original_clusters}   events without a parseable time: {no_time}")


def clusters_for(W):
    c = defaultdict(list)       # key -> list of (technique, correct or None)
    for p in pool:
        t = ts_of(p["event"])
        key = (p["technique_label"], p["source_file"], "NA" if t is None else int(t // W))
        pr = pred.get(p["event_uid"], {})
        ok = None if "predicted_technique" not in pr else int(pr["predicted_technique"] == p["technique_label"])
        c[key].append((p["technique_label"], ok))
    return c


def summarize(c):
    per = {}
    for key, evs in c.items():
        scored = [o for _, o in evs if o is not None]
        if scored:                                   # a cluster with no scored event cannot be scored
            per[key] = (key[0], sum(scored) / len(scored), len(evs))
    return per


results = {}
for W in WINDOWS:
    per = summarize(clusters_for(W))
    results[W] = per
    if W == 60 and len(per) != original_clusters:
        print(f"WARNING: at W=60 this script finds {len(per)} clusters, the pool has {original_clusters}. "
              "The time field or parsing differs from clean_pool.py; do not use the table below until this is explained.")

print(f"\n{'window':>8}{'clusters':>10}{'excl.T1059.001':>16}{'singletons':>12}"
      f"{'acc (all)':>11}{'acc (excl)':>12}{'correct/wrong all':>19}{'correct/wrong excl':>20}")
for W in WINDOWS:
    per = results[W]
    allv = list(per.values())
    ex = [v for v in allv if v[0] != "T1059.001"]
    acc = sum(v[1] for v in allv) / len(allv)
    acc_ex = sum(v[1] for v in ex) / len(ex)
    singles = sum(1 for v in allv if v[2] == 1)
    ca, ce = round(acc * len(allv)), round(acc_ex * len(ex))
    mark = "  <- original" if W == 60 else ""
    print(f"{str(W) + ' s':>8}{len(allv):>10}{len(ex):>16}{singles:>12}{acc * 100:>10.1f}%{acc_ex * 100:>11.1f}%"
          f"{f'{ca}/{len(allv) - ca}':>19}{f'{ce}/{len(ex) - ce}':>20}{mark}")

print("\nclusters per technique")
print(f"{'technique':<12}" + "".join(f"{str(W) + ' s':>8}" for W in WINDOWS))
for t in TECHS:
    print(f"{t:<12}" + "".join(f"{sum(1 for v in results[W].values() if v[0] == t):>8}" for W in WINDOWS))
print("\nIf the cluster counts and the accuracy barely move, the choice of 60 s does not drive the results.\n"
      "If T1562.002 or T1055 change a lot, those techniques are the ones to describe with care.")