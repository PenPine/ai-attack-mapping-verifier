import json
from collections import Counter

pool = [json.loads(l) for l in open("results/pool_clean.jsonl") if l.strip()]
sb = [p for p in pool if p["technique_label"] == "T1059.001"]
print("T1059.001 events:", len(sb), "clusters:", len({p["cluster_id"] for p in sb}))

print("\nby script origin:")
for k, n in Counter("has file Path" if p["event"].get("Path") else "no Path (in-memory)" for p in sb).most_common():
    print(f"  {n:4d}  {k}")

print("\nby source file:")
for k, n in Counter(p["source_file"][:50] for p in sb).most_common():
    print(f"  {n:4d}  {k}")

print("\nfile-based script names:")
for k, n in Counter(str(p["event"].get("Path")).split("\\")[-1] for p in sb if p["event"].get("Path")).most_common(8):
    print(f"  {n:4d}  {k}")

print("\nmost common script-block openings:")
for k, n in Counter(" ".join(str(p["event"].get("ScriptBlockText", "")).split())[:70] for p in sb).most_common(12):
    print(f"  {n:4d}  {k}")