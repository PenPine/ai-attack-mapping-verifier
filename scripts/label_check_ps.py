"""
scripts/label_check_ps.py
Read-only (2026-10-30): looks for the process-creation events (Sysmon 1, Security 4688) of the three
T1547.001 pool events, for the chain notes in results/stage3_v3/label_check.md. No API calls.

Run from the project root:  python scripts/label_check_ps.py
"""
import glob, json, sys
sys.path.insert(0, ".")
from extraction.extract_pool import load_events
from evidence.stage3_builder import to_pid
pool = {json.loads(l)["event_uid"]: json.loads(l) for l in open("results/pool_clean_v3.jsonl", encoding="utf-8")}
for uid in ("d2d8a80c7c8a667f", "2a127f68cdc4410d", "243e55d798340ba4"):
    p = pool[uid]; e = p["event"]
    raw = load_events(glob.glob(f"data/raw/*/{p['source_file']}")[0])
    g = str(e.get("ProcessGuid")).strip("{}").lower(); pid = to_pid(e.get("ProcessId"))
    s1 = [x for x in raw if x.get("EventID") == 1 and str(x.get("ProcessGuid", "")).strip("{}").lower() == g]
    c4688 = [(x.get("EventTime"), x.get("NewProcessName"), x.get("ParentProcessName")) for x in raw
             if x.get("EventID") == 4688 and to_pid(x.get("NewProcessId")) == pid]
    other = [(x.get("EventID"), x.get("UtcTime") or x.get("EventTime")) for x in raw
             if str(x.get("ProcessGuid", "")).strip("{}").lower() == g][:3]
    print(uid, "pid", pid, "sysmon1:", len(s1), "4688 same pid:", c4688, "first events with this guid:", other,
          "sysmon1 in file:", sum(1 for x in raw if x.get("EventID") == 1), "4688 in file:", sum(1 for x in raw if x.get("EventID") == 4688))
