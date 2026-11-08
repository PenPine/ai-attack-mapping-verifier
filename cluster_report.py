import json
from collections import defaultdict

results = [json.loads(l) for l in open('results/baseline_full_results.jsonl')]
candidates = [json.loads(l) for l in open('results/candidate_pool.jsonl')]

cand_map = {}
for i, c in enumerate(candidates):
    cand_map[c['technique_label'] + '_' + str(i)] = c

def minute_of(e):
    ts = e.get('UtcTime') or e.get('TimeCreated') or e.get('EventTime') or 'NA'
    return str(ts).replace('T', ' ')[:16]

clusters = defaultdict(list)
for r in results:
    if 'error' in r['prediction']:
        continue
    c = cand_map[r['candidate_id']]
    key = (r['technique_label'], c['source_file'].split('\\')[-1], minute_of(c['event']))
    ok = 1 if r['prediction'].get('predicted_technique') == r['technique_label'] else 0
    clusters[key].append(ok)

by_tech = defaultdict(list)
for (tech, src, minute), vals in clusters.items():
    by_tech[tech].append(vals)

print(f"{'Technique':<11}{'Events':>7}{'Clusters':>9}{'MaxSize':>8}{'EventAcc':>10}{'ClusterAcc':>11}")
ev_c = ev_t = 0
cl_accs = []
for tech, groups in sorted(by_tech.items()):
    n = sum(len(g) for g in groups)
    k = sum(sum(g) for g in groups)
    ca = sum(sum(g) / len(g) for g in groups) / len(groups)
    print(f"{tech:<11}{n:>7}{len(groups):>9}{max(len(g) for g in groups):>8}{k/n*100:>9.1f}%{ca*100:>10.1f}%")
    ev_c += k
    ev_t += n
    cl_accs.extend(sum(g) / len(g) for g in groups)

print()
print(f"Total events: {ev_t}, total clusters: {len(cl_accs)}")
print(f"Event-level accuracy:   {ev_c / ev_t * 100:.1f}%")
print(f"Cluster-level accuracy: {sum(cl_accs) / len(cl_accs) * 100:.1f}%")