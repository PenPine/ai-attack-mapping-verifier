"""
scripts/recompute_tables_v3.py
Recomputes the PR4 tables on the v3 pool from the EXISTING baseline predictions. No API calls.

The PR4 analysis scripts are run unchanged. They read and write fixed paths under results/, so each run
happens in a temporary directory whose results/ holds staged copies of the inputs:
  pr4   results/pool_clean.jsonl, baseline_clean.jsonl, checks_*.json(l)        (reference re-run)
  v3    results/pool_clean_v3.jsonl, baseline_clean_v3.jsonl, and the existing checks sample and
        noise/mask runs with the clusters removed in v3 dropped (no re-sampling, no new runs)
Nothing under results/ is modified except results/tables_v3/, which receives:
  pr4/<script>.txt, v3/<script>.txt, the CSVs the scripts write, and side_by_side.txt

Run from the project root:  python scripts/recompute_tables_v3.py
"""
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "results", "tables_v3")
CHECK_MODES = ("noise", "mask1", "mask2")
RUNS = [
    ("pool_summary", None),
    ("pr4_baseline_metrics", ["pr4_baseline_metrics.py"]),
    ("pr4_checks_report", ["pr4_checks.py", "report"]),
    ("pr4_checks_report_lenient", ["pr4_checks.py", "report", "--lenient"]),
    ("pr4_eventid_baseline", ["pr4_eventid_baseline.py"]),
    ("pr4_cluster_window", ["pr4_cluster_window.py"]),
]
CSVS = ("confusion_events.csv", "confusion_clusters.csv", "prf_by_technique.csv")


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def dump(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def stage(version, d):
    src = os.path.join(ROOT, "results")
    res = os.path.join(d, "results")
    os.makedirs(res)
    suffix = "_v3" if version == "v3" else ""
    shutil.copy(os.path.join(src, f"pool_clean{suffix}.jsonl"), os.path.join(res, "pool_clean.jsonl"))
    shutil.copy(os.path.join(src, f"baseline_clean{suffix}.jsonl"), os.path.join(res, "baseline_clean.jsonl"))
    clusters = {p["cluster_id"] for p in load(os.path.join(res, "pool_clean.jsonl"))}
    sample = json.load(open(os.path.join(src, "checks_sample.json"), encoding="utf-8"))
    kept = [s for s in sample if s["cluster_id"] in clusters]
    json.dump(kept, open(os.path.join(res, "checks_sample.json"), "w", encoding="utf-8"), indent=1)
    uids = {s["event_uid"] for s in kept}
    dropped = {}
    for mode in CHECK_MODES:
        recs = load(os.path.join(src, f"checks_{mode}.jsonl"))
        dump([r for r in recs if r["event_uid"] in uids], os.path.join(res, f"checks_{mode}.jsonl"))
        dropped[mode] = len(recs) - sum(r["event_uid"] in uids for r in recs)
    return len(sample), len(kept), dropped


def pool_summary(d):
    """Same numbers as the end of clean_pool.py, computed from the staged pool and baseline."""
    pool = load(os.path.join(d, "results", "pool_clean.jsonl"))
    base = load(os.path.join(d, "results", "baseline_clean.jsonl"))
    lines = [f"kept events: {len(pool)}   clusters: {len({p['cluster_id'] for p in pool})}",
             f"baseline joined: {len(base)}"]
    by_cluster, ev_ok, ev_n = defaultdict(list), 0, 0
    for j in base:
        p = j["prediction"]
        if "error" in p:
            continue
        ok = int(p.get("predicted_technique") == j["technique_label"])
        by_cluster[j["cluster_id"]].append(ok)
        ev_ok, ev_n = ev_ok + ok, ev_n + 1
    cl = {c: sum(v) / len(v) for c, v in by_cluster.items()}
    ex = [a for c, a in cl.items() if not c.startswith("T1059.001|")]
    lines += [f"event-level accuracy:   {ev_ok / ev_n * 100:.1f}%  ({ev_ok}/{ev_n})",
              f"cluster-level accuracy: {sum(cl.values()) / len(cl) * 100:.1f}%  ({len(cl)} clusters)",
              f"cluster-level accuracy excl. T1059.001: {sum(ex) / len(ex) * 100:.1f}%  ({len(ex)} clusters)",
              "", "per technique (events / clusters / cluster-level correct):"]
    ev_t, cl_t = defaultdict(int), defaultdict(set)
    for p in pool:
        ev_t[p["technique_label"]] += 1
        cl_t[p["technique_label"]].add(p["cluster_id"])
    for t in sorted(ev_t):
        ok = sum(cl.get(c, 0) for c in cl_t[t])
        lines.append(f"  {t:<11}{ev_t[t]:>5}{len(cl_t[t]):>5}   {ok:.1f} of {len(cl_t[t])}")
    lines += ["", "by stratum (events / clusters):"]
    for s in ("atomic", "apt29"):
        ev = [p for p in pool if p["stratum"] == s]
        lines.append(f"  {s:<8}{len(ev):>5}{len({p['cluster_id'] for p in ev}):>5}")
    return "\n".join(lines) + "\n"


def run_all(version):
    out = os.path.join(OUT, version)
    os.makedirs(out, exist_ok=True)
    texts = {}
    with tempfile.TemporaryDirectory() as d:
        n_sample, n_kept, dropped = stage(version, d)
        print(f"[{version}] checks sample {n_sample} -> {n_kept}; records dropped per run: {dropped}")
        for name, cmd in RUNS:
            if cmd is None:
                text = pool_summary(d)
            else:
                r = subprocess.run([sys.executable, os.path.join(ROOT, cmd[0])] + cmd[1:], cwd=d,
                                   capture_output=True, text=True, encoding="utf-8")
                if r.returncode != 0:
                    raise SystemExit(f"[{version}] {name} failed:\n{r.stderr}")
                text = r.stdout
            texts[name] = text
            with open(os.path.join(out, f"{name}.txt"), "w", encoding="utf-8") as f:
                f.write(text)
        for c in CSVS:
            shutil.copy(os.path.join(d, "results", c), os.path.join(out, c))
    return texts


def side_by_side(old, new, width=78):
    lines = []
    for name, _ in RUNS:
        a, b = old[name].splitlines(), new[name].splitlines()
        lines.append("=" * (2 * width + 3) + f"\n{name}   (PR4 | v3; changed lines only)")
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            for k in range(max(i2 - i1, j2 - j1)):
                l = a[i1 + k] if i1 + k < i2 else ""
                r = b[j1 + k] if j1 + k < j2 else ""
                lines.append(f"{l[:width]:<{width}} | {r[:width]}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    old, new = run_all("pr4"), run_all("v3")
    sbs = side_by_side(old, new)
    with open(os.path.join(OUT, "side_by_side.txt"), "w", encoding="utf-8") as f:
        f.write(sbs)
    print(f"wrote {OUT}")
