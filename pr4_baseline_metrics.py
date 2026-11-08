"""
pr4_baseline_metrics.py
Confusion matrix and per-technique precision / recall / F1 for the baseline on the frozen pool.
No API calls. Reads results/baseline_clean.jsonl. Writes three CSV files into results/.

Two views, because the unit of analysis is the cluster:
  event-level    every scored event counts once
  cluster-level  every event counts 1/(events scored in its cluster), so each cluster counts once
"""
import csv
import json
from collections import Counter, defaultdict

TECHS = ["T1003.001", "T1003.006", "T1021.002", "T1053.005", "T1055",
         "T1059.001", "T1059.003", "T1546.003", "T1547.001", "T1562.002"]
COLS = TECHS + ["NONE", "OTHER"]   # OTHER = any string that is not one of the 10 IDs or NONE


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


rows, skipped = [], 0
for b in load("results/baseline_clean.jsonl"):
    p = b["prediction"]
    if "error" in p or "predicted_technique" not in p:
        skipped += 1
        continue
    pred = p["predicted_technique"]
    if pred not in TECHS and pred != "NONE":
        pred = "OTHER"
    rows.append((b["cluster_id"], b["technique_label"], pred))

n_in = Counter(c for c, _, _ in rows)
print(f"scored events: {len(rows)}   clusters: {len(n_in)}   skipped (no parseable answer): {skipped}")


def confusion(weight):
    m = {t: Counter() for t in TECHS}
    for c, t, p in rows:
        m[t][p] += weight(c)
    return m


def prf(m):
    out = {}
    for t in TECHS:
        tp = m[t][t]
        support = sum(m[t].values())
        fp = sum(m[o][t] for o in TECHS if o != t)
        prec = tp / (tp + fp) if (tp + fp) else None
        rec = tp / support if support else None
        f1 = 0.0 if tp == 0 else 2 * prec * rec / (prec + rec)
        out[t] = (support, prec, rec, f1)
    return out


def short(c):
    return c[1:] if c.startswith("T") else c      # T1003.001 -> 1003.001


def cell(v, decimals):
    return f"{v:>9.{decimals}f}" if decimals else f"{int(round(v)):>9}"


def show(name, m, fname, decimals):
    print(f"\n=== {name} ===")
    print(f"{'true label':<17}" + "".join(f"{short(c):>9}" for c in COLS) + "   <- model answer")
    for t in TECHS:
        print(f"{t:<17}" + "".join(cell(m[t][c], decimals) for c in COLS))
    with open(f"results/confusion_{fname}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["true_label"] + COLS)
        for t in TECHS:
            w.writerow([t] + [round(m[t][c], 3) for c in COLS])
    res = prf(m)
    print(f"\n{'technique':<12}{'support':>9}{'precision':>11}{'recall':>9}{'F1':>7}")
    for t in TECHS:
        s, p, r, f1 = res[t]
        ps = f"{p:.2f}" if p is not None else "n/a"
        rs = f"{r:.2f}" if r is not None else "n/a"
        print(f"{t:<12}{s:>9.1f}{ps:>11}{rs:>9}{f1:>7.2f}")
    macro = sum(res[t][3] for t in TECHS) / len(TECHS)
    total = sum(res[t][0] for t in TECHS)
    acc = sum(m[t][t] for t in TECHS) / total
    print(f"macro-F1 over the 10 techniques: {macro:.3f}    accuracy: {acc * 100:.1f}%")
    return res


ev = show("EVENT level (each event counts 1)", confusion(lambda c: 1.0), "events", 0)
cl = show("CLUSTER level (each cluster counts 1)", confusion(lambda c: 1.0 / n_in[c]), "clusters", 1)

with open("results/prf_by_technique.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["technique", "level", "support", "precision", "recall", "f1"])
    for level, res in (("event", ev), ("cluster", cl)):
        for t in TECHS:
            s, p, r, f1 = res[t]
            w.writerow([t, level, round(s, 2), "" if p is None else round(p, 3),
                        "" if r is None else round(r, 3), round(f1, 3)])
print("\nwrote results/confusion_events.csv, confusion_clusters.csv, prf_by_technique.csv")