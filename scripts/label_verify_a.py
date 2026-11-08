"""
scripts/label_verify_a.py
Read-only (2026-11-08, after the Stage 3 results): the T1021.002 event 4fc6fdb9ffb5b639 (javamtsup service) and
every raw event in the APT29 day-1 file that mentions the service. No API calls. Follow-up: scripts/label_verify_a2.py.

Run from the project root:  python scripts/label_verify_a.py
"""
import glob, json, sys
sys.path.insert(0, ".")
from extraction.extract_pool import load_events

pool = {json.loads(l)["event_uid"]: json.loads(l) for l in open("results/pool_clean_v3.jsonl", encoding="utf-8")}
p = pool["4fc6fdb9ffb5b639"]
print("source:", p["source_file"], "| cluster:", p["cluster_id"])
print(json.dumps(p["event"], indent=1)[:3000])

raw = load_events(glob.glob(f"data/raw/*/{p['source_file'].split(chr(92))[-1].split('/')[-1]}")[0])
print("\nraw events:", len(raw))
SHOW = ["EventID", "Hostname", "Computer", "EventTime", "UtcTime", "Channel", "Image", "ParentImage", "CommandLine",
        "ParentCommandLine", "User", "SubjectUserName", "TargetUserName", "LogonType", "IpAddress", "SourceIp",
        "DestinationIp", "DestinationPort", "TargetFilename", "TargetObject", "Details", "ServiceName", "ImagePath",
        "ServiceFileName", "AccountName", "ShareName", "RelativeTargetName", "ProcessId", "ParentProcessId",
        "ProcessGuid", "ParentProcessGuid", "ScriptBlockText", "Payload"]
hits = [(i, e) for i, e in enumerate(raw) if "javamtsup" in json.dumps(e).lower()]
print("events mentioning javamtsup:", len(hits))
for i, e in hits:
    print(f"\n--- raw {i}")
    for k in SHOW:
        if e.get(k) not in (None, "", "-"):
            print(f"  {k}: {str(e[k])[:400]}")
