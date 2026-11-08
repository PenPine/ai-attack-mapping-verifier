import json
from collections import Counter

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
candidates = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cand_map = {}
i = 0
for c in candidates:
    cid = c['technique_label'] + '_' + str(i)
    cand_map[cid] = c['source_file']
    i += 1

none_ids = [r['candidate_id'] for r in results
            if r['prediction'].get('predicted_technique') == 'NONE'
            and r['technique_label'] == 'T1562.002']

sources = Counter(cand_map.get(cid, 'UNKNOWN') for cid in none_ids)
print(f"T1562.002 里被判成 NONE 的共 {len(none_ids)} 条，来源分布：")
for src, c in sources.most_common():
    print(f"  {c} 条: {src}")