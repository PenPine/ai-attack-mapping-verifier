"""
scripts/artifact_check2.py
Read-only (2026-11-01), follow-up to scripts/artifact_check.py: checks each cited Event ID against the EventID
lines of the original and the evidence event, and prints the prompt lines closest to the artifacts that were
not found literally. No API calls.

Run from the project root:  python scripts/artifact_check2.py
"""
import re, sys
sys.path.insert(0, ".")
import run_stage3 as S
evals = {e["event_uid"]: e for e in S.load(S.EVAL)}
pairs = {r["pair_id"]: r for r in S.load(S.PAIRS)}
res = {r["pair_id"]: r for r in S.load("results/stage3_v3/stage3_results.jsonl")}

# event IDs cited: check against the EventID lines of the original and the evidence
cites = {"15a2624605c9e3d3|misleading": ["4662"], "691ea664af0c6825|misleading": ["4662"],
         "235415a4e63aed89|misleading": ["8"], "57ef63e46ffa0e1f|misleading": ["8"],
         "243e55d798340ba4|misleading": ["19"], "ac42058f1cdd3ac1|misleading": ["10"],
         "ae4b62e1857e1a39|misleading": ["4104"], "b7d819458bfa1246|misleading": ["13"]}
for pid, ids in cites.items():
    up = S.user_prompt(pairs[pid], evals)
    o, _, ev = up.partition("Additional evidence:")
    oid = re.search(r"^EventID: (\d+)$", o, re.M).group(1)
    eid = re.search(r"^EventID: (\d+)$", ev, re.M).group(1)
    print(f"{pid}: cited {ids}; original EventID {oid}, evidence EventID {eid}")

print()
probes = {"ae4b62e1857e1a39|genuine": ["ntds", "dit"],
          "0793212750e00b04|misleading": ["Run\\Updater", "HKCU"],
          "b7d819458bfa1246|misleading": ["Run\\Updater", "HKCU"],
          "30f8bc022db8378b|misleading": ["Software\\Classes", "HKCU"],
          "ae4b62e1857e1a39|misleading": ["View-Job"]}
for pid, keys in probes.items():
    up = S.user_prompt(pairs[pid], evals)
    lines = [l for l in up.splitlines() if any(k.lower() in l.lower() for k in keys)]
    print(f"== {pid}")
    for l in lines:
        print("   ", l[:260])
