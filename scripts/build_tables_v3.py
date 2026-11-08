"""
scripts/build_tables_v3.py
Tables 1-5 of the report on the v3 pool, in the PR4 layout, from the existing baseline predictions and the
existing noise / mask runs. No API calls. Run scripts/recompute_tables_v3.py first (Table 1 is rendered from
the CSVs that the unchanged pr4_baseline_metrics.py writes there).

  Table 1  baseline metrics: confusion matrix and per-technique P/R/F1, event and cluster level
  Table 2  defensible-alternatives sensitivity (row 1 = v3 main result, row 2 = reviewed alternatives counted)
  Table 3  noise floor and masking checks, PR4 convention: n = 63 in every row, an answer that is not valid
           JSON counts as not correct; lenient parsing as a separate sensitivity row
  Table 4  cluster time-window sensitivity
  Table 5  Event ID lookup baseline (tie rule: see evaluation/eventid_lookup.py)

Run from the project root:  python scripts/build_tables_v3.py
Outputs: results/tables_v3/v3/table1.md ... table5.md
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, ".")
from evaluation import eventid_lookup as lk
from pr4_checks import exact_mcnemar, parse_prediction

OUT = "results/tables_v3/v3"
TECHS = ["T1003.001", "T1003.006", "T1021.002", "T1053.005", "T1055",
         "T1059.001", "T1059.003", "T1546.003", "T1547.001", "T1562.002"]
ACCEPT = {"defensible_alternative", "both"}
WINDOWS = [30, 60, 120, 300]


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def md(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(a, b):
    return f"{a / b * 100:.1f}%"


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")
    print(f"wrote {OUT}/{name}")


pool = load("results/pool_clean_v3.jsonl")
by_uid = {p["event_uid"]: p for p in pool}
base = load("results/baseline_clean_v3.jsonl")
pred = {b["event_uid"]: b["prediction"] for b in base}
clusters = {p["cluster_id"] for p in pool}


# ---------------- Table 1 ----------------
def table1():
    parts = ["# Table 1. Baseline: confusion matrix and per-technique precision / recall / F1 (v3 pool)\n"]
    prf = defaultdict(dict)
    with open(f"{OUT}/prf_by_technique.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            prf[r["level"]][r["technique"]] = r
    for level, fname, dec in (("event", "events", 0), ("cluster", "clusters", 1)):
        with open(f"{OUT}/confusion_{fname}.csv", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        head, body = rows[0], rows[1:]
        fmt = (lambda v: f"{float(v):.0f}") if dec == 0 else (lambda v: f"{float(v):.1f}")
        diag = sum(float(r[head.index(r[0])]) for r in body)
        total = sum(float(prf[level][t]["support"]) for t in TECHS)
        macro = sum(float(prf[level][t]["f1"]) for t in TECHS) / len(TECHS)
        note = "each event counts 1" if level == "event" else "each cluster counts 1"
        parts.append(f"## {level.capitalize()} level ({note})\n")
        parts.append(md(["true label \\ model answer"] + head[1:], [[r[0]] + [fmt(v) for v in r[1:]] for r in body]))
        parts.append("")
        parts.append(md(["technique", "support", "precision", "recall", "F1"],
                        [[t, f"{float(prf[level][t]['support']):.1f}",
                          f"{float(prf[level][t]['precision']):.2f}" if prf[level][t]["precision"] else "n/a",
                          f"{float(prf[level][t]['recall']):.2f}" if prf[level][t]["recall"] else "n/a",
                          f"{float(prf[level][t]['f1']):.2f}"] for t in TECHS]))
        parts.append(f"\nMacro-F1 over the 10 techniques: {macro:.3f}. Accuracy: {diag / total * 100:.1f}%.\n")
    n_skip = sum(1 for b in base if "predicted_technique" not in b["prediction"])
    parts.append(f"Scored events: {len(base) - n_skip} of {len(base)} ({n_skip} without a parseable answer); "
                 f"clusters: {len(clusters)}. OTHER = an answer that is not one of the 10 IDs or NONE.")
    write("table1.md", "\n".join(parts))


# ---------------- Table 2 ----------------
def table2():
    with open("results/t1059_review.csv", newline="", encoding="utf-8-sig") as f:
        review = list(csv.DictReader(f))
    accepted = {r["event_uid"] for r in review if (r["judgment"] or "").strip() in ACCEPT}
    blank = sum(1 for r in review if not (r["judgment"] or "").strip())
    in_pool = len(accepted & by_uid.keys())

    def view(accept):
        ev_ok = ev_n = t1_ok = t1_n = 0
        cl = defaultdict(list)
        for p in pool:
            pr = pred.get(p["event_uid"], {})
            if "predicted_technique" not in pr:
                continue
            ok = int(pr["predicted_technique"] == p["technique_label"] or p["event_uid"] in accept)
            ev_ok, ev_n = ev_ok + ok, ev_n + 1
            if p["technique_label"] == "T1059.001":
                t1_ok, t1_n = t1_ok + ok, t1_n + 1
            cl[(p["cluster_id"], p["technique_label"])].append(ok)
        shares = [(t, sum(v) / len(v)) for (_, t), v in cl.items()]
        ex = [s for t, s in shares if t != "T1059.001"]
        t1 = [s for t, s in shares if t == "T1059.001"]
        return [ev_n, pct(ev_ok, ev_n), len(shares), f"{sum(s for _, s in shares) / len(shares) * 100:.1f}%",
                f"{sum(ex) / len(ex) * 100:.1f}% ({len(ex)})", f"{pct(t1_ok, t1_n)} ({t1_ok}/{t1_n})",
                f"{sum(t1) / len(t1) * 100:.1f}% ({len(t1)})"]

    rows = [["1. v3 main result"] + view(set()), ["2. defensible alternatives counted"] + view(accepted)]
    text = ("# Table 2. Agreement with the rule label, with reviewed T1059.001 alternatives counted (v3 pool)\n\n"
            + md(["", "events", "event %", "clusters", "cluster %", "cluster % excl. T1059.001",
                  "T1059.001 event", "T1059.001 cluster"], rows)
            + f"\n\nRow 2 counts the {len(accepted)} T1059.001 events judged defensible_alternative or both in "
              f"results/t1059_review.csv ({in_pool} of them are in the v3 pool; {blank} events without a judgment "
              "are treated as not acceptable). One reviewer, AI-assisted reading: descriptive only. The main numbers "
              "remain those in row 1. The PR4 row 3 (without the dsregcmd.exe events) is now the v3 pool itself.")
    write("table2.md", text)


# ---------------- Table 3 ----------------
def table3():
    sample = [s for s in json.load(open("results/checks_sample.json", encoding="utf-8")) if s["cluster_id"] in clusters]
    n_all = len(sample)

    def correct(p, label, lenient):
        d = parse_prediction(p, lenient) if p is not None else None
        return d is not None and d.get("predicted_technique") == label

    def cells(run, subset, lenient):
        b = sum(correct(pred[s["event_uid"]], s["technique_label"], False) for s in subset)
        if run is None:
            return [f"{b}/{len(subset)} ({b / len(subset) * 100:.0f}%)", "", ""]
        c = lost = gained = 0
        for s in subset:
            ok0 = correct(pred[s["event_uid"]], s["technique_label"], False)
            ok1 = correct(run.get(s["event_uid"]), s["technique_label"], lenient)
            c, lost, gained = c + ok1, lost + (ok0 and not ok1), gained + (ok1 and not ok0)
        return [f"{c}/{len(subset)} ({c / len(subset) * 100:.0f}%)", f"{lost} / {gained}", f"{exact_mcnemar(lost, gained):.3f}"]

    ex = [s for s in sample if s["technique_label"] != "T1059.001"]
    runs = {m: {r["event_uid"]: r["prediction"] for r in load(f"results/checks_{m}.jsonl")} for m in ("noise", "mask1", "mask2")}
    missing = {m: sum(s["event_uid"] not in runs[m] for s in sample) for m in runs}
    invalid = {m: sum(s["event_uid"] in runs[m] and parse_prediction(runs[m][s["event_uid"]], False) is None for s in sample)
               for m in runs}
    def differ(run, lenient):
        if run is None:
            return ""
        answers = [parse_prediction(run[s["event_uid"]], lenient) for s in sample]
        valid = [(s, a) for s, a in zip(sample, answers) if a is not None]
        n = sum(a["predicted_technique"] != pred[s["event_uid"]]["predicted_technique"] for s, a in valid)
        miss = len(sample) - len(valid)
        return f"{n} of {len(valid)}" + (f" ({miss} had no valid answer)" if miss else "")

    spec = [("Baseline (stored)", None, False),
            ("Noise floor: same prompt, repeated", "noise", False),
            ("Mask 1: event-type cues hidden", "mask1", False),
            ("Mask 2: event-type cues + process/tool names hidden", "mask2", False),
            ("Mask 2, lenient parsing (sensitivity)", "mask2", True)]
    rows = []
    for name, mode, lenient in spec:
        run = runs[mode] if mode else None
        rows.append([name] + cells(run, sample, lenient) + cells(run, ex, lenient) + [differ(run, lenient)])
    for m in ("noise", "mask1"):
        same = all(correct(runs[m].get(s["event_uid"]), s["technique_label"], True)
                   == correct(runs[m].get(s["event_uid"]), s["technique_label"], False) for s in sample)
        assert same, f"lenient parsing changes the {m} row; add it to Table 3"
    text = ("# Table 3. Noise floor and masking ablation (v3 pool, one event per cluster)\n\n"
            + md(["", f"Correct (all, n={n_all})", "Lost / gained", "exact McNemar p",
                  f"Correct (excl. T1059.001, n={len(ex)})", "Lost / gained", "exact McNemar p",
                  "Answers that differ from the baseline"], rows)
            + f"\n\nn = {n_all} in every row: the PR4 sample of {n_all + 3} clusters minus the 3 clusters removed in v3 "
              "(no re-sampling, no new runs). An answer that is not valid JSON counts as not correct. "
              "Lost = correct in the baseline, not correct in the check; gained = the reverse. "
              "Answers that differ: valid answers naming a different technique (or NONE) than the stored baseline "
              "answer, out of the valid answers. "
              f"Answers that were not valid JSON: noise {invalid['noise']}, mask 1 {invalid['mask1']}, "
              f"mask 2 {invalid['mask2']}. Lenient parsing (take the JSON object that follows some prose) changes "
              "only the Mask 2 row, so it is shown for Mask 2 only.")
    assert not any(missing.values()), f"sample events without a check record: {missing}"
    write("table3.md", text)


# ---------------- Table 4 ----------------
def ts_of(e):
    # same field priority and formats as pr4_cluster_window.py
    v = e.get("UtcTime") or e.get("TimeCreated") or e.get("EventTime")
    if not v:
        return None
    s = str(v).replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    return None


def table4():
    res = {}
    for W in WINDOWS:
        c = defaultdict(list)
        for p in pool:
            t = ts_of(p["event"])
            pr = pred.get(p["event_uid"], {})
            ok = None if "predicted_technique" not in pr else int(pr["predicted_technique"] == p["technique_label"])
            c[(p["technique_label"], p["source_file"], "NA" if t is None else int(t // W))].append(ok)
        per = {}
        for key, oks in c.items():
            scored = [o for o in oks if o is not None]
            if scored:
                per[key] = (key[0], sum(scored) / len(scored), len(oks))
        res[W] = list(per.values())
    assert len(res[60]) == len(clusters), "60 s window does not reproduce the pool's clusters"
    rows = []
    for W in WINDOWS:
        allv = res[W]
        ex = [v for v in allv if v[0] != "T1059.001"]
        acc, acc_ex = sum(v[1] for v in allv) / len(allv), sum(v[1] for v in ex) / len(ex)
        ca, ce = round(acc * len(allv)), round(acc_ex * len(ex))
        rows.append([f"{W} s" + (" (original)" if W == 60 else ""), len(allv), len(ex), sum(1 for v in allv if v[2] == 1),
                     f"{acc * 100:.1f}%", f"{acc_ex * 100:.1f}%", f"{ca}/{len(allv) - ca}", f"{ce}/{len(ex) - ce}"])
    per_t = [[t] + [sum(1 for v in res[W] if v[0] == t) for W in WINDOWS] for t in TECHS]
    text = ("# Table 4. Sensitivity of the cluster definition to the time window (v3 pool)\n\n"
            + md(["window", "clusters", "excl. T1059.001", "singletons", "accuracy (all)", "accuracy (excl.)",
                  "correct/wrong (all)", "correct/wrong (excl.)"], rows)
            + "\n\nClusters per technique\n\n" + md(["technique"] + [f"{W} s" for W in WINDOWS], per_t)
            + "\n\nCluster = same technique label + same source file + same W-second bucket; 60 s is the definition "
              "used everywhere else. Accuracy is cluster-level; correct/wrong rounds the summed cluster shares.")
    write("table4.md", text)


# ---------------- Table 5 ----------------
def table5():
    rows, llm = [], []
    for b in base:
        pr = b["prediction"]
        if "predicted_technique" not in pr:
            continue
        rows.append((b["cluster_id"], b["technique_label"], str(by_uid[b["event_uid"]]["event"].get("EventID"))))
        llm.append(int(pr["predicted_technique"] == b["technique_label"]))
    by_cl = defaultdict(list)
    for (cid, label, _), ok in zip(rows, llm):
        by_cl[cid].append((label, ok))
    llm_cl = {cid: sum(o for _, o in v) / len(v) for cid, v in by_cl.items()}
    llm_pt = defaultdict(list)
    for cid, v in by_cl.items():
        llm_pt[v[0][0]].append(llm_cl[cid])

    ins = lk.evaluate(rows, loo=False)
    loo = lk.evaluate(rows, loo=True)
    up = lk.evaluate(rows, loo=True, tie_rule="upper")
    f = lambda r: [f"{r['event_acc'] * 100:.1f}%", f"{r['cluster_acc'] * 100:.1f}%", f"{len(r['ties'])} ({r['tie_clusters']})"]
    main = [["LLM baseline", pct(sum(llm), len(llm)), f"{sum(llm_cl.values()) / len(llm_cl) * 100:.1f}%", ""],
            ["Event ID lookup, in-sample (ceiling)"] + f(ins),
            ["Event ID lookup, leave-one-cluster"] + f(loo),
            ["  same, ties resolved to the true label (upper bound)"] + f(up)]
    mean = lambda v: f"{sum(v) / len(v) * 100:.0f}%"
    per_t = [[t, len(llm_pt[t]), mean(llm_pt[t]), mean(ins["per_tech"][t]), mean(loo["per_tech"][t]),
              mean(up["per_tech"][t])] for t in TECHS if t in llm_pt]
    table = lk.build_table(rows)
    multi = [f"- Event ID {e}: " + ", ".join(f"{t}: {n}" for t, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
             for e, c in sorted(table.items(), key=lambda kv: -sum(kv[1].values())) if len(c) > 1]
    grouped = defaultdict(list)
    for t in loo["ties"]:
        grouped[(t["cluster_id"], t["event_id"], json.dumps(t["counts"]), t["prediction"], t["technique_label"])].append(t)
    ties = [f"- left out {cid} ({len(v)} event{'s' if len(v) > 1 else ''}): Event ID {eid} counts {counts} -> {p} "
            f"(true label {label})" for (cid, eid, counts, p, label), v in grouped.items()]
    text = ("# Table 5. Event ID lookup baseline vs the LLM (v3 pool)\n\n"
            + md(["", "event level", "cluster level", "predictions decided by a tie (clusters)"], main)
            + f"\n\nScored events: {len(rows)}; clusters: {len(by_cl)}. Lookup = majority technique label per Event ID. "
              "Leave-one-cluster builds the lookup without the cluster being predicted. Unseen Event IDs and ties "
              "both get NONE (counted wrong); the upper-bound row resolves each tie to the true label.\n\n"
              "Ties in the leave-one-cluster lookup:\n" + ("\n".join(ties) if ties else "- none")
            + "\n\nCluster-level accuracy by technique\n\n"
            + md(["technique", "clusters", "LLM", "lookup in-sample", "lookup leave-one-cluster", "upper bound"], per_t)
            + "\n\nEvent IDs that carry more than one technique label (the lookup cannot separate these):\n"
            + "\n".join(multi))
    write("table5.md", text)
    return ins, loo, up


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    table1()
    table2()
    table3()
    table4()
    table5()
