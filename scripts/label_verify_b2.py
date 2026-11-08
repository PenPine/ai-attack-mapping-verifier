"""
scripts/label_verify_b2.py
Read-only (2026-11-08, after the Stage 3 results): every T1003.006 pool event (subject, replication-rights GUIDs)
and the events of logon session 0x167eda on NEWYORK. No API calls.

Run from the project root:  python scripts/label_verify_b2.py
"""
import glob, json, re, sys
sys.path.insert(0, ".")
from extraction.extract_pool import load_events

for l in open("results/pool_clean_v3.jsonl", encoding="utf-8"):
    p = json.loads(l)
    if p["technique_label"] == "T1003.006":
        e = p["event"]
        g = sorted(set(re.findall(r"1131f6a[a-d]-9c07|89e95b76", str(e.get("Properties")))))
        print(f"{p['event_uid']}  {p['source_file'][:45]:<45} {e.get('Hostname')}  subject {e.get('SubjectUserName')} "
              f"sid {e.get('SubjectUserSid')}  logon {e.get('SubjectLogonId')}  rights {g}")

raw = load_events(glob.glob("data/raw/*/apt29_evals_day1_manual_2020-05-01225525.json")[0])
print("\nevents on NEWYORK with logon id 0x167eda:")
for i, x in enumerate(raw):
    if str(x.get("Hostname", "")).lower().startswith("newyork") and "0x167eda" in (str(x.get("TargetLogonId")), str(x.get("SubjectLogonId"))):
        print(f"  {i} {x.get('EventID')} {x.get('EventTime')} type {x.get('LogonType')} target {x.get('TargetUserName')} "
              f"subject {x.get('SubjectUserName')} ip {x.get('IpAddress')} process {x.get('ProcessName')} auth {x.get('AuthenticationPackageName')}")
print("\nhosts with a 4662 that has ObjectServer DS:")
print(sorted({str(x.get("Hostname")) for x in raw if x.get("EventID") == 4662 and x.get("ObjectServer") == "DS"}))
