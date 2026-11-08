"""
scripts/artifact_check.py
Read-only (2026-11-01). For the 17 Stage 3 answers whose correctness changed (genuine and misleading), extract
the artifacts the model's reasoning cites (GUIDs, event IDs, registry keys, paths, file and process names, hex
values, quoted strings, cmdlets, host-like names, a fixed list of tool names) and check each, case-insensitive,
against the prompt that was sent (system prompt + user prompt, rebuilt and checked against prompt_sha1).
No API calls. Follow-up checks: scripts/artifact_check2.py.

Run from the project root:  python scripts/artifact_check.py
"""
import hashlib, json, re, sys
sys.path.insert(0, ".")
import run_stage3 as S
from llm.prompts import STAGE3_SYSTEM_PROMPT

evals = {e["event_uid"]: e for e in S.load(S.EVAL)}
pairs = {r["pair_id"]: r for r in S.load(S.PAIRS)}
res = S.load("results/stage3_v3/stage3_results.jsonl")

changed = []
for r in res:
    if r["condition"] == "neutral":
        continue
    e = evals[r["event_uid"]]
    now = r["prediction"].get("predicted_technique") == e["technique_label"]
    if bool(e["baseline_correct"]) != now:
        changed.append(r)

TOOLS = ["Dumpert", "Outflank", "PurpleSharp", "Mimikatz", "Meterpreter", "MSFConsole", "Metasploit", "Covenant",
         "Empire", "PsExec", "Sysinternals", "ntdsutil", "wmiprvse", "DSC", "Task Manager", "taskmgr", "conhost",
         "Invoke-Expression", "Set-Service", "Move-Item", "New-Item", "View-Job", "schtasks", "WinPE"]
RULES = [
    ("guid", r"\{?[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}?"),
    ("event id", r"(?:Event\s?ID|EventID|Event)\s*(\d{1,5})\b"),
    ("registry key", r"\bHK(?:LM|CU|U|EY_[A-Z_]+)[:\\][^\s'\"(),;]+"),
    ("path", r"\b[A-Za-z]:\\[^\s'\"(),;]+"),
    ("file / process", r"\b[\w.-]+\.(?:exe|dll|ps1|psm1|psd1|dat|bin|dit|zip|txt|png|lnk|bat|vbs)\b"),
    ("hex value", r"\b0x[0-9A-Fa-f]+\b"),
    ("quoted name", r"'([^']{2,60})'|\"([^\"]{2,60})\""),
    ("cmdlet", r"\b[A-Z][a-z]+-[A-Z][A-Za-z]+\b"),
    ("host-like name", r"\b[A-Z]{2,}\d+\b"),
]


def extract(text):
    found = []
    for kind, rx in RULES:
        for m in re.finditer(rx, text):
            v = next((g for g in m.groups() if g), m.group(0)) if m.groups() else m.group(0)
            found.append((kind, v.rstrip(".:")))
    for t in TOOLS:
        if re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", text, re.I):
            found.append(("tool / program name", t))
    seen, out = set(), []
    for k, v in found:
        if v.lower() not in seen:
            seen.add(v.lower()); out.append((k, v))
    return out


def normalize(s):
    s = s.lower().replace("\\\\", "\\")
    s = re.sub(r"hku\\s-1-5-[\d-]+\\", "hkcu\\\\", s)        # HKU\<SID>\ written as HKCU\
    s = s.replace("hkcu:\\", "hkcu\\").replace("hklm:\\", "hklm\\").replace("hkcu:", "hkcu\\").replace("hklm:", "hklm\\")
    return s


print(f"changed answers: {len(changed)}")
for r in sorted(changed, key=lambda r: (r["condition"], r["event_uid"])):
    p = pairs[r["pair_id"]]
    up = S.user_prompt(p, evals)
    sha = hashlib.sha1((STAGE3_SYSTEM_PROMPT + "\n\n" + up).encode("utf-8")).hexdigest()
    prompt = STAGE3_SYSTEM_PROMPT + "\n\n" + up
    orig_part, _, ev_part = up.partition("Additional evidence:")
    reasoning = r["prediction"].get("reasoning") or r["raw"]
    arts = extract(reasoning)
    rows = []
    for kind, v in arts:
        lit = v.lower() in prompt.lower()
        where = ("original" if v.lower() in orig_part.lower() else "") + \
                ("+evidence" if v.lower() in ev_part.lower() else "") + \
                ("+system" if v.lower() in STAGE3_SYSTEM_PROMPT.lower() else "")
        norm = normalize(v) in normalize(prompt)
        rows.append((kind, v, lit, where.strip("+"), norm))
    missing = [x for x in rows if not x[2]]
    e = evals[r["event_uid"]]
    print(json.dumps({"pair": r["pair_id"], "label": e["technique_label"],
                      "new": r["prediction"].get("predicted_technique"), "prompt_sha1_matches": sha == r["prompt_sha1"],
                      "artifacts": len(rows), "not_in_prompt_literally": len(missing),
                      "checked": [f"{k}: {v} -> {'in ' + w if l else ('NOT FOUND' + (' (found after normalising)' if n else ''))}"
                                  for k, v, l, w, n in rows]}, ensure_ascii=False))
