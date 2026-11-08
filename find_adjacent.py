"""
find_adjacent.py
Feasibility check for Stage 3 evidence. No API calls, nothing is modified.

For every event in the eval set, look for a related REAL event in the same raw file:
  - same Hostname, different EventID, EventID in INFORMATIVE (noise types are never evidence)
  - process-linked (shared process GUID or PID): within LINKED_WINDOW seconds
  - otherwise time-only: within UNLINKED_WINDOW seconds
  - timestamps are only compared within the same field family, because the files mix
    clocks (TimeCreated and UtcTime differ by hours in several datasets)
The rule is fixed here, before any Stage 3 result exists.
"""
import glob
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone

from extraction.extract_pool import load_events

LINKED_WINDOW = 120
UNLINKED_WINDOW = 5
INFORMATIVE = {1, 3, 8, 11, 19, 20, 21, 22, 23, 4103, 4104, 4624, 4648,
               4662, 4688, 4697, 4698, 5140, 5145, 7045}
TIME_KINDS = [("R", ["TimeCreated", "EventTime"]), ("U", ["UtcTime"]), ("L", ["@timestamp"])]
GUID_FIELDS = ["ProcessGuid", "SourceProcessGuid", "TargetProcessGuid"]
PID_FIELDS = ["ProcessId", "SourceProcessId", "TargetProcessId", "NewProcessId"]
SHOW = ["Image", "CommandLine", "TargetObject", "DestinationIp", "DestinationPort",
        "QueryName", "ScriptBlockText", "TargetImage", "SourceImage"]


def parse_time(e):
    for kind, fields in TIME_KINDS:
        for f in fields:
            v = e.get(f)
            if not v:
                continue
            s = str(v).replace("T", " ").replace("Z", "")
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    return kind, datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
                except ValueError:
                    pass
    return None, None


def link_keys(e):
    guids = {e[f] for f in GUID_FIELDS if e.get(f)}
    pids = {str(e[f]) for f in PID_FIELDS if e.get(f) not in (None, "")}
    return guids, pids


def brief(e):
    parts = [f"{k}={str(e[k])[:70].strip()}" for k in SHOW if e.get(k)]
    return f"EID {e.get('EventID')} " + " | ".join(parts[:3])


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


pool = {p["event_uid"]: p for p in load("results/pool_clean.jsonl")}
eval_rows = load("results/eval_set.jsonl")

by_file = defaultdict(list)
for r in eval_rows:
    p = pool[r["event_uid"]]
    by_file[p["source_file"]].append((r, p))

status = {}          # event_uid -> "linked" / "time-only" / "none" / "not found"
examples = defaultdict(list)
kinds0 = Counter()

for basename, items in by_file.items():
    paths = glob.glob(f"data/raw/*/{basename}")
    if not paths:
        print("WARNING: raw file not found:", basename)
        continue
    raw = load_events(paths[0])
    wanted = {json.dumps(p["event"], sort_keys=True): r["event_uid"] for r, p in items}
    wanted_eids = {p["event"].get("EventID") for r, p in items}

    index = defaultdict(list)
    located = {}
    for i, e in enumerate(raw):
        eid = e.get("EventID")
        if eid in wanted_eids:
            ks = json.dumps(e, sort_keys=True)
            if ks in wanted:
                located[wanted[ks]] = i
        if eid in INFORMATIVE:
            kind, t = parse_time(e)
            if t is not None:
                g, pi = link_keys(e)
                index[str(e.get("Hostname", ""))].append((kind, t, eid, g, pi, i))

    for r, p in items:
        uid = r["event_uid"]
        i0 = located.get(uid)
        if i0 is None:
            status[uid] = "not found"
            continue
        e0 = raw[i0]
        kind0, t0 = parse_time(e0)
        kinds0[kind0] += 1
        if t0 is None:
            status[uid] = "none"
            continue
        g0, p0 = link_keys(e0)
        best = None
        for kind, t, eid, g, pi, j in index[str(e0.get("Hostname", ""))]:
            if j == i0 or eid == e0.get("EventID") or kind != kind0:
                continue
            dt = abs(t - t0)
            linked = bool((g0 & g) or (p0 & pi))
            if linked and dt <= LINKED_WINDOW:
                rank = (0, dt)
            elif not linked and dt <= UNLINKED_WINDOW:
                rank = (1, dt)
            else:
                continue
            if best is None or rank < best[0]:
                best = (rank, j, dt, linked)
        if best is None:
            status[uid] = "none"
        else:
            status[uid] = "linked" if best[3] else "time-only"
            if len(examples[status[uid]]) < 6:
                examples[status[uid]].append(
                    (p["technique_label"], brief(e0), brief(raw[best[1]]), best[2]))

print(f"{'Technique':<11}{'events':>7}{'linked':>8}{'time-only':>10}{'none':>6}{'not found':>10}")
by_tech = defaultdict(Counter)
for r in eval_rows:
    by_tech[r["technique_label"]][status.get(r["event_uid"], "not found")] += 1
tot = Counter()
for t in sorted(by_tech):
    c = by_tech[t]
    tot.update(c)
    print(f"{t:<11}{sum(c.values()):>7}{c['linked']:>8}{c['time-only']:>10}{c['none']:>6}{c['not found']:>10}")
n = sum(tot.values())
print(f"{'ALL':<11}{n:>7}{tot['linked']:>8}{tot['time-only']:>10}{tot['none']:>6}{tot['not found']:>10}")
print(f"\ncoverage: {(tot['linked'] + tot['time-only']) / n * 100:.0f}%  (linked only: {tot['linked'] / n * 100:.0f}%)")
print("time-field family of originals:", dict(kinds0))

print()
for kind in ("linked", "time-only"):
    print(f"--- examples ({kind}) ---")
    for tech, orig, ev, dt in examples[kind]:
        print(f"{tech}\n   original: {orig}\n   evidence: {ev}   (dt={dt:.1f}s)")
    print()