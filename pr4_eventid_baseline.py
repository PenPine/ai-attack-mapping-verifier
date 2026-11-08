"""
pr4_eventid_baseline.py
A baseline that does not use an LLM: predict the technique from the Event ID alone.
No API calls. Reads results/pool_clean.jsonl and results/baseline_clean.jsonl.

Two versions of the lookup (Event ID -> most common technique label):
  in-sample           built on the whole pool. This is a CEILING for "reading the event type".
  leave-one-cluster   built without the cluster being predicted. Unseen Event IDs get NONE (counted wrong).
Compared with the LLM baseline on the same scored events.
"""
import json
from collections import Counter, defaultdict

TECHS = ["T1003.001", "T1003.006", "T1021.002", "T1053.005", "T1055",
         "T1059.001", "T1059.003", "T1546.003", "T1547.001", "T1562.002"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


pool = {p["event_uid"]: p for p in load("results/pool_clean.jsonl")}
rows = []          # (cluster, label, event id, llm answer)
for b in load("results/baseline_clean.jsonl"):
    pr = b["prediction"]
    if "predicted_technique" not in pr:
        continue
    rows.append((b["cluster_id"], b["technique_label"], str(pool[b["event_uid"]]["event"].get("EventID")), pr["predicted_technique"]))

table = defaultdict(Counter)
for _, label, eid, _ in rows:
    table[eid][label] += 1
majority = {e: c.most_common(1)[0][0] for e, c in table.items()}

by_cluster = defaultdict(list)
for r in rows:
    by_cluster[r[0]].append(r)


def lookup_loo(cluster):
    sub = defaultdict(Counter)
    for e, c in table.items():
        sub[e] = Counter(c)
    for _, label, eid, _ in by_cluster[cluster]:
        sub[eid][label] -= 1
    out = {}
    for e, c in sub.items():
        c = +c                                   # drop zero or negative counts
        out[e] = c.most_common(1)[0][0] if c else "NONE"
    return out


def evaluate(predictor):
    ev_ok = ev_n = 0
    cl, per_tech = [], defaultdict(list)
    for cid, items in by_cluster.items():
        loo = predictor(cid)
        oks = [int(loo(eid) == label) for _, label, eid, _ in items]
        ev_ok, ev_n = ev_ok + sum(oks), ev_n + len(oks)
        cl.append((items[0][1], sum(oks) / len(oks)))
        per_tech[items[0][1]].append(sum(oks) / len(oks))
    return ev_ok / ev_n, sum(a for _, a in cl) / len(cl), per_tech, ev_n


def pred_insample(cid):
    return lambda eid: majority.get(eid, "NONE")


def pred_loo(cid):
    tab = lookup_loo(cid)
    return lambda eid: tab.get(eid, "NONE")


def pred_llm_acc():
    ev_ok = sum(int(a == label) for _, label, _, a in rows)
    cl, per_tech = [], defaultdict(list)
    for cid, items in by_cluster.items():
        s = sum(int(a == label) for _, label, _, a in items) / len(items)
        cl.append(s)
        per_tech[items[0][1]].append(s)
    return ev_ok / len(rows), sum(cl) / len(cl), per_tech


llm_ev, llm_cl, llm_pt = pred_llm_acc()
in_ev, in_cl, in_pt, n = evaluate(pred_insample)
lo_ev, lo_cl, lo_pt, _ = evaluate(pred_loo)

print(f"scored events: {n}   clusters: {len(by_cluster)}\n")
print(f"{'':<34}{'event level':>13}{'cluster level':>15}")
print(f"{'LLM baseline':<34}{llm_ev * 100:>12.1f}%{llm_cl * 100:>14.1f}%")
print(f"{'Event ID lookup, in-sample':<34}{in_ev * 100:>12.1f}%{in_cl * 100:>14.1f}%   (ceiling)")
print(f"{'Event ID lookup, leave-one-cluster':<34}{lo_ev * 100:>12.1f}%{lo_cl * 100:>14.1f}%")

print(f"\ncluster-level accuracy by technique")
print(f"{'technique':<12}{'clusters':>9}{'LLM':>8}{'lookup in':>11}{'lookup loo':>12}")
mean = lambda v: sum(v) / len(v) * 100
for t in TECHS:
    if t in llm_pt:
        print(f"{t:<12}{len(llm_pt[t]):>9}{mean(llm_pt[t]):>7.0f}%{mean(in_pt[t]):>10.0f}%{mean(lo_pt[t]):>11.0f}%")

print("\nEvent IDs that carry more than one technique label (the lookup cannot separate these):")
for e, c in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
    if len(c) > 1:
        print(f"  EventID {e:<6} " + ", ".join(f"{t}: {n}" for t, n in c.most_common()))
print("\nRead: if the in-sample lookup is close to or above the LLM, then much of the LLM accuracy can be "
      "explained by event type alone, and the baseline accuracy should not be described as technique recognition.")