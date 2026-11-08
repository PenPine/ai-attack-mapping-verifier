import json
from collections import Counter

data = [json.loads(l) for l in open('results/candidate_pool.jsonl')]
print(f"Total: {len(data)}")
counts = Counter(d['technique_label'] for d in data)
for t, c in sorted(counts.items()):
    print(f"  {t}: {c}")