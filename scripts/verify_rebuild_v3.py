"""
scripts/verify_rebuild_v3.py
Rebuilds the pool in memory with the current rules (clean_pool.py + extraction/config.py) and diffs it
against the frozen PR4 pool (results/pool_clean.jsonl) and the written v3 pool (results/pool_clean_v3.jsonl).
Writes nothing. No API calls.

Run from the project root:  python scripts/verify_rebuild_v3.py
Expected (PR5): 292/66 -> 289/63, exactly 3 T1059.003 events removed (parent dsregcmd.exe, APT29 file),
none added, and the in-memory rebuild identical to pool_clean_v3.jsonl.
"""
import glob
import os
import sys
from collections import Counter

sys.path.insert(0, ".")
import clean_pool as cp

raw = []
for tech, folders in cp.TECHNIQUE_FOLDERS.items():
    for folder in folders:
        raw.extend(cp.extract_for_technique(tech, glob.glob(f"data/raw/{folder}/*.json")))
paths = sorted({p for fs in cp.TECHNIQUE_FOLDERS.values() for f in fs for p in glob.glob(f"data/raw/{f}/*.json")})
for p in paths:
    if cp.basename(p).startswith("apt29"):
        m = cp.boot_markers(p)
        if m:
            cp.BOOTS[cp.basename(p)] = m

ps = [r for r in raw if r["technique_label"] == "T1055" and "empire_psinject" in r["source_file"]]
keep_ps = min(ps, key=lambda r: r["event"].get("UtcTime", "")) if ps else None
seen, kept, excl = set(), [], Counter()
for rec in raw:
    reason = cp.exclusion_reason(rec, seen, keep_ps)
    if reason:
        excl[reason] += 1
    else:
        kept.append(rec)

new = {cp.event_uid(r): r for r in kept}
old = {p["event_uid"]: p for p in cp.load_jsonl("results/pool_clean.jsonl")}
print(f"raw: {len(raw)}  excluded: {dict(sorted(excl.items()))}")
print(f"old pool: {len(old)} events, {len({p['cluster_id'] for p in old.values()})} clusters")
print(f"new pool: {len(new)} events, {len({cp.cluster_id(r) for r in new.values()})} clusters")
removed, added = old.keys() - new.keys(), new.keys() - old.keys()
print(f"removed: {len(removed)}  added: {len(added)}")
for u in sorted(removed):
    p = old[u]
    print("  -", u, p["technique_label"], p["source_file"], p["cluster_id"],
          "Parent:", p["event"].get("ParentImage"), "Image:", p["event"].get("Image"))
for u in sorted(added):
    r = new[u]
    print("  +", u, r["technique_label"], cp.basename(r["source_file"]))

if os.path.exists(cp.OUT_POOL):
    written = {p["event_uid"]: p for p in cp.load_jsonl(cp.OUT_POOL)}
    same = written.keys() == new.keys() and all(written[u]["cluster_id"] == cp.cluster_id(new[u]) for u in new)
    print(f"{cp.OUT_POOL}: {len(written)} events, {'identical to' if same else 'DIFFERS FROM'} the in-memory rebuild")
