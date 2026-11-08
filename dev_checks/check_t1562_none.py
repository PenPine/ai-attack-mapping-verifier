import json
from collections import Counter

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
candidates = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cand_map = {}
i = 0
for c in candidates:
    cid = c['technique_label'] + '_' + str(i)
    cand_map[cid] = c
    i += 1

targets = Counter()
images = Counter()
samples = []
for r in results:
    if r['technique_label'] == 'T1562.002' and r['prediction'].get('predicted_technique') == 'NONE':
        e = cand_map[r['candidate_id']]['event']
        targets[str(e.get('TargetObject'))[:110]] += 1
        images[str(e.get('Image'))[-45:]] += 1
        if len(samples) < 4:
            samples.append((str(e.get('TargetObject'))[:110], r['prediction'].get('reasoning')))

print("TargetObject distribution:")
for t, c in targets.most_common(10):
    print(f"  {c:3d}  {t}")
print()
print("Image distribution:")
for t, c in images.most_common(5):
    print(f"  {c:3d}  {t}")
print()
for t, reason in samples:
    print("Example:", t)
    print("  Reasoning:", reason)