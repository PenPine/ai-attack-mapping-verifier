import json
from collections import defaultdict, Counter

pool = {p["event_uid"]: p for p in
        (json.loads(l) for l in open("results/pool_clean.jsonl") if l.strip())}
base = [json.loads(l) for l in open("results/baseline_clean.jsonl") if l.strip()]

rows = []
for b in base:
    p = b["prediction"]
    if "error" in p or "predicted_technique" not in p:
        continue
    rows.append({
        "cluster": b["cluster_id"],
        "tech": b["technique_label"],
        "stratum": pool[b["event_uid"]]["stratum"],
        "ok": int(p["predicted_technique"] == b["technique_label"]),
        "pred": p["predicted_technique"],
    })


def cluster_scores(subset):
    by = defaultdict(list)
    for r in subset:
        by[r["cluster"]].append(r["ok"])
    return [sum(v) / len(v) for v in by.values()]


def report(name, subset):
    cs = cluster_scores(subset)
    if not cs:
        return
    ev = sum(r["ok"] for r in subset) / len(subset)
    print(f"{name:<28}{len(subset):>7}{len(cs):>9}{ev * 100:>10.1f}%{sum(cs) / len(cs) * 100:>11.1f}%")


print(f"{'group':<28}{'events':>7}{'clusters':>9}{'event acc':>11}{'cluster acc':>12}")
report("all", rows)
report("excluding T1059.001", [r for r in rows if r["tech"] != "T1059.001"])
report("T1059.001 only", [r for r in rows if r["tech"] == "T1059.001"])
for s in ("atomic", "apt29"):
    report(f"stratum {s}", [r for r in rows if r["stratum"] == s])
    report(f"  {s}, excl. T1059.001", [r for r in rows if r["stratum"] == s and r["tech"] != "T1059.001"])
for t in sorted({r["tech"] for r in rows}):
    report(f"technique {t}", [r for r in rows if r["tech"] == t])

print()
print("what the model answered when wrong (events), by true technique:")
wrong = defaultdict(Counter)
for r in rows:
    if not r["ok"]:
        wrong[r["tech"]][r["pred"]] += 1
for t in sorted(wrong):
    print(f"  {t}: {dict(wrong[t].most_common())}")