"""
pr4_t1059_003_check.py
The T1059.003 rule in extraction/config.py keeps events whose ParentImage CONTAINS the text "cmd.exe".
That text is also inside "dsregcmd.exe". This script lists the T1059.003 events whose parent process is not
exactly cmd.exe and shows the baseline numbers with and without them. No API calls; the pool is not changed.
"""
import json
import re
from collections import defaultdict


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def basename(v):
    return re.split(r"[\\/]", str(v or ""))[-1].lower()


pool = load("results/pool_clean.jsonl")
pred = {b["event_uid"]: b["prediction"] for b in load("results/baseline_clean.jsonl")}

bad = [p for p in pool if p["technique_label"] == "T1059.003" and basename(p["event"].get("ParentImage")) != "cmd.exe"]
good = [p for p in pool if p["technique_label"] == "T1059.003" and basename(p["event"].get("ParentImage")) == "cmd.exe"]
print(f"T1059.003 events in the pool: {len(bad) + len(good)}   parent is exactly cmd.exe: {len(good)}   parent is something else: {len(bad)}\n")
for p in bad:
    e = p["event"]
    answer = pred.get(p["event_uid"], {}).get("predicted_technique", "(not scored)")
    print(f"event_uid {p['event_uid']}\n  cluster   {p['cluster_id']}\n  source    {p['source_file']}\n"
          f"  parent    {e.get('ParentImage')}\n  image     {e.get('Image')}\n  command   {str(e.get('CommandLine'))[:90]}\n"
          f"  model answered: {answer}\n")
print("For comparison, events whose parent really is cmd.exe:")
for p in good:
    print(f"  {p['event_uid']}   model answered: {pred.get(p['event_uid'], {}).get('predicted_technique', '(not scored)')}")

drop = {p["event_uid"] for p in bad}


def agreement(skip):
    ev_ok = ev_n = 0
    cl = defaultdict(list)
    for p in pool:
        if p["event_uid"] in skip:
            continue
        pr = pred.get(p["event_uid"], {})
        if "predicted_technique" not in pr:
            continue
        ok = int(pr["predicted_technique"] == p["technique_label"])
        ev_ok, ev_n = ev_ok + ok, ev_n + 1
        cl[(p["cluster_id"], p["technique_label"])].append(ok)
    shares = [(t, sum(v) / len(v)) for (c, t), v in cl.items()]
    ex = [s for t, s in shares if t != "T1059.001"]
    t3 = [s for t, s in shares if t == "T1059.003"]
    return (ev_n, len(shares), ev_ok / ev_n, sum(s for _, s in shares) / len(shares), len(ex), sum(ex) / len(ex),
            len(t3), (sum(t3) / len(t3)) if t3 else float("nan"))


print(f"\n{'':<34}{'events':>8}{'clusters':>10}{'event %':>9}{'cluster %':>11}{'clusters excl 1059.001':>24}{'cluster % excl':>16}{'T1059.003 clusters':>20}{'T1059.003 %':>13}")
for name, skip in (("current pool", set()), ("without the non-cmd.exe parents", drop)):
    n, k, e, c, kx, cx, k3, c3 = agreement(skip)
    print(f"{name:<34}{n:>8}{k:>10}{e * 100:>8.1f}%{c * 100:>10.1f}%{kx:>24}{cx * 100:>15.1f}%{k3:>20}{c3 * 100:>12.0f}%")
print("\nThe second row is a sensitivity check only. The pool is unchanged. The exclusion is based on the parent "
      "process in the event, not on the model's answer.")