import json

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
candidates = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cand_map = {}
i = 0
for c in candidates:
    cid = c['technique_label'] + '_' + str(i)
    cand_map[cid] = c
    i += 1

for r in results:
    if r['technique_label'] == 'T1546.003' and r['prediction'].get('predicted_technique') == 'NONE':
        cand = cand_map[r['candidate_id']]
        e = cand['event']
        print('candidate_id:', r['candidate_id'])
        print('source:', cand['source_file'].split(chr(92))[-1][:60])
        print('EventID:', e.get('EventID'))
        for key in ['EventType', 'Operation', 'User', 'Name', 'Type', 'Query', 'Destination', 'Consumer', 'Filter', 'EventNamespace', 'Image']:
            if key in e:
                print(f'  {key}:', str(e[key])[:150])
        print('confidence:', r['prediction'].get('confidence'))
        print('reasoning:', r['prediction'].get('reasoning'))
        print()