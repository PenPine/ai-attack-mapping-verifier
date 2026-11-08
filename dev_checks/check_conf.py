import json
from collections import Counter

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
ok, bad = Counter(), Counter()
for r in results:
    p = r['prediction']
    if 'confidence' not in p:
        continue
    b = min(int(p['confidence']) // 10 * 10, 90)
    (ok if p.get('predicted_technique') == r['technique_label'] else bad)[b] += 1
print("conf bin   correct   wrong")
for b in range(0, 100, 10):
    print(f"{b:>3}-{b+9:<3}   {ok[b]:>6}   {bad[b]:>5}")