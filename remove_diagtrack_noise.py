import json

data = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cleaned = []
removed = 0
for d in data:
    if d['technique_label'] == 'T1562.002':
        target = str(d['event'].get('TargetObject', '')).lower()
        if 'diagtrack' in target:
            removed += 1
            continue
    cleaned.append(d)

with open('results/candidate_pool.jsonl', 'w') as f:
    for d in cleaned:
        f.write(json.dumps(d) + "\n")

print(f"Before cleaning: {len(data)} records")
print(f"After cleaning: {len(cleaned)} records, removed {removed} DiagTrack false positives")