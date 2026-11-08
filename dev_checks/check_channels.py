import json
from collections import Counter, defaultdict

data = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

by_tech = defaultdict(Counter)
for d in data:
    channel = str(d['event'].get('Channel', 'N/A')).lower()
    by_tech[d['technique_label']][channel] += 1

for tech, counts in sorted(by_tech.items()):
    print(f"=== {tech} ===")
    for ch, c in counts.most_common():
        print(f"  {c:4d}  {ch}")
    print()