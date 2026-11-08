"""
scripts/scan_t1059_001_genuine.py
Lists every T1059.001 genuine pair whose evidence loads a tool or does something that matches another
candidate technique. Lists only; nothing is excluded. No API calls.

Run from the project root (after python -m evidence.stage3_builder):  python scripts/scan_t1059_001_genuine.py
Output: results/stage3_v3/t1059_001_genuine_matches.md
"""
import json
import re

PAIRS = "results/stage3_v3/evidence_pairs.jsonl"
OUT = "results/stage3_v3/t1059_001_genuine_matches.md"
CONTEXT = 70

# categories asked for, then extra ones (marked) that also match another candidate technique
PATTERNS = [
    ("T1003.006 DCSync", r"dc ?sync|DsGetNCChanges|drsuapi|Replicating Directory Changes|Get-ADReplAccount"),
    ("T1021.002 PsExec / remote service", r"psexec|smbexec|svcctl|New-Service|CreateService|\bsc(?:\.exe)?\s+\\\\"
                                          r"|\\\\[\w.-]+\\(?:admin|c|ipc)\$|ADMIN\$"),
    ("T1562.002 Event Log service", r"eventlog|wevtutil|Clear-EventLog|Limit-EventLog|MiniNt|auditpol"),
    ("T1546.003 WMI subscription", r"__EventFilter|EventConsumer|FilterToConsumerBinding|Register-WmiEvent"
                                   r"|Register-CimIndicationEvent"),
    ("T1547.001 Run keys / Startup", r"CurrentVersion\\Run|\\Startup\\|Start Menu\\Programs\\Startup"),
    ("T1053.005 scheduled task", r"schtasks|ScheduledTask|Schedule\.Service|\\Tasks\\"),
    ("(extra) T1003.001 LSASS", r"lsass|sekurlsa|MiniDump|comsvcs|logonpasswords"),
    ("(extra) T1055 injection", r"VirtualAllocEx|WriteProcessMemory|CreateRemoteThread|ReflectivePEInjection"
                                r"|Invoke-\w*Inject\w*|NtQueueApcThread"),
    ("(extra) T1059.003 cmd.exe", r"\bcmd(?:\.exe)?\s+/[ck]\b"),
    ("(extra) tool load", r"mimikatz|\bkiwi\b|meterpreter|powersploit|powerview|Invoke-Mimikatz|DownloadString"
                          r"|DownloadFile|Net\.WebClient|Import-Module[ \t]+[^\s-]\S*|\[Reflection\.Assembly\]::Load"),
]
COMPILED = [(name, re.compile(p, re.I)) for name, p in PATTERNS]


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def snippet(text, m):
    a, b = max(0, m.start() - CONTEXT), min(len(text), m.end() + CONTEXT)
    s = text[a:b].replace("\r", " ").replace("\n", " ").replace("|", "\\|").replace("`", "'")
    return ("..." if a else "") + s + ("..." if b < len(text) else "")


def main():
    rows = [r for r in load(PAIRS) if r["technique_label"] == "T1059.001" and r["condition"] == "genuine"]
    hits = []
    for r in rows:
        found = []
        for field, value in (r.get("evidence_fields") or {}).items():
            if field in ("Channel", "SourceName"):
                continue
            text = str(value)
            for name, rx in COMPILED:
                m = rx.search(text)
                if m:
                    found.append((name, field, m.group(0), snippet(text, m)))
        if found:
            hits.append((r, found))
    excluded = [r for r in rows if r["link_type"] == "excluded"]
    out = ["# T1059.001 genuine pairs whose evidence matches another candidate technique or loads a tool\n",
           f"Scanned {len(rows)} T1059.001 genuine pairs ({len(rows) - len(excluded)} with evidence, "
           f"{len(excluded)} excluded by hand: {', '.join(r['pair_id'] for r in excluded)}). "
           f"{len(hits)} pairs match at least one pattern. Nothing is excluded by this list. "
           "Categories marked (extra) go beyond the requested list.\n",
           "| pair | cluster | link | evidence EID | category | field | matched | context |",
           "|---|---|---|---|---|---|---|---|"]
    for r, found in hits:
        for name, field, match, ctx in found:
            out.append(f"| `{r['pair_id']}` | {r['cluster_id'].split('|', 1)[1]} | {r['link_type']} | "
                       f"{r['evidence_event_id']} | {name} | {field} | `{match}` | {ctx} |")
    by_cat = {}
    for r, found in hits:
        for name, *_ in found:
            by_cat.setdefault(name, set()).add(r["pair_id"])
    out.append("\nPairs per category: " + "; ".join(f"{k}: {len(v)}" for k, v in by_cat.items()))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
