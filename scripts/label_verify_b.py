"""
scripts/label_verify_b.py
Read-only (2026-11-08, after the Stage 3 results): is NEWYORK a domain controller in the APT29 day-1 file
(Kerberos KDC events, DC service binaries, channels and IP per host)? Also prints the T1003.006 event
f75cb76d84f877ff. No API calls. Follow-up: scripts/label_verify_b2.py.

Run from the project root:  python scripts/label_verify_b.py
"""
import glob, json, sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
from extraction.extract_pool import load_events

pool = {json.loads(l)["event_uid"]: json.loads(l) for l in open("results/pool_clean_v3.jsonl", encoding="utf-8")}
p = pool["f75cb76d84f877ff"]
print("label:", p["technique_label"], "| source:", p["source_file"], "| cluster:", p["cluster_id"])
e = p["event"]
for k in ("EventID", "Hostname", "EventTime", "SubjectUserName", "SubjectDomainName", "SubjectUserSid", "SubjectLogonId",
          "ObjectServer", "ObjectType", "ObjectName", "OperationType", "AccessMask", "Properties"):
    print(f"  {k}: {str(e.get(k))[:300]}")

raw = load_events(glob.glob(f"data/raw/*/{p['source_file']}")[0])
def host(x): return str(x.get("Hostname") or "").lower()
hosts = Counter(host(x) for x in raw)
print("\nhosts in the file:", dict(hosts))

DC_ONLY = {4768: "Kerberos TGT issued (KDC)", 4769: "Kerberos service ticket issued (KDC)",
           4771: "Kerberos pre-auth failed (KDC)", 4662: "directory service object access",
           5136: "directory service object modified", 4929: "AD replica source naming context removed",
           4932: "AD replication of naming context began", 4933: "AD replication ended"}
by = defaultdict(Counter)
for x in raw:
    by[host(x)][x.get("EventID")] += 1
print("\nDC-indicative Security Event IDs per host:")
for h in hosts:
    print(f"  {h:<32}", {f"{k}": by[h][k] for k in DC_ONLY if by[h][k]})

chan = defaultdict(Counter)
for x in raw:
    chan[host(x)][x.get("Channel")] += 1
print("\nchannels per host:")
for h in hosts:
    print(f"  {h}: {dict(chan[h].most_common())}")

print("\nDC service binaries running on each host (Sysmon 1 Image / Sysmon 7 / any Image field):")
DC_BIN = ("ntdsai.dll", "dfsrs.exe", "ismserv.exe", "dns.exe", "ntfrs.exe", "kdcsvc.dll", "ntdsa.dll")
seen = defaultdict(set)
for x in raw:
    for f in ("Image", "ImageLoaded", "ParentImage", "TargetImage", "SourceImage"):
        v = str(x.get(f) or "").lower()
        for b in DC_BIN:
            if v.endswith(b):
                seen[host(x)].add(b)
for h in hosts:
    print(f"  {h}: {sorted(seen[h])}")

print("\nIP addresses seen for each host (Sysmon 3 SourceIp of initiated connections):")
ips = defaultdict(Counter)
for x in raw:
    if x.get("EventID") == 3 and str(x.get("Initiated")).lower() == "true":
        ips[host(x)][x.get("SourceIp")] += 1
for h in hosts:
    print(f"  {h}: {dict(ips[h].most_common(3))}")

print("\nSample 4768/4769 on NEWYORK (first 3):")
n = 0
for x in raw:
    if host(x).startswith("newyork") and x.get("EventID") in (4768, 4769):
        print(f"  {x.get('EventID')} {x.get('EventTime')} account {x.get('TargetUserName')} service {x.get('ServiceName')} from {x.get('IpAddress')}")
        n += 1
        if n == 3:
            break
