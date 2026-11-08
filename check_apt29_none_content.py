import json

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
candidates = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cand_map = {}
i = 0
for c in candidates:
    cid = c['technique_label'] + '_' + str(i)
    cand_map[cid] = c
    i += 1

shown = 0
for r in results:
    if (r['prediction'].get('predicted_technique') == 'NONE'
            and r['technique_label'] == 'T1562.002'
            and 'apt29' in cand_map.get(r['candidate_id'], {}).get('source_file', '')):
        cand = cand_map[r['candidate_id']]
        print('candidate_id:', r['candidate_id'])
        print('TargetObject:', cand['event'].get('TargetObject'))
        print('Image/ProcessName:', cand['event'].get('Image', cand['event'].get('ProcessName')))
        print('reasoning:', r['prediction'].get('reasoning'))
        print()
        shown += 1
        if shown >= 5:
            break