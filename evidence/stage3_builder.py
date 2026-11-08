"""
evidence/stage3_builder.py
Stage 3 evidence builder (v3 pool). No API calls. Rules fixed before any Stage 3 result exists.

For every row of results/eval_set_v3.jsonl, up to three conditions:
  genuine     a real event from the same raw file and host, with a different Event ID. Preference order:
                1. guid  shares a process GUID with the original (nearest in time)
                2. pid   shares a process ID with the original, within PID_WINDOW seconds (PIDs are reused)
                3. time  no link; nearest in time inside the original's 60 s cluster window
              Only Event IDs in INFORMATIVE are used as evidence (the feasibility rule of dev_checks/find_adjacent.py).
              Times are only compared within one clock family, because the raw files mix clocks.
              An event that is itself a pool event labelled with ANOTHER technique is never used: the next
              link in the same order is taken; if none is left the event has no genuine evidence.
              An event that logs the same action as the original a second time (Sysmon 1 / Security 4688 for
              one process creation, 4104 / 4103 for one command; same_action) is passed over the same way.
              Rule R-G1: genuine evidence for a T1059.001 or T1059.003 event is excluded when its content
              matches another of the ten candidate techniques (OTHER_TECHNIQUE_PATTERNS); the pair then has
              no genuine evidence.
  misleading  an event from the v3 pool events of the decoy technique (DECOY in build_eval_set.py), all of
              them eligible, not only eval-set events: cluster, then event, drawn with a fixed per-event seed.
              Rule R-M1: an event matching a candidate technique other than the decoy is dropped and the draw
              repeated. T1021.002 has no misleading condition.
              Both rules judge content, not the carrier (CARRIER_PRINCIPLE): cmd.exe / powershell.exe that
              only launch an action do not match T1059.003 / T1059.001 on their own.
  neutral     same re-ask prompt, no evidence.

Every evidence event is cleaned like the baseline input (extraction/clean_event.py), then host names,
timestamps and instance GUIDs are removed: fields that hold them are dropped and remaining values are masked
([HOST], [TIME], [GUID]); timestamps inside file names and paths are masked too, and well-known schema and
rights GUIDs (WELL_KNOWN_GUIDS) are kept. Process and thread IDs are replaced by [PID] / [TID]. Technique IDs
are masked ([REDACTED]). Genuine log content (channel names, image paths, script text) is kept; technique
names in it are flagged for audit. The leak check, R-G1 and R-M1 also scan decoded Base64. Per pair,
same_channel records whether evidence and original come from the same log channel (the Event ID never
matches in either condition).

Run from the project root:  python -m evidence.stage3_builder
Outputs: results/stage3_v3/evidence_pairs.jsonl, results/stage3_v3/summary.txt
"""
import base64
import binascii
import glob
import json
import ntpath
import os
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from data.techniques import CANDIDATE_TECHNIQUES
from extraction.clean_event import clean_event
from extraction.extract_pool import load_events

SEED = "stage3-v1"                          # same seed as build_eval_set.py
POOL = "results/pool_clean_v3.jsonl"
EVAL = "results/eval_set_v3.jsonl"
OUT_DIR = "results/stage3_v3"

PID_WINDOW = 120
CLUSTER_WINDOW = 60
INFORMATIVE = {1, 3, 8, 11, 19, 20, 21, 22, 23, 4103, 4104, 4624, 4648,
               4662, 4688, 4697, 4698, 5140, 5145, 7045}
TIME_KINDS = [("R", ["TimeCreated", "EventTime"]), ("U", ["UtcTime"]), ("L", ["@timestamp"])]
GUID_LINK_FIELDS = ["ProcessGuid", "ParentProcessGuid", "SourceProcessGuid", "TargetProcessGuid",
                    "SourceProcessGUID", "TargetProcessGUID"]
PID_LINK_FIELDS = ["ProcessId", "ProcessID", "ParentProcessId", "NewProcessId", "SourceProcessId",
                   "TargetProcessId", "CallerProcessId", "ClientProcessId"]
NO_LINK_PIDS = {0, 4}                       # Idle and System
HOST_FIELDS = {"Hostname", "host", "Computer", "ComputerName", "SourceHostname", "DestinationHostname",
               "Workstation", "WorkstationName"}
PID_FIELD_RE = re.compile(r"process_?id$", re.I)        # ProcessId, ParentProcessId, NewProcessId, ProcessID, ...
TID_FIELD_RE = re.compile(r"thread_?id$", re.I)

# Exclusion rule R-G1 (decided 2026-10-29; first applied by hand to two pairs on 2026-10-28 / 2026-10-29):
# genuine evidence for a T1059.001 event is excluded when its content matches another of the ten candidate
# techniques. Script content is never masked, so such a pair gets no genuine evidence instead. The content is
# every evidence field except Channel and SourceName, after stripping. Patterns as in
# scripts/scan_t1059_001_genuine.py (its technique categories; "tool load" is not a technique).
RULE_G1 = ("R-G1 (2026-10-29; extended to T1059.003 2026-10-30): genuine evidence for a T1059.001 or T1059.003 "
           "event is excluded when its content matches another of the ten candidate techniques")
# cmd.exe is a carrier like powershell.exe (CARRIER_PRINCIPLE), so its genuine evidence gets the same check
RULE_G1_TECHNIQUES = {"T1059.001", "T1059.003"}
OTHER_TECHNIQUE_PATTERNS = {
    "T1003.006": r"dc ?sync|DsGetNCChanges|drsuapi|Replicating Directory Changes|Get-ADReplAccount",
    "T1021.002": r"psexec|smbexec|svcctl|New-Service|CreateService|\bsc(?:\.exe)?\s+\\\\"
                 r"|\\\\[\w.-]+\\(?:admin|c|ipc)\$|ADMIN\$",
    "T1562.002": r"eventlog|wevtutil|Clear-EventLog|Limit-EventLog|MiniNt|auditpol",
    "T1546.003": r"__EventFilter|EventConsumer|FilterToConsumerBinding|Register-WmiEvent|Register-CimIndicationEvent",
    "T1547.001": r"CurrentVersion\\Run|\\Startup\\|Start Menu\\Programs\\Startup",
    "T1053.005": r"schtasks|ScheduledTask|Schedule\.Service|\\Tasks\\",
    "T1003.001": r"lsass|sekurlsa|MiniDump|comsvcs|logonpasswords",
    "T1055": r"VirtualAllocEx|WriteProcessMemory|CreateRemoteThread|ReflectivePEInjection|Invoke-\w*Inject\w*"
             r"|NtQueueApcThread",
}
# Content, not carrier (2026-10-30): R-G1 and R-M1 judge what the evidence does, not what carries it. A command
# interpreter (cmd.exe, powershell.exe) that only launches an action counts as that action, so it does not
# match T1059.003 or T1059.001 on its own. Hence no pattern for either: the former T1059.003 pattern
# "cmd(.exe) /c|/k" was removed, and no PowerShell pattern is added.
CARRIER_PRINCIPLE = ("R-G1/R-M1 judge content, not the carrier: a command interpreter that only launches an "
                     "action counts as that action and does not match T1059.003 or T1059.001 on its own")
OTHER_TECHNIQUE_RE = {t: re.compile(p, re.I) for t, p in OTHER_TECHNIQUE_PATTERNS.items()}
# the pairs R-G1 excludes on the v3 pool; the build stops if the rule excludes anything else
RULE_G1_EXPECTED = {
    "10e28166046adcc9": "T1003.006 (Meterpreter Invoke-DcSyncAll script)",
    "565fa9197f8b105b": "T1003.006 (Meterpreter Invoke-DcSyncAll script)",
    "10c9e2221a786d8e": "T1021.002 (PsExec64.exe to a remote host)",
    "df28c325f68125d2": "T1021.002 (PsExec64.exe to a remote host)",
    "2120d356ca88c930": "T1021.002 (PsExec64.exe to a remote host)",
    "d2ea07bf752be380": "T1021.002 (PsExec64.exe to a remote host)",
    "71baed215173a602": "T1562.002 (Set-Service EventLog -StartupType Disabled)",
}


RULE_M1 = ("R-M1 (2026-10-30): misleading evidence must not match a candidate technique other than its decoy "
           "(OTHER_TECHNIQUE_PATTERNS, Base64 decoded); the event is redrawn")

# Base64 (2026-10-30): every scan (leak check, R-G1, R-M1) also reads the decoded text of Base64 strings of 20+
# characters, as UTF-16LE (PowerShell -enc) or UTF-8, kept only if 95% printable; nested strings up to depth 3.
B64_RE = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{20,}={0,2}(?![A-Za-z0-9+/=])")
# Fixed in advance (2026-10-30): the Empire launcher's standard code that turns off script block logging is
# not a T1562.002 match; statements that touch the script block logging settings are removed before that check.
EMPIRE_SBL_RE = re.compile(r"[^;{}]*(?:ScriptB'?\+?'?lockLogging|ScriptBlockInvocationLogging|cachedGroupPolicySettings)[^;{}]*", re.I)


def decode_b64(text, depth=0):
    """Decoded texts of the Base64 strings in text (see B64_RE)."""
    out = []
    for m in B64_RE.findall(text):
        try:
            b = base64.b64decode(m + "=" * (-len(m) % 4), validate=True)
        except (binascii.Error, ValueError):
            continue
        for enc in ("utf-16-le", "utf-8"):
            try:
                d = b.decode(enc)
            except UnicodeDecodeError:
                continue
            if d and sum(c.isprintable() or c in "\r\n\t" for c in d) / len(d) >= 0.95:
                out.append(d)
                if depth < 2:
                    out += decode_b64(d, depth + 1)
                break
    return out


def other_technique_matches(fields, allowed):
    """[(technique, field, matched text)] for evidence content that matches a candidate technique not in
    `allowed`. Decoded Base64 is scanned too (field name suffixed ' (base64)')."""
    out = []
    for k, v in fields.items():
        if k in ("Channel", "SourceName"):
            continue
        for name, text in [(k, str(v))] + [(f"{k} (base64)", d) for d in decode_b64(str(v))]:
            for t, rx in OTHER_TECHNIQUE_RE.items():
                m = rx.search(EMPIRE_SBL_RE.sub(" ", text) if t == "T1562.002" else text)
                if t not in allowed and m:
                    out.append((t, name, m.group(0)))
    return out


def misleading_matches(fields, decoy):
    """R-M1 hits: matches of any candidate technique other than the decoy."""
    return other_technique_matches(fields, {decoy})


# Same action logged twice (2026-10-30): never genuine evidence; the next link is taken.
#   Sysmon 1 vs Security 4688: same host, same new-process PID and same image.
#   4104 vs 4103: same PowerShell process (ExecutionProcessID) and the command the 4103 records
#   (CommandInvocation) is written in the 4104 script block, by name, by a built-in alias, or without "Get-".
PS_ALIASES = {
    "set-location": ["cd", "chdir", "sl"], "get-childitem": ["gci", "ls", "dir"], "set-alias": ["sal"],
    "move-item": ["mv", "move", "mi"], "remove-item": ["rm", "del", "ri", "rd", "rmdir", "erase"],
    "copy-item": ["cp", "copy", "cpi"], "get-content": ["gc", "cat", "type"], "get-process": ["gps", "ps"],
    "where-object": ["where", "?"], "foreach-object": ["foreach", "%"], "write-output": ["echo", "write"],
    "invoke-expression": ["iex"], "invoke-webrequest": ["iwr", "curl", "wget"], "start-sleep": ["sleep"],
    "get-itemproperty": ["gp"], "set-itemproperty": ["sp"], "new-item": ["ni"], "start-process": ["saps", "start"],
    "stop-process": ["spps", "kill"], "get-location": ["gl", "pwd"], "select-object": ["select"],
}
INVOCATION_RE = re.compile(r"CommandInvocation\(([^)]+)\)")


def same_action(a, b):
    """True when a and b record the same action (see the rule above)."""
    ids = {a.get("EventID"), b.get("EventID")}
    if ids == {1, 4688}:
        s, w = (a, b) if a.get("EventID") == 1 else (b, a)
        return (host_of(s) == host_of(w) and to_pid(s.get("ProcessId")) is not None
                and to_pid(s.get("ProcessId")) == to_pid(w.get("NewProcessId"))
                and ntpath.basename(str(s.get("Image", ""))).lower() == ntpath.basename(str(w.get("NewProcessName", ""))).lower())
    if ids == {4103, 4104}:
        m, sb = (a, b) if a.get("EventID") == 4103 else (b, a)
        pid = to_pid(m.get("ExecutionProcessID"))
        if host_of(m) != host_of(sb) or pid is None or pid != to_pid(sb.get("ExecutionProcessID")):
            return False
        inv = INVOCATION_RE.search(str(m.get("Payload", "")))
        if not inv:
            return False
        cmd = inv.group(1).strip().lower()
        names = [cmd] + PS_ALIASES.get(cmd, []) + ([cmd[4:]] if cmd.startswith("get-") else [])
        text = str(sb.get("ScriptBlockText", "")).lower()
        return any(re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text) for n in names)
    return False

GUID_RE = re.compile(r"\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?")
# Well-known schema and rights GUIDs are the same on every domain and are kept (2026-10-30); only instance
# GUIDs (objects, runspaces, activities, script blocks) are masked.
WELL_KNOWN_GUIDS = {
    "19195a5b-6da0-11d0-afd3-00c04fd930c9",    # domainDNS object class
    "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2",    # DS-Replication-Get-Changes
    "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2",    # DS-Replication-Get-Changes-All
    "89e95b76-444d-4c62-991a-0facbeda640c",    # DS-Replication-Get-Changes-In-Filtered-Set
    "1131f6ab-9c07-11d1-f79f-00c04fc2dcd2",    # DS-Replication-Synchronize
    "1131f6ac-9c07-11d1-f79f-00c04fc2dcd2",    # DS-Replication-Manage-Topology
}
TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
                     r"|\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}(?::\d{2})?(?: ?[AP]M)?")
# timestamps inside file names and paths, e.g. 20200904-030800 (2026-10-30)
PATH_TIME_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}-?[01]\d-?[0-3]\d[-_T]?[0-2]\d[0-5]\d[0-5]\d(?!\d)")
# Any non-alphanumeric character (underscore and dot included) is a boundary, e.g. ntds_T1003 (2026-10-30).
TECH_ID_RE = re.compile(r"(?<![A-Za-z0-9])T1\d{3}(?:\.\d{3})?(?![A-Za-z0-9])", re.I)
TECH_NAMES = [t["name"] for t in CANDIDATE_TECHNIQUES]

DECOY = {
    "T1059.001": "T1059.003", "T1059.003": "T1059.001",
    "T1003.001": "T1003.006", "T1003.006": "T1003.001",
    "T1055": "T1562.002", "T1562.002": "T1055",
    "T1053.005": "T1547.001", "T1547.001": "T1546.003", "T1546.003": "T1053.005",
    "T1021.002": None,
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def key_of(e):
    return json.dumps(e, sort_keys=True)


# ---------------- time and links ----------------
def parse_time(e):
    """(clock family, epoch seconds); same field priority as dev_checks/find_adjacent.py."""
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


def to_pid(v):
    try:
        s = str(v).strip()
        n = int(s, 16) if s.lower().startswith("0x") else int(s)
    except (TypeError, ValueError):
        return None
    return None if n in NO_LINK_PIDS else n


def link_keys(e):
    guids = {str(e[f]).strip("{}").lower() for f in GUID_LINK_FIELDS if e.get(f)}
    pids = {p for p in (to_pid(e.get(f)) for f in PID_LINK_FIELDS) if p is not None}
    if "powershell" in str(e.get("Channel", "")).lower():
        p = to_pid(e.get("ExecutionProcessID"))       # for PowerShell events this is the powershell.exe PID
        if p is not None:
            pids.add(p)
    return guids, pids


def host_of(e):
    return str(e.get("Hostname") or e.get("Computer") or "").lower()


def find_genuine(raw, i0, blocked=frozenset()):
    """Index, link type and |dt| of the genuine evidence for raw[i0], or (None, 'none', None), plus the
    indices in `blocked` (pool events of another technique) that would have ranked higher and the indices
    passed over because they log the same action as raw[i0] (same_action)."""
    e0 = raw[i0]
    kind0, t0 = parse_time(e0)
    if t0 is None:
        return None, "none", None, [], []
    g0, p0 = link_keys(e0)
    h0, eid0 = host_of(e0), e0.get("EventID")
    best, skipped, dup = None, [], []
    for j, e in enumerate(raw):
        eid = e.get("EventID")
        if j == i0 or eid == eid0 or eid not in INFORMATIVE or host_of(e) != h0:
            continue
        kind, t = parse_time(e)
        if t is None or kind != kind0:
            continue
        dt = abs(t - t0)
        g, p = link_keys(e)
        if g0 & g:
            rank = (0, dt, j)
        elif p0 & p and dt <= PID_WINDOW:
            rank = (1, dt, j)
        elif t // CLUSTER_WINDOW == t0 // CLUSTER_WINDOW:
            rank = (2, dt, j)
        else:
            continue
        if j in blocked:
            skipped.append(rank)
            continue
        if same_action(e0, e):
            dup.append(rank)
            continue
        if best is None or rank < best:
            best = rank
    skipped = [s[2] for s in sorted(skipped) if best is None or s < best]
    dup = [s[2] for s in sorted(dup) if best is None or s < best]
    if best is None:
        return None, "none", None, skipped, dup
    return best[2], ("guid", "pid", "time")[best[0]], best[1], skipped, dup


# ---------------- stripping ----------------
def host_names(raw):
    names = set()
    for e in raw:
        for f in HOST_FIELDS:
            v = e.get(f)
            if isinstance(v, str) and v.strip() not in ("", "-") and not re.fullmatch(r"[\d.:]+", v.strip()):
                names.add(v.strip())
                names.add(v.strip().split(".")[0])
    return sorted((n for n in names if len(n) >= 3), key=len, reverse=True)   # FQDN before short name


def instance_guids(text):
    return [g for g in GUID_RE.findall(text) if g.strip("{}").lower() not in WELL_KNOWN_GUIDS]


def mask_guids(text):
    return GUID_RE.sub(lambda m: m.group(0) if m.group(0).strip("{}").lower() in WELL_KNOWN_GUIDS else "[GUID]", text)


def strip_event(e, hosts):
    """Clean like the baseline input, then remove host names, timestamps and GUIDs. Returns (fields, removed)."""
    removed = []
    out = {}
    host_re = re.compile(r"(?<![\w-])(?:" + "|".join(map(re.escape, hosts)) + r")(?![\w-])", re.I) if hosts else None
    for k, v in clean_event(e).items():
        if k in HOST_FIELDS or "guid" in k.lower():
            removed.append(k)
            continue
        if PID_FIELD_RE.search(k) or TID_FIELD_RE.search(k):
            out[k] = "[PID]" if PID_FIELD_RE.search(k) else "[TID]"
            removed.append(f"{k} (masked)")
            continue
        if isinstance(v, str) and re.search(r"time|stamp", k, re.I) and TIME_RE.fullmatch(v.strip()):
            removed.append(k)
            continue
        if isinstance(v, str):
            v2 = mask_guids(v)
            v2 = TIME_RE.sub("[TIME]", v2)
            v2 = PATH_TIME_RE.sub("[TIME]", v2)
            if host_re:
                v2 = host_re.sub("[HOST]", v2)
            v2 = TECH_ID_RE.sub("[REDACTED]", v2)     # neutral placeholder (2026-11-01; was [TECHNIQUE_ID])
            if v2 != v:
                removed.append(f"{k} (masked)")
            v = v2
        out[k] = v
    return out, removed


def render(fields):
    return "\n".join(f"{k}: {v}" for k, v in fields.items())


def leaks(text, hosts, pids=()):
    """Anything that should not be in evidence text after stripping (empty list = clean). `pids` are the
    original event's process IDs; one of them left in the evidence would link the two visibly. Decoded Base64
    is checked too; a finding there is prefixed 'base64 '."""
    found = []
    for prefix, t in [("", text)] + [("base64 ", d) for d in decode_b64(text)]:
        for n in pids:
            if re.search(rf"(?<![\w.]){n}(?![\w.])|(?<!\w)0x{n:x}(?!\w)", t, re.I):
                found.append(f"{prefix}pid:{n}")
        if instance_guids(t):
            found.append(f"{prefix}guid")
        if TIME_RE.search(t) or PATH_TIME_RE.search(t):
            found.append(f"{prefix}timestamp")
        if TECH_ID_RE.search(t):
            found.append(f"{prefix}technique_id")
        low = t.lower()
        found += [f"{prefix}host:{h}" for h in hosts if re.search(r"(?<![\w-])" + re.escape(h.lower()) + r"(?![\w-])", low)]
    return list(dict.fromkeys(found))


def technique_name_hits(text):
    return [n for n in TECH_NAMES if n.lower() in text.lower()]


# ---------------- build ----------------
def build():
    pool = load(POOL)
    by_uid = {p["event_uid"]: p for p in pool}
    pool_label = {key_of(p["event"]): p["technique_label"] for p in pool}
    eval_rows = load(EVAL)
    clusters_by_tech = defaultdict(lambda: defaultdict(list))
    for p in pool:
        clusters_by_tech[p["technique_label"]][p["cluster_id"]].append(p)

    raws, hosts_by_file, labels_by_file = {}, {}, {}
    pool_by_file = defaultdict(list)
    for p in pool:
        pool_by_file[p["source_file"]].append(p)

    def raw_of(fname):
        if fname not in raws:
            paths = glob.glob(f"data/raw/*/{fname}")
            assert len(paths) == 1, f"raw file not found or ambiguous: {fname}"
            raws[fname] = load_events(paths[0])
            hosts_by_file[fname] = host_names(raws[fname])
            eids = {p["event"].get("EventID") for p in pool_by_file[fname]}
            labels_by_file[fname] = {j: pool_label[key_of(e)] for j, e in enumerate(raws[fname])
                                     if e.get("EventID") in eids and key_of(e) in pool_label}
        return raws[fname]

    pairs = []
    for r in eval_rows:
        p = by_uid[r["event_uid"]]
        orig = clean_event(p["event"])
        common = {"event_uid": r["event_uid"], "cluster_id": r["cluster_id"], "technique_label": r["technique_label"],
                  "decoy_technique": r["decoy_technique"], "baseline_correct": r["baseline_correct"],
                  "original_event_id": p["event"].get("EventID"), "original_fields": orig}

        # genuine
        raw = raw_of(p["source_file"])
        idx = {key_of(e): i for i, e in enumerate(raw) if e.get("EventID") == p["event"].get("EventID")}
        i0 = idx.get(key_of(p["event"]))
        assert i0 is not None, f"original not found in raw file: {r['event_uid']}"
        labels = labels_by_file[p["source_file"]]
        blocked = frozenset(k for k, lab in labels.items() if lab != r["technique_label"])
        j, link, dt, skipped, dup = find_genuine(raw, i0, blocked)
        row = {**common, "pair_id": f"{r['event_uid']}|genuine", "condition": "genuine", "link_type": link,
               "dt_seconds": None if dt is None else round(dt, 3),
               "skipped_other_technique": [{"raw_index": k, "pool_label": labels[k]} for k in skipped],
               "skipped_same_action": [{"raw_index": k, "event_id": raw[k].get("EventID")} for k in dup]}
        if j is not None:
            ev = raw[j]
            fields, removed = strip_event(ev, hosts_by_file[p["source_file"]])
            hits = other_technique_matches(fields, {r["technique_label"]})
            if r["technique_label"] in RULE_G1_TECHNIQUES and hits:
                row.update(link_type="excluded", dt_seconds=None, excluded_reason=RULE_G1,
                           excluded_matches=[{"technique": t, "field": k, "matched": m} for t, k, m in hits])
            else:
                row.update(evidence_source={"source_file": p["source_file"], "raw_index": j,
                                            "pool_label": pool_label.get(key_of(ev))},
                           evidence_event_id=ev.get("EventID"), evidence_fields=fields, stripped=removed)
        pairs.append(row)

        # misleading
        d = r["decoy_technique"]
        if d:
            # R-M1: draw cluster then event; an event matching another technique is dropped and the draw
            # repeated with the same generator, so pairs whose first draw is clean are unchanged
            rng = random.Random(f"{SEED}|misleading|{r['event_uid']}")
            left = {c: sorted(evs, key=lambda x: x["event_uid"]) for c, evs in clusters_by_tech[d].items()}
            rejected, chosen = [], None
            while left:
                cid = rng.choice(sorted(left))
                q = rng.choice(left[cid])
                raw_of(q["source_file"])
                fields, removed = strip_event(q["event"], hosts_by_file[q["source_file"]])
                hits = misleading_matches(fields, d)
                if not hits:
                    chosen = q
                    break
                rejected.append({"event_uid": q["event_uid"], "matches": [{"technique": t, "field": k, "matched": m}
                                                                          for t, k, m in hits]})
                left[cid] = [x for x in left[cid] if x is not q]
                if not left[cid]:
                    del left[cid]
            row = {**common, "pair_id": f"{r['event_uid']}|misleading", "condition": "misleading",
                   "link_type": None, "dt_seconds": None, "rejected_rule_m1": rejected,
                   "decoy_pool_events": sum(len(v) for v in clusters_by_tech[d].values())}
            if chosen is None:
                row.update(link_type="excluded", evidence_event_id=None, evidence_fields=None, excluded_reason=RULE_M1)
            else:
                row.update(evidence_source={"source_file": q["source_file"], "event_uid": q["event_uid"],
                                            "cluster_id": cid, "pool_label": d},
                           evidence_event_id=q["event"].get("EventID"), evidence_fields=fields, stripped=removed)
            pairs.append(row)

        # neutral
        pairs.append({**common, "pair_id": f"{r['event_uid']}|neutral", "condition": "neutral",
                      "link_type": None, "dt_seconds": None, "evidence_event_id": None, "evidence_fields": None})

    all_hosts = sorted({h for hs in hosts_by_file.values() for h in hs}, key=len, reverse=True)
    for row in pairs:
        f = row.get("evidence_fields")
        row["evidence_text"] = render(f) if f else None
        row["same_channel"] = None if f is None else f.get("Channel") == row["original_fields"].get("Channel")
        row["leaks"] = leaks(row["evidence_text"], all_hosts, link_keys(by_uid[row["event_uid"]]["event"])[1]) if f else []
        row["technique_name_hits"] = technique_name_hits(row["evidence_text"]) if f else []
    return pairs


def main():
    pairs = build()
    excluded = {r["event_uid"] for r in pairs if r["link_type"] == "excluded" and r["condition"] == "genuine"}
    assert excluded == set(RULE_G1_EXPECTED), (f"R-G1 excludes {sorted(excluded)}, expected "
                                               f"{sorted(RULE_G1_EXPECTED)}; review before using the pairs")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/evidence_pairs.jsonl", "w", encoding="utf-8") as fh:
        for row in pairs:
            fh.write(json.dumps(row) + "\n")
    summary = summarize(pairs)
    with open(f"{OUT_DIR}/summary.txt", "w", encoding="utf-8") as fh:
        fh.write(summary)
    print(summary)


def summarize(pairs):
    lines = []
    cond = Counter(r["condition"] for r in pairs)
    lines.append(f"pairs: {len(pairs)}  " + "  ".join(f"{c}: {n}" for c, n in sorted(cond.items())))
    lines.append(f"seed: {SEED}   PID window: {PID_WINDOW} s   cluster window: {CLUSTER_WINDOW} s\n")
    lines.append("genuine evidence by technique (link type)")
    lines.append(f"{'technique':<11}{'events':>7}{'guid':>6}{'pid':>5}{'time':>6}{'none':>6}{'excluded':>10}"
                 f"{'same channel':>14}{'same-technique pool event':>27}{'other-technique skipped':>25}")
    by = defaultdict(list)
    for r in pairs:
        if r["condition"] == "genuine":
            by[r["technique_label"]].append(r)
    tot = Counter()
    for t in sorted(by):
        c = Counter(r["link_type"] for r in by[t])
        tot.update(c)
        inpool = sum(1 for r in by[t] if r.get("evidence_source", {}).get("pool_label"))
        lines.append(f"{t:<11}{len(by[t]):>7}{c['guid']:>6}{c['pid']:>5}{c['time']:>6}{c['none']:>6}{c['excluded']:>10}"
                     f"{sum(bool(r['same_channel']) for r in by[t]):>14}{inpool:>27}"
                     f"{sum(1 for r in by[t] if r['skipped_other_technique']):>25}")
    n = sum(tot.values())
    lines.append(f"{'ALL':<11}{n:>7}{tot['guid']:>6}{tot['pid']:>5}{tot['time']:>6}{tot['none']:>6}{tot['excluded']:>10}")
    lines.append("same-technique pool event = the evidence is itself a v3 pool event with the original's label (allowed)")
    lines.append("other-technique skipped = a higher-ranked link was a pool event of another technique and was passed over\n")

    lines.append("misleading evidence by technique")
    lines.append(f"{'technique':<11}{'decoy':<11}{'pairs':>6}{'decoy pool events':>19}{'distinct used':>15}{'same channel':>14}"
                 f"{'redrawn (R-M1)':>16}{'excluded':>10}")
    mis = defaultdict(list)
    for r in pairs:
        if r["condition"] == "misleading":
            mis[r["technique_label"]].append(r)
    for t in sorted(mis):
        rs = mis[t]
        lines.append(f"{t:<11}{rs[0]['decoy_technique']:<11}{len(rs):>6}{rs[0]['decoy_pool_events']:>19}"
                     f"{len({r['evidence_source']['event_uid'] for r in rs if r.get('evidence_source')}):>15}"
                     f"{sum(bool(r['same_channel']) for r in rs):>14}"
                     f"{sum(1 for r in rs if r['rejected_rule_m1']):>16}{sum(1 for r in rs if r['link_type'] == 'excluded'):>10}")

    ev = [r for r in pairs if r.get("evidence_text")]
    lk = Counter(x.split(":")[0] for r in ev for x in r["leaks"])
    lines.append(f"\nleak check on {len(ev)} evidence texts (host / timestamp / GUID / technique ID left after stripping): "
                 + (", ".join(f"{k}: {v}" for k, v in lk.items()) if lk else "none"))
    nh = Counter(n for r in ev for n in r["technique_name_hits"])
    lines.append("technique names appearing in evidence text (flagged, not masked): "
                 + (", ".join(f"'{k}': {v}" for k, v in nh.most_common()) if nh else "none"))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
