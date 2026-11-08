import json
from collections import Counter

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
candidates = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cand_map = {}
i = 0
for c in candidates:
    cand_map[c['technique_label'] + '_' + str(i)] = c
    i += 1

correct_imgs, none_imgs = Counter(), Counter()
for r in results:
    if r['technique_label'] != 'T1562.002':
        continue
    image = str(cand_map[r['candidate_id']]['event'].get('Image', 'N/A'))
    name = image.split('\\')[-1].lower()
    pred = r['prediction'].get('predicted_technique')
    if pred == 'T1562.002':
        correct_imgs[name] += 1
    elif pred == 'NONE':
        none_imgs[name] += 1

print("Writer process among CORRECT predictions:")
for n, c in correct_imgs.most_common():
    print(f"  {c:4d}  {n}")
print()
print("Writer process among NONE predictions:")
for n, c in none_imgs.most_common():
    print(f"  {c:4d}  {n}")