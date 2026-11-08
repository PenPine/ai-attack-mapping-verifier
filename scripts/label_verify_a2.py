"""
scripts/label_verify_a2.py
Read-only (2026-11-08, after the Stage 3 results): process chain of the javamtsup New-Service call (raw index 50923
of the APT29 day-1 file, Sysmon 1 ParentProcessGuid links) and remote-access signs on SCRANTON from 23:00 to
23:06 (4624 type 3/10, 5140/5145, 4648, Sysmon 3 on 135/139/445/5985/5986). No API calls.

Run from the project root:  python scripts/label_verify_a2.py
"""
import glob, sys
sys.path.insert(0, ".")
from extraction.extract_pool import load_events

raw = load_events(glob.glob("data/raw/*/apt29_evals_day1_manual_2020-05-01225525.json")[0])
e = raw[50923]
print("4103 ContextInfo:\n", str(e.get("ContextInfo"))[:900])
pid = int(str(e.get("ExecutionProcessID")))
print("ExecutionProcessID:", pid)
H = "scranton.dmevals.local"
def host(x): return str(x.get("Hostname") or "").lower()

# Sysmon 1 events on SCRANTON, by process GUID, before the install
procs = {}
for x in raw[:50923]:
    if x.get("EventID") == 1 and host(x) == H:
        procs[str(x.get("ProcessGuid")).lower()] = x
cand = [x for x in procs.values() if str(x.get("ProcessId")) == str(pid)]
print(f"\nSysmon 1 on SCRANTON with ProcessId {pid} before the install:", len(cand))
cur = cand[-1] if cand else None
depth = 0
while cur is not None and depth < 12:
    print(f"  [{depth}] {cur.get('UtcTime')}  pid {cur.get('ProcessId')}  {cur.get('Image')}\n"
          f"       cmd: {str(cur.get('CommandLine'))[:300]}\n       user: {cur.get('User')}  integrity: {cur.get('IntegrityLevel')}  "
          f"logon id: {cur.get('LogonId')}")
    cur = procs.get(str(cur.get("ParentProcessGuid")).lower())
    depth += 1

print("\nRemote-access signs on SCRANTON, 23:00-23:06 (EventTime):")
for i, x in enumerate(raw):
    t = str(x.get("EventTime", ""))
    if host(x) != H or not ("2020-05-01 23:00" <= t[:16] <= "2020-05-01 23:06"):
        continue
    eid = x.get("EventID")
    if eid == 4624 and str(x.get("LogonType")) in ("3", "10"):
        print(f"  {i} 4624 {t} type {x.get('LogonType')} user {x.get('TargetDomainName')}\\{x.get('TargetUserName')} "
              f"from {x.get('IpAddress')} ws {x.get('WorkstationName')} logonid {x.get('TargetLogonId')}")
    elif eid in (5140, 5145):
        print(f"  {i} {eid} {t} share {x.get('ShareName')} target {x.get('RelativeTargetName')} from {x.get('IpAddress')} user {x.get('SubjectUserName')}")
    elif eid == 3 and str(x.get("DestinationPort")) in ("135", "445", "139", "5985", "5986") :
        print(f"  {i} sysmon3 {t} {x.get('Image')} {x.get('SourceIp')}:{x.get('SourcePort')} -> {x.get('DestinationIp')}:{x.get('DestinationPort')} initiated {x.get('Initiated')}")
    elif eid == 4648:
        print(f"  {i} 4648 {t} {x.get('SubjectUserName')} -> {x.get('TargetUserName')} on {x.get('TargetServerName')} proc {x.get('ProcessName')}")
