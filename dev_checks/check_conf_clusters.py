import json
from collections import defaultdict, Counter

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
    p = r['prediction']
    if 'error' in p or 'confidence' not in p:
        continue
    c = cand_map[r['candidate_id']]
    key = (r['technique_label'], c['source_file'].split('\\')[-1], minute_of(c['event']))
    clusters[key].append((int(p['confidence']), p.get('predicted_technique') == r['technique_label'], p.get('predicted_technique')))

rows = []
for key, items in clusters.items():
    conf = sum(x[0] for x in items) / len(items)
    acc = sum(x[1] for x in items) / len(items)
    rows.append((key, conf, acc, len(items), items))

def bucket(conf):
    if conf < 70: return '<70'
    if conf < 80: return '70-79'
    if conf < 90: return '80-89'
    return '90+'

bins = defaultdict(list)
for key, conf, acc, n, items in rows:
    bins[bucket(conf)].append((conf, acc))

print("Cluster-level confidence vs accuracy")
print(f"{'bin':<7}{'clusters':>9}{'mean conf':>11}{'accuracy':>10}")
for b in ['<70', '70-79', '80-89', '90+']:
    v = bins.get(b, [])
    if v:
        print(f"{b:<7}{len(v):>9}{sum(x[0] for x in v)/len(v):>10.1f}%{sum(x[1] for x in v)/len(v)*100:>9.1f}%")
    else:
        print(f"{b:<7}{0:>9}")

mc = sum(r[1] for r in rows) / len(rows)
ma = sum(r[2] for r in rows) / len(rows)
brier = sum((r[1] / 100 - r[2]) ** 2 for r in rows) / len(rows)
print()
print(f"Clusters: {len(rows)}  mean confidence: {mc:.1f}%  mean accuracy: {ma*100:.1f}%  Brier: {brier:.3f}")

print()
print("Clusters with mean confidence >= 90 that were NOT fully correct:")
for key, conf, acc, n, items in sorted(rows, key=lambda r: -r[1]):
    if conf >= 90 and acc < 1:
        preds = Counter(x[2] for x in items if not x[1])
        print(f"  {key[0]:<10} conf {conf:.0f}  acc {acc*100:.0f}%  n={n}  wrong ->", dict(preds))

print()
print("Wrong predictions by (true -> predicted), in cluster-equivalents:")
pairs = Counter()
for key, conf, acc, n, items in rows:
    wrong = [x[2] for x in items if not x[1]]
    for p, cnt in Counter(wrong).items():
        pairs[(key[0], p)] += cnt / n
for (t, p), w in pairs.most_common(12):
    print(f"  {t} -> {p}: {w:.1f}")