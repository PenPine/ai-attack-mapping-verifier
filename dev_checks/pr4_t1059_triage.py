"""
pr4_t1059_triage.py
A first pass over the 23 T1059.001 review events. It does NOT judge anything. For each event it looks in the full
script text for telltale words of the technique the model answered, so you know where to look first.
  tokens found     -> the script contains words typical of the model's technique: read it carefully, it may be
                      a defensible alternative
  no tokens found  -> nothing typical of the model's technique is in the script: likely a model error, but check
Reads results/t1059_review.csv and results/pool_clean.jsonl. Writes results/t1059_triage.csv. No API calls.
"""
import csv
import json
import re

TOKENS = {      # (what is shown, pattern searched for, case-insensitive)
    "T1547.001": [("CurrentVersion\\Run", r"currentversion\\run"), ("\\Run\\", r"\\run\\"), ("RunOnce", r"runonce"),
                  ("shell:startup", r"shell:startup"), ("Startup folder", r"start menu\\programs\\startup")],
    "T1003.006": [("dcsync", r"dcsync"), ("DsGetNCChanges", r"dsgetncchanges"), ("replicat...", r"replicat"),
                  ("Get-ADReplication", r"get-adreplication"), ("lsadump", r"lsadump")],
    "T1546.003": [("__EventFilter", r"__eventfilter"), ("EventConsumer", r"eventconsumer"),
                  ("__FilterToConsumerBinding", r"__filtertoconsumerbinding"), ("Set-WmiInstance", r"set-wmiinstance"),
                  ("Register-WmiEvent", r"register-wmievent")],
    "T1021.002": [("ADMIN$", r"admin\$"), ("C$", r"\bc\$"), ("a UNC path (\\\\host\\share)", r"\\\\[\w.$-]+\\[\w$]"),
                  ("New-PSDrive", r"new-psdrive"), ("net use", r"net use"), ("psexec", r"psexec")],
    "T1562.002": [("wevtutil", r"wevtutil"), ("eventlog", r"eventlog"), ("auditpol", r"auditpol"),
                  ("Clear-EventLog", r"clear-eventlog"), ("Set-Service", r"set-service")],
    "T1055": [("VirtualAlloc", r"virtualalloc"), ("WriteProcessMemory", r"writeprocessmemory"),
              ("CreateRemoteThread", r"createremotethread"), ("QueueUserAPC", r"queueuserapc"),
              ("reflective", r"reflective"), ("inject", r"inject")],
}

pool = {}
with open("results/pool_clean.jsonl", encoding="utf-8") as f:
    for l in f:
        if l.strip():
            p = json.loads(l)
            pool[p["event_uid"]] = p

with open("results/t1059_review.csv", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

out, found_n = [], 0
print(f"{'id':<5}{'model answered':<12}{'script chars':>13}  {'signal':<18} tokens found")
for r in rows:
    text = str(pool[r["event_uid"]]["event"].get("ScriptBlockText") or "")
    ans = r["model_answer"]
    hits = sorted({label for label, pat in TOKENS.get(ans, []) if re.search(pat, text, flags=re.I)})
    signal = "tokens found" if hits else "no tokens found"
    found_n += bool(hits)
    print(f"{r['review_id']:<5}{ans:<12}{len(text):>13}  {signal:<18} {', '.join(hits)}")
    out.append({"review_id": r["review_id"], "event_uid": r["event_uid"], "model_answer": ans, "script_chars": len(text),
                "signal": signal, "tokens_found": "; ".join(hits), "script_start": " ".join(text.split())[:160]})
with open("results/t1059_triage.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print(f"\n{found_n} of {len(rows)} events contain words typical of the technique the model answered; {len(rows) - found_n} do not.")
print("This is only a pointer. Read the 'tokens found' ones first, then confirm or reject the others yourself.")