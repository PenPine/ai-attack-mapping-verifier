"""
pr4_rule_peek.py
What do the events behind each rule label look like? Lists the distinct values of a few key fields for the
techniques whose labels came up as questionable (and the other small ones). No API calls, no expertise needed:
it shows how specific each rule really is, for example whether every event labeled T1021.002 is PsExec.

    python dev_checks/pr4_rule_peek.py            all techniques below
    python dev_checks/pr4_rule_peek.py T1021.002  one technique
"""
import json
import sys
from collections import defaultdict

FIELDS = {
    "T1021.002": ["EventID", "ServiceName", "ImagePath", "Image"],
    "T1059.003": ["ParentImage", "Image"],
    "T1055": ["SourceImage", "TargetImage", "StartFunction"],
    "T1562.002": ["EventID", "TargetObject"],
    "T1053.005": ["EventID", "Image"],
    "T1547.001": ["TargetObject"],
    "T1546.003": ["EventID"],
    "T1003.001": ["SourceImage", "TargetImage", "GrantedAccess"],
    "T1003.006": ["EventID", "AccessMask"],
}
TOP = 12


def short(v, n=70):
    s = "-" if v in (None, "") else str(v).replace("\n", " ")
    return s if len(s) <= n else s[:n] + "..."


pool = [json.loads(l) for l in open("results/pool_clean.jsonl", encoding="utf-8") if l.strip()]
want = sys.argv[1:] or list(FIELDS)
for t in want:
    fields = FIELDS.get(t, ["EventID"])
    ev = [p for p in pool if p["technique_label"] == t]
    groups = defaultdict(lambda: [0, set()])
    for p in ev:
        k = tuple(short(p["event"].get(f)) for f in fields)
        groups[k][0] += 1
        groups[k][1].add(p["cluster_id"])
    print("=" * 78)
    print(f"{t}: {len(ev)} events, {len({p['cluster_id'] for p in ev})} clusters, {len(groups)} distinct combinations of {', '.join(fields)}")
    for k, (n, cl) in sorted(groups.items(), key=lambda kv: -kv[1][0])[:TOP]:
        print(f"  {n:>4} events {len(cl):>3} clusters   " + "  |  ".join(f"{f}={v}" for f, v in zip(fields, k)))