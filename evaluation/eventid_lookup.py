"""
evaluation/eventid_lookup.py
Event ID lookup baseline: predict the technique from the Event ID alone (majority label per Event ID).
Same method as pr4_eventid_baseline.py, with the tie rule made explicit. No API calls.

Rows are (cluster_id, technique_label, event_id) tuples, one per scored event.

Tie rule (TIE_RULE = "none"): when two or more labels share the top count for an Event ID, the lookup
answers NONE, which is counted wrong, exactly like an Event ID the lookup has never seen. The PR4 script
broke ties by first appearance in baseline_clean.jsonl (Counter.most_common), which depends on file order.
"upper" is a sensitivity bound only: a tie is resolved to the true label whenever the true label is tied.
"""
from collections import Counter, defaultdict

NONE = "NONE"


def build_table(rows):
    table = defaultdict(Counter)
    for _, label, eid in rows:
        table[eid][label] += 1
    return table


def pick(counts, truth=None, tie_rule="none"):
    """Majority label of a Counter. Returns (label, tied). Ignores zero or negative counts."""
    counts = +counts
    if not counts:
        return NONE, False
    top = max(counts.values())
    leaders = sorted(t for t, n in counts.items() if n == top)
    if len(leaders) == 1:
        return leaders[0], False
    if tie_rule == "upper" and truth in leaders:
        return truth, True
    return NONE, True


def without_cluster(table, rows, cluster):
    """Copy of the table with every event of `cluster` removed."""
    sub = {e: Counter(c) for e, c in table.items()}
    for cid, label, eid in rows:
        if cid == cluster:
            sub[eid][label] -= 1
    return sub


def evaluate(rows, loo=True, tie_rule="none"):
    """Event- and cluster-level accuracy of the lookup, plus every prediction decided by a tie."""
    table = build_table(rows)
    by_cluster = defaultdict(list)
    for r in rows:
        by_cluster[r[0]].append(r)
    ev_ok, cl_acc, per_tech, ties = 0, {}, defaultdict(list), []
    for cid, items in by_cluster.items():
        tab = without_cluster(table, rows, cid) if loo else table
        oks = []
        for _, label, eid in items:
            pred, tied = pick(tab.get(eid, Counter()), label, tie_rule)
            oks.append(int(pred == label))
            if tied:
                ties.append({"cluster_id": cid, "technique_label": label, "event_id": eid, "prediction": pred,
                             "counts": dict(sorted((+tab[eid]).items()))})
        ev_ok += sum(oks)
        cl_acc[cid] = sum(oks) / len(oks)
        per_tech[items[0][1]].append(cl_acc[cid])
    return {"event_acc": ev_ok / len(rows), "event_ok": ev_ok, "n_events": len(rows),
            "cluster_acc": sum(cl_acc.values()) / len(cl_acc), "n_clusters": len(cl_acc),
            "per_tech": dict(per_tech), "ties": ties,
            "tie_clusters": len({t["cluster_id"] for t in ties})}
