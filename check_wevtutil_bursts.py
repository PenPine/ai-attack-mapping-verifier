import json
from collections import Counter

data = [json.loads(l) for l in open('results/candidate_pool.jsonl')]
bursts = Counter()
objs = Counter()
for d in data:
    if d['technique_label'] != 'T1562.002':
        continue
    e = d['event']
    if not str(e.get('Image', '')).lower().endswith('wevtutil.exe'):
        continue
    ts = str(e.get('UtcTime', e.get('TimeCreated', 'N/A')))[:16]
    src = d['source_file'].split('\\')[-1][:45]
    bursts[(src, ts)] += 1
    objs[str(e.get('TargetObject'))[:90]] += 1

print("wevtutil.exe events by (source file, minute):")
for (src, ts), c in bursts.most_common(8):
    print(f"  {c:4d}  {ts}  {src}")
print("distinct bursts:", len(bursts))
print()
print("Most common TargetObject:")
for t, c in objs.most_common(5):
    print(f"  {c:4d}  {t}")