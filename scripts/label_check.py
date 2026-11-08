"""
scripts/label_check.py
Read-only label check (2026-10-30): writes results/stage3_v3/label_check.md. No API calls.
The 'Notes on the chains' section of that file was added by hand from scripts/label_check_ps.py; rerunning
this script drops it.

Run from the project root:  python scripts/label_check.py
"""
import glob
import json
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
from extraction.extract_pool import load_events
from evidence.stage3_builder import parse_time, to_pid, host_of

POOL = "results/pool_clean_v3.jsonl"
OUT = "results/stage3_v3/label_check.md"
TECHS = ["T1547.001", "T1059.003", "T1003.006"]
DEFENDER_RE = re.compile(r"\\WindowsAzure\\|MsMpEng\.exe|MpCmdRun\.exe|NisSrv\.exe|MsSense\.exe|SenseIR\.exe|"
                         r"SenseCncProxy\.exe|MpDefenderCoreService\.exe|\\Windows Defender|"
                         r"Windows Defender Advanced Threat Protection", re.I)

pool = [json.loads(l) for l in open(POOL, encoding="utf-8") if l.strip()]
raws = {}


def raw_of(fname):
    if fname not in raws:
        paths = glob.glob(f"data/raw/*/{fname}")
        assert len(paths) == 1, fname
        raws[fname] = load_events(paths[0])
    return raws[fname]


def creation_index(raw):
    """Process-creation events: Sysmon 1 by ProcessGuid, Security 4688 by (host, NewProcessId)."""
    by_guid, by_pid = {}, defaultdict(list)
    for e in raw:
        if e.get("EventID") == 1 and "sysmon" in str(e.get("Channel", "")).lower() and e.get("ProcessGuid"):
            by_guid[str(e["ProcessGuid"]).strip("{}").lower()] = e
        elif e.get("EventID") == 4688 and to_pid(e.get("NewProcessId")) is not None:
            by_pid[(host_of(e), to_pid(e["NewProcessId"]))].append(e)
    return by_guid, by_pid


def find_creation(idx, host, guid, pid, t):
    by_guid, by_pid = idx
    if guid and guid in by_guid:
        return by_guid[guid], "Sysmon 1"
    if pid is not None:
        cands = [e for e in by_pid.get((host, pid), []) if parse_time(e)[1] is not None
                 and (t is None or parse_time(e)[1] <= t + 1)]
        if cands:
            return max(cands, key=lambda e: parse_time(e)[1]), "4688"
    return None, None


def chain(e, idx):
    """List of (image, command line, source) from the event's own process upward, as far as the raw file shows."""
    host, t = host_of(e), parse_time(e)[1]
    own_img = e.get("Image") or e.get("NewProcessName") or e.get("SourceImage")
    guid = str(e.get("ProcessGuid") or e.get("SourceProcessGuid") or "").strip("{}").lower() or None
    pid = to_pid(e.get("ProcessId") or e.get("NewProcessId") or e.get("SourceProcessId"))
    if e.get("EventID") == 4662:
        return []
    out, seen = [], set()
    if e.get("EventID") == 1 or e.get("EventID") == 4688:
        out.append((own_img, e.get("CommandLine"), "this event"))
        pimg = e.get("ParentImage") or e.get("ParentProcessName")
        guid = str(e.get("ParentProcessGuid") or "").strip("{}").lower() or None
        pid = to_pid(e.get("ParentProcessId") or (e.get("ProcessId") if e.get("EventID") == 4688 else None))
        pending = (pimg, e.get("ParentCommandLine"), "parent field in this event")
    else:
        pending = (own_img, None, "Image field in this event")
    for _ in range(12):
        c, src = find_creation(idx, host, guid, pid, t)
        if c is None or id(c) in seen:
            if pending[0]:
                out.append(pending)
            break
        seen.add(id(c))
        out.append((c.get("Image") or c.get("NewProcessName"), c.get("CommandLine"), f"{src} at {c.get('UtcTime') or c.get('EventTime') or c.get('TimeCreated')}"))
        pimg = c.get("ParentImage") or c.get("ParentProcessName")
        guid = str(c.get("ParentProcessGuid") or "").strip("{}").lower() or None
        pid = to_pid(c.get("ParentProcessId") if src == "Sysmon 1" else c.get("ProcessId"))
        pending = (pimg, c.get("ParentCommandLine"), "parent field of the creation event above")
        t = parse_time(c)[1]
    return out


idx_cache = {}


def chain_of(p):
    f = p["source_file"]
    if f not in idx_cache:
        idx_cache[f] = creation_index(raw_of(f))
    return chain(p["event"], idx_cache[f])


def cell(v, n=400):
    s = "" if v is None else str(v).replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    return s if len(s) <= n else s[:n] + f" ... [+{len(s) - n} chars]"


lines = ["# Label check: T1547.001, T1059.003, T1003.006 (v3 pool)\n",
         "Read only; nothing in the pool, builder or tables was changed. Parent chains were rebuilt from the raw "
         "file by following process-creation events upward: Sysmon 1 by `ParentProcessGuid`, else Security 4688 "
         "by host and PID (latest creation at or before the event). A chain stops where the raw file has no "
         "creation event for the next process; the last entry then comes from a parent field. The first entry "
         "is the event's own process.\n"]

for tech in TECHS:
    rows = sorted((p for p in pool if p["technique_label"] == tech), key=lambda p: (p["cluster_id"], p["event_uid"]))
    lines.append(f"\n## {tech} ({len(rows)} events, {len({p['cluster_id'] for p in rows})} clusters)\n")
    for p in rows:
        e = p["event"]
        lines.append(f"\n### `{p['event_uid']}`\n")
        lines.append(f"- cluster: `{p['cluster_id']}`")
        lines.append(f"- Event ID {e.get('EventID')}, channel `{e.get('Channel')}`, time `{e.get('UtcTime') or e.get('EventTime')}`")
        if e.get("EventID") == 4662:
            lines.append(f"- SubjectUserName: `{e.get('SubjectUserName')}` (domain `{e.get('SubjectDomainName')}`)")
            lines.append(f"- ObjectName: `{e.get('ObjectName')}`; ObjectType: `{e.get('ObjectType')}`; AccessMask: `{e.get('AccessMask')}`")
            lines.append(f"- Properties: `{cell(e.get('Properties'))}`")
            lines.append("- parent chain: none (4662 carries no process fields)")
            continue
        lines.append(f"- Image: `{e.get('Image')}`; User: `{e.get('User') or (str(e.get('Domain')) + chr(92) + str(e.get('AccountName')))}`")
        if e.get("TargetObject"):
            lines.append(f"- TargetObject: `{e.get('TargetObject')}`; Details: `{cell(e.get('Details'))}`")
        if e.get("CommandLine"):
            lines.append(f"- CommandLine: `{cell(e.get('CommandLine'))}`")
        lines.append("- parent chain (own process first):\n")
        lines.append("  | level | image | command line | from |")
        lines.append("  |---|---|---|---|")
        for k, (img, cmd, src) in enumerate(chain_of(p)):
            lines.append(f"  | {k} | `{cell(img)}` | {('`' + cell(cmd, 300) + '`') if cmd else ''} | {src} |")

# whole-pool counts
counts = defaultdict(Counter)
for p in pool:
    c = chain_of(p)
    in_chain = any(DEFENDER_RE.search(str(img or "")) for img, _, _ in c)
    anywhere = bool(DEFENDER_RE.search(json.dumps(p["event"])))
    counts[p["technique_label"]]["events"] += 1
    counts[p["technique_label"]]["chain"] += in_chain
    counts[p["technique_label"]]["anywhere"] += anywhere
    if p["event"].get("EventID") == 4662:
        counts[p["technique_label"]]["4662"] += 1
        counts[p["technique_label"]]["4662$"] += str(p["event"].get("SubjectUserName", "")).endswith("$")

lines.append("\n## Whole v3 pool\n")
lines.append("Defender pattern: `\\WindowsAzure\\`, `MsMpEng.exe`, `MpCmdRun.exe`, `NisSrv.exe`, `MsSense.exe`, "
             "`SenseIR.exe`, `SenseCncProxy.exe`, `MpDefenderCoreService.exe`, `\\Windows Defender`, "
             "`Windows Defender Advanced Threat Protection` (case-insensitive). \"In process or parent chain\" checks "
             "the image of every chain entry, as rebuilt above. \"Anywhere in the event\" is a looser extra column: "
             "any field of the pool event itself (for example TargetImage or a command line).\n")
lines.append("| technique | events | process or parent chain matches | anywhere in the event | 4662 events | 4662 with SubjectUserName ending in $ |")
lines.append("|---|---|---|---|---|---|")
tot = Counter()
for t in sorted(counts):
    c = counts[t]
    tot.update(c)
    lines.append(f"| {t} | {c['events']} | {c['chain']} | {c['anywhere']} | {c['4662']} | {c['4662$']} |")
lines.append(f"| **all** | {tot['events']} | {tot['chain']} | {tot['anywhere']} | {tot['4662']} | {tot['4662$']} |")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines[-(len(counts) + 3):]))
