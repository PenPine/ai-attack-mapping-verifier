import json
from collections import Counter, defaultdict

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]

total = len(results)
correct = 0
errors = 0
by_tech = defaultdict(lambda: {"correct": 0, "total": 0, "none": 0, "error": 0})

for r in results:
    tech = r['technique_label']
    pred = r['prediction'].get('predicted_technique')
    by_tech[tech]["total"] += 1
    if 'error' in r['prediction']:
        errors += 1
        by_tech[tech]["error"] += 1
        continue
    if pred == tech:
        correct += 1
        by_tech[tech]["correct"] += 1
    elif pred == 'NONE':
        by_tech[tech]["none"] += 1

print(f"Total: {total}")
print(f"Errors: {errors}")
print(f"Overall accuracy (excl. errors): {correct}/{total-errors} = {correct/(total-errors)*100:.1f}%")
print()
print(f"{'Technique':<12} {'Correct':<9} {'Total':<7} {'Acc%':<7} {'NONE':<6} {'Err':<5}")
for tech, d in sorted(by_tech.items()):
    denom = d['total'] - d['error']
    acc = d['correct'] / denom * 100 if denom else 0
    print(f"{tech:<12} {d['correct']:<9} {d['total']:<7} {acc:<7.1f} {d['none']:<6} {d['error']:<5}")