"""
scripts/t1021_002_local_remote.py
Read-only (2026-11-08, after the Stage 3 results): for every T1021.002 event in the v3 pool (all are System 7045,
one per cluster), was the service created locally or remotely? Prints, from the raw file:
  - the installing host and the 4697 for the same service (subject, logon ID), and the 4624 that opened that
    logon session (logon type, source IP, process)
  - remote-creation signs on the installing host from 120 s before to 5 s after the 7045: 4624 type 3/10 from
    another address, 4648 explicit credentials, 5140/5145 share / named-pipe access (IPC$, ADMIN$, svcctl),
    inbound Sysmon 3 on 135/139/445, Sysmon 11 writes of the service binary by System (PID 4)
  - the creating process: on the installing host, Sysmon 1 / 4688 / 4103 / 4104 that name the service or its
    binary; on any other host, processes whose command line names the installing host, the service or its binary,
    with their Sysmon 1 parent chain
No API calls.

Run from the project root:  python scripts/t1021_002_local_remote.py
"""
import glob
import json
import ntpath
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, ".")
from extraction.extract_pool import load_events

BEFORE, AFTER = 120, 5
LOOPBACK = {"::1", "127.0.0.1", "-", "", "None", "0:0:0:0:0:0:0:1"}


def t_of(e):
    for f in ("EventTime", "TimeCreated"):
        v = e.get(f)
        if v:
            try:
                return datetime.strptime(str(v).replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S").timestamp()
            except ValueError:
                pass
    return None


def host(e):
    return str(e.get("Hostname") or e.get("Computer") or "").lower()


def short(s):
    return str(s)[:220].replace("\n", " ").replace("\r", " ")


pool = [json.loads(l) for l in open("results/pool_clean_v3.jsonl", encoding="utf-8")]
targets = sorted((p for p in pool if p["technique_label"] == "T1021.002"), key=lambda p: (p["source_file"], p["event"].get("EventTime")))
raws = {}
for p in targets:
    e0 = p["event"]
    f = p["source_file"]
    if f not in raws:
        raws[f] = load_events(glob.glob(f"data/raw/*/{f}")[0])
    raw = raws[f]
    H, T = host(e0), t_of(e0)
    svc_name, img = str(e0.get("ServiceName")), str(e0.get("ImagePath"))
    binary = ntpath.basename(img.split()[0]).lower() if img else ""
    hosts = Counter(host(x) for x in raw)
    my_ips = {str(x.get("SourceIp")) for x in raw if x.get("EventID") == 3 and host(x) == H
              and str(x.get("Initiated")).lower() == "true"} - LOOPBACK
    print("=" * 110)
    print(f"{p['event_uid']}  {f}\n  host {H}  time {e0.get('EventTime')}  service {svc_name!r}  image {short(img)[:120]}")
    print(f"  hosts in file: {dict(hosts)}  installing host's own IPs: {sorted(my_ips)}")
    win = [(i, x) for i, x in enumerate(raw) if (tx := t_of(x)) is not None and T - BEFORE <= tx <= T + AFTER]

    # 4697 for this service, and the logon session behind it
    s4697 = [x for i, x in win if x.get("EventID") == 4697 and host(x) == H]
    for x in s4697:
        lid = str(x.get("SubjectLogonId"))
        print(f"  4697: service {x.get('ServiceName')}  subject {x.get('SubjectDomainName')}\\{x.get('SubjectUserName')}  logon {lid}")
        logons = [y for y in raw if y.get("EventID") == 4624 and host(y) == H and str(y.get("TargetLogonId")) == lid]
        for y in logons:
            print(f"    4624 opening {lid}: {y.get('EventTime')} type {y.get('LogonType')} user {y.get('TargetUserName')} "
                  f"from {y.get('IpAddress')} ws {y.get('WorkstationName')} process {y.get('ProcessName')} auth {y.get('AuthenticationPackageName')}")
        if not logons:
            print(f"    no 4624 for {lid} in the file")
    if not s4697:
        print("  4697: none in the window")

    print("  remote-creation signs on the installing host:")
    n = 0
    for i, x in win:
        if host(x) != H:
            continue
        eid = x.get("EventID")
        line = None
        if eid == 4624 and str(x.get("LogonType")) in ("3", "10") and str(x.get("IpAddress")) not in LOOPBACK | my_ips:
            line = (f"4624 type {x.get('LogonType')} {x.get('TargetDomainName')}\\{x.get('TargetUserName')} from {x.get('IpAddress')} "
                    f"logon {x.get('TargetLogonId')} auth {x.get('AuthenticationPackageName')}")
        elif eid == 4648:
            line = f"4648 {x.get('SubjectUserName')} -> {x.get('TargetUserName')} on {x.get('TargetServerName')} proc {x.get('ProcessName')}"
        elif eid in (5140, 5145):
            line = (f"{eid} share {x.get('ShareName')} target {x.get('RelativeTargetName')} from {x.get('IpAddress')} "
                    f"user {x.get('SubjectUserName')} logon {x.get('SubjectLogonId')}")
        elif eid == 3 and str(x.get("Initiated")).lower() == "false" and str(x.get("DestinationPort")) in ("135", "139", "445"):
            line = f"sysmon3 inbound {x.get('SourceIp')}:{x.get('SourcePort')} -> {x.get('DestinationIp')}:{x.get('DestinationPort')} {x.get('Image')}"
        elif eid == 11 and binary and ntpath.basename(str(x.get("TargetFilename"))).lower() == binary:
            line = f"sysmon11 {x.get('Image')} (pid {x.get('ProcessId')}) wrote {x.get('TargetFilename')}"
        if line:
            n += 1
            if n <= 25:
                print(f"    {i} {x.get('EventTime')} {line}")
    if n > 25:
        print(f"    ... {n - 25} more")
    if n == 0:
        print("    none")

    keys = [k for k in {svc_name.lower(), binary} if k and k not in ("none", "cmd.exe", "%comspec%")]
    print(f"  creating process (command lines naming {keys} or the installing host):")
    sysmon1 = {str(x.get("ProcessGuid")).lower(): x for x in raw if x.get("EventID") == 1}
    hshort = H.split(".")[0]
    for i, x in win:
        eid = x.get("EventID")
        text = " ".join(str(x.get(k, "")) for k in ("CommandLine", "Payload", "ScriptBlockText", "NewProcessName")).lower()
        if eid not in (1, 4688, 4103, 4104) or not text.strip():
            continue
        if any(k in text for k in keys) or (host(x) != H and re.search(r"(?<![\w-])" + re.escape(hshort) + r"(?![\w-])", text)):
            where = "same host" if host(x) == H else f"OTHER host {host(x)}"
            print(f"    {i} {eid} {x.get('EventTime')} [{where}] {x.get('Image') or x.get('NewProcessName') or ''}  {short(text)[:200]}")
            cur, d = sysmon1.get(str(x.get("ParentProcessGuid")).lower()) if eid == 1 else None, 0
            while cur is not None and d < 6:
                print(f"        parent: {cur.get('Image')}  {short(cur.get('CommandLine'))[:140]}  user {cur.get('User')}")
                cur, d = sysmon1.get(str(cur.get("ParentProcessGuid")).lower()), d + 1
