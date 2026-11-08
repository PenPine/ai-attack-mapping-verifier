"""
build_eval_set.py
Builds the Stage 3 evaluation set from the cleaned pool.

Design decisions fixed BEFORE seeing any Stage 3 results (do not change them afterwards):
  - unit of analysis = attack-action cluster
  - at most K_PER_CLUSTER events per cluster, drawn with a fixed per-cluster seed
  - decoy pairs follow the PR2 rule (same tactic where one exists)
  - T1021.002 has no same-tactic partner among the 10 techniques -> excluded from the misleading condition

v3 (PR5): reads the v3 pool and writes results/eval_set_v3.jsonl; results/eval_set.jsonl (PR4) is left as is.
The seed is unchanged and per cluster, so every cluster that survives in v3 gets the same events as in PR4.
"""
import json
import random
from collections import defaultdict

SEED = "stage3-v1"
K_PER_CLUSTER = 3
POOL = "results/pool_clean_v3.jsonl"
BASELINE = "results/baseline_clean_v3.jsonl"
OUT = "results/eval_set_v3.jsonl"

DECOY = {
    "T1059.001": "T1059.003",
    "T1059.003": "T1059.001",
    "T1003.001": "T1003.006",
    "T1003.006": "T1003.001",
    "T1055": "T1562.002",
    "T1562.002": "T1055",
    "T1053.005": "T1547.001",
    "T1547.001": "T1546.003",
    "T1546.003": "T1053.005",
    "T1021.002": None,
}


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


pool = load(POOL)
base = {b["event_uid"]: b for b in load(BASELINE)}

by_cluster = defaultdict(list)
for p in pool:
    by_cluster[p["cluster_id"]].append(p)

clusters_by_tech = defaultdict(set)
for cid, evs in by_cluster.items():
    clusters_by_tech[evs[0]["technique_label"]].add(cid)

eval_rows, dropped = [], 0
for cid, events in sorted(by_cluster.items()):
    events = sorted(events, key=lambda p: p["event_uid"])
    usable = []
    for p in events:
        pred = base[p["event_uid"]]["prediction"]
        if "error" in pred or "predicted_technique" not in pred:
            dropped += 1
            continue
        usable.append((p, pred))
    rng = random.Random(f"{SEED}|{cid}")
    chosen = rng.sample(usable, min(K_PER_CLUSTER, len(usable))) if usable else []
    for p, pred in chosen:
        tech = p["technique_label"]
        row = {
            "event_uid": p["event_uid"],
            "cluster_id": cid,
            "technique_label": tech,
            "decoy_technique": DECOY[tech],
            "baseline": {
                "predicted_technique": pred["predicted_technique"],
                "confidence": pred.get("confidence"),
                "reasoning": pred.get("reasoning"),
            },
            "baseline_correct": pred["predicted_technique"] == tech,
        }
        if tech == "T1059.001":
            text = str(p["event"].get("ScriptBlockText", "")).lstrip().lower()
            row["script_kind"] = "function_definition" if text.startswith("function") else "other"
        eval_rows.append(row)

with open(OUT, "w") as f:
    for r in eval_rows:
        f.write(json.dumps(r) + "\n")

n_clusters = len({r["cluster_id"] for r in eval_rows})
print(f"eval events: {len(eval_rows)}   clusters: {n_clusters}   dropped (no baseline prediction): {dropped}")
print()
print(f"{'Technique':<11}{'events':>7}{'clusters':>9}{'base ok':>8}   decoy")
by_tech = defaultdict(list)
for r in eval_rows:
    by_tech[r["technique_label"]].append(r)
for t in sorted(DECOY):
    rows = by_tech.get(t, [])
    d = DECOY[t]
    decoy_txt = f"{d} ({len(clusters_by_tech[d])} clusters in pool)" if d else "none (excluded from misleading)"
    print(f"{t:<11}{len(rows):>7}{len({r['cluster_id'] for r in rows}):>9}"
          f"{sum(r['baseline_correct'] for r in rows):>8}   {decoy_txt}")

fd = [r for r in eval_rows if r.get("script_kind") == "function_definition"]
ot = [r for r in eval_rows if r.get("script_kind") == "other"]
print()
print("T1059.001 baseline-correct by script kind:")
print(f"  function_definition: {sum(r['baseline_correct'] for r in fd)}/{len(fd)}")
print(f"  other:               {sum(r['baseline_correct'] for r in ot)}/{len(ot)}")

n_mis = sum(1 for r in eval_rows if r["decoy_technique"])
n_calls = len(eval_rows) + n_mis + len(eval_rows)
print()
print(f"planned verification calls: genuine {len(eval_rows)} + misleading {n_mis} + neutral {len(eval_rows)} = {n_calls}")
print(f"rough cost at ~$0.01/call: ${n_calls * 0.01:.1f}  (guess: baseline cost $3.9 / 718 calls, verification prompts are longer)")