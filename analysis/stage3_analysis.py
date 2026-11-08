"""
analysis/stage3_analysis.py
Stage 3 analysis (PR4 Evaluation plan). No API calls.

Unit: cluster. A cluster's score in a condition is the share of its sampled eval events scored correct there
(primary parse: lenient, the last valid JSON object with predicted_technique; no such object = not correct).
Its baseline score is the share of the same events whose stored baseline answer is correct. A contrast
between two arms uses, per cluster, only the events answered in both arms; clusters with none drop out.

Primary contrast: misleading vs baseline (two-sided, alpha 0.05; T1021.002 excluded, it has no misleading
condition). Secondary: genuine vs baseline, neutral vs baseline, misleading vs neutral, Holm-corrected
together. Test: paired permutation (sign flip) on the per-cluster score differences, statistic = their sum;
exact over the clusters with a non-zero difference when there are at most 25 of them, otherwise 1,000,000
random sign flips with seed PERM_SEED (p = (hits + 1) / (N + 1)). Every test runs on four cluster sets:
all 63, 40 excluding T1059.001, and both without the 3 sensitivity clusters (60, 37). A conclusion needs the
63 and 40 sets to agree in direction.

Descriptive, per condition: corrections / regressions / unchanged (event and cluster level), mean confidence
and its change, Brier score and 5-bin ECE (with the number of answers left out for lack of a valid
confidence), non-JSON rate, the tests with strict parsing, T1059.001 alone, and genuine / misleading split
by same vs different log channel.
Sensitivity of the primary contrast: (a) one event per cluster (seed ONE_PER_CLUSTER_SEED), (b) each
technique left out in turn. Cap 5 and the reboot-window sensitivity of the plan are not run (new calls or a
new pool would be needed). Exploratory (PR4 plan): under misleading evidence, baseline confidence of the
events that regressed vs those that stayed correct.
Post hoc, exploratory (2026-11-08, after the results): every test again without the T1021.002 clusters that are a
local service install (POST_HOC_LOCAL_INSTALL), printed last and labelled as such.

Run from the project root:  python analysis/stage3_analysis.py results/stage3_v3/stage3_results.jsonl
On the full results the printed output is also saved to results/stage3_v3/analysis_output.txt.
"""
import json
import os
import random
import sys
from collections import defaultdict
from fractions import Fraction
from math import lcm

import numpy as np

sys.path.insert(0, ".")
from run_stage3 import parse_lenient, parse_strict  # noqa: E402  same parsers as the runner

FULL_RESULTS = "results/stage3_v3/stage3_results.jsonl"
OUTPUT_FILE = "results/stage3_v3/analysis_output.txt"
EVAL = "results/eval_set_v3.jsonl"
PAIRS = "results/stage3_v3/evidence_pairs.jsonl"
SENSITIVITY = "results/stage3_v3/sensitivity_clusters.json"
ALPHA = 0.05
EXACT_MAX = 25
N_FLIPS = 1_000_000
PERM_SEED = 20261101
ONE_PER_CLUSTER_SEED = "stage3-analysis|one-per-cluster"
CONDITIONS = ("genuine", "misleading", "neutral")
PRIMARY = ("misleading", "baseline")
SECONDARY = [("genuine", "baseline"), ("neutral", "baseline"), ("misleading", "neutral")]
EXCLUDED_FROM_PRIMARY = "T1021.002"
ECE_BINS = 5
# post hoc (2026-11-08, after the results): T1021.002 clusters whose service was installed locally, not remotely
# (scripts/t1021_002_local_remote.py); reported only in the exploratory post hoc section
POST_HOC_LOCAL_INSTALL = {
    "T1021.002|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:04":
        "javamtsup, New-Service in a local elevated PowerShell on SCRANTON",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ---------------- data ----------------
def answers(path, evals, parser):
    """{condition: {event_uid: {"correct", "confidence", "valid"}}} from a results file, parsed from raw."""
    out = defaultdict(dict)
    for r in load(path):
        p = parser(r.get("raw"))
        valid = "predicted_technique" in p
        out[r["condition"]][r["event_uid"]] = {
            "correct": valid and p["predicted_technique"] == evals[r["event_uid"]]["technique_label"],
            "confidence": confidence(p) if valid else None, "valid": valid}
    return out


def baseline_arm(evals):
    return {u: {"correct": bool(e["baseline_correct"]), "confidence": confidence(e["baseline"]), "valid": True}
            for u, e in evals.items()}


def confidence(p):
    c = p.get("confidence")
    return float(c) if isinstance(c, (int, float)) and not isinstance(c, bool) and 0 <= c <= 100 else None


def cluster_sets(evals):
    with open(SENSITIVITY, encoding="utf-8") as f:
        sens = {c["cluster_id"] for c in json.load(f)["clusters"]}
    tech = {e["cluster_id"]: e["technique_label"] for e in evals.values()}
    allc = set(tech)
    no59 = {c for c in allc if tech[c] != "T1059.001"}
    return [("all", allc), ("excl. T1059.001", no59), ("all, without sensitivity", allc - sens),
            ("excl. T1059.001, without sensitivity", no59 - sens)]


def cluster_diffs(arm_a, arm_b, evals, clusters):
    """{cluster: (score_a, score_b)} as Fractions over the events answered in both arms."""
    by = defaultdict(list)
    for u in set(arm_a) & set(arm_b):
        c = evals[u]["cluster_id"]
        if c in clusters:
            by[c].append(u)
    return {c: (Fraction(sum(arm_a[u]["correct"] for u in us), len(us)),
                Fraction(sum(arm_b[u]["correct"] for u in us), len(us))) for c, us in by.items()}


# ---------------- test ----------------
def sign_flip_test(diffs):
    """Two-sided paired permutation test on the sum of the differences. Returns (p, method, k)."""
    nz = [d for d in diffs if d != 0]
    k = len(nz)
    if k == 0:
        return 1.0, "none (all differences zero)", 0
    scale = lcm(*(d.denominator for d in nz))
    ints = [int(d * scale) for d in nz]
    obs = abs(sum(ints))
    if k <= EXACT_MAX:
        dist = {0: 1}                                  # distribution of the flipped sum, by dynamic programming
        for v in ints:
            nxt = defaultdict(int)
            for s, n in dist.items():
                nxt[s + v] += n
                nxt[s - v] += n
            dist = nxt
        hits = sum(n for s, n in dist.items() if abs(s) >= obs)
        return hits / 2 ** k, f"exact ({k} non-zero clusters, {2 ** k:,} sign patterns)", k
    rng = np.random.default_rng(PERM_SEED)
    a = np.array(ints, dtype=np.int64)
    hits, done, batch = 0, 0, 50_000
    while done < N_FLIPS:
        m = min(batch, N_FLIPS - done)
        signs = rng.integers(0, 2, size=(m, k), dtype=np.int8) * 2 - 1
        hits += int((np.abs(signs @ a) >= obs).sum())
        done += m
    return (hits + 1) / (N_FLIPS + 1), f"Monte Carlo ({k} non-zero clusters, {N_FLIPS:,} sign flips, seed {PERM_SEED})", k


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def contrast_rows(arms, evals, clusters):
    """The primary and the three Holm-corrected secondary contrasts on one cluster set."""
    rows = []
    for a, b in [PRIMARY] + SECONDARY:
        cs = clusters - ({c for c in clusters if c.startswith(EXCLUDED_FROM_PRIMARY + "|")} if (a, b) == PRIMARY else set())
        cd = cluster_diffs(arms[a], arms[b], evals, cs)
        diffs = [x - y for x, y in cd.values()]
        p, method, k = sign_flip_test(diffs)
        mean_a = float(sum(x for x, _ in cd.values()) / len(cd)) if cd else float("nan")
        mean_b = float(sum(y for _, y in cd.values()) / len(cd)) if cd else float("nan")
        rows.append({"contrast": f"{a} vs {b}", "n": len(cd), "k": k, "mean_a": mean_a, "mean_b": mean_b,
                     "diff": float(sum(diffs) / len(diffs)) if diffs else float("nan"), "p": p, "method": method})
    for r, adj in zip(rows[1:], holm([r["p"] for r in rows[1:]])):
        r["p_holm"] = adj
    rows[0]["p_holm"] = None
    return rows


def print_rows(set_name, clusters, rows):
    print(f"\n[{set_name}: {len(clusters)} clusters]")
    print(f"  {'contrast':<24}{'clusters':>9}{'score A':>9}{'score B':>9}{'mean diff':>11}{'p':>9}{'p (Holm)':>10}  method")
    for r in rows:
        ph = "primary" if r["p_holm"] is None else f"{r['p_holm']:.4f}"
        print(f"  {r['contrast']:<24}{r['n']:>9}{r['mean_a']:>9.3f}{r['mean_b']:>9.3f}{r['diff']:>+11.3f}"
              f"{r['p']:>9.4f}{ph:>10}  {r['method']}")


def run_tests(arms, evals, title):
    print(f"\n{'=' * 100}\n{title}\n{'=' * 100}")
    contrasts = [PRIMARY] + SECONDARY
    results = {}
    for set_name, clusters in cluster_sets(evals):
        rows = contrast_rows(arms, evals, clusters)
        results[set_name] = rows
        print_rows(set_name, clusters, rows)
    print("\nConclusion rule: significant on the 63-cluster set (primary p < 0.05; secondary Holm p < 0.05) "
          "and the 40-cluster set agrees in direction.")
    for i, (a, b) in enumerate(contrasts):
        r63, r40 = results["all"][i], results["excl. T1059.001"][i]
        p63 = r63["p"] if r63["p_holm"] is None else r63["p_holm"]
        sgn = lambda x: (x > 0) - (x < 0)
        agree = sgn(r63["diff"]) == sgn(r40["diff"]) and sgn(r63["diff"]) != 0
        direction = "no difference" if sgn(r63["diff"]) == 0 else ("agree" if agree else "DISAGREE")
        print(f"  {a + ' vs ' + b:<24} direction 63: {r63['diff']:+.3f}  40: {r40['diff']:+.3f}  {direction:<14}"
              f"-> {'SUPPORTED' if p63 < ALPHA and agree else 'not supported'}")
    return results


# ---------------- descriptive ----------------
def transitions(arm, base, evals, events=None):
    us = [u for u in arm if events is None or u in events]
    corr = sum(not base[u]["correct"] and arm[u]["correct"] for u in us)
    reg = sum(base[u]["correct"] and not arm[u]["correct"] for u in us)
    by = defaultdict(list)
    for u in us:
        by[evals[u]["cluster_id"]].append(u)
    up = down = same = 0
    for c, xs in by.items():
        d = Fraction(sum(arm[u]["correct"] for u in xs), len(xs)) - Fraction(sum(base[u]["correct"] for u in xs), len(xs))
        up, down, same = up + (d > 0), down + (d < 0), same + (d == 0)
    return {"events": len(us), "corrections": corr, "regressions": reg, "unchanged": len(us) - corr - reg,
            "clusters": len(by), "cl_up": up, "cl_down": down, "cl_same": same,
            "acc_base": sum(base[u]["correct"] for u in us) / len(us) if us else float("nan"),
            "acc": sum(arm[u]["correct"] for u in us) / len(us) if us else float("nan")}


def calibration(arm, us):
    pts = [(arm[u]["confidence"] / 100, 1.0 if arm[u]["correct"] else 0.0) for u in us if arm[u]["confidence"] is not None]
    if not pts:
        return float("nan"), float("nan"), 0
    brier = sum((p - y) ** 2 for p, y in pts) / len(pts)
    bins = defaultdict(list)
    for p, y in pts:
        bins[min(int(p * ECE_BINS), ECE_BINS - 1)].append((p, y))
    ece = sum(len(b) / len(pts) * abs(sum(y for _, y in b) / len(b) - sum(p for p, _ in b) / len(b)) for b in bins.values())
    return brier, ece, len(pts)


def describe(arms, evals, title, events=None):
    base = arms["baseline"]
    print(f"\n{title}")
    if not any(u in arms[c] for c in CONDITIONS for u in (events if events is not None else arms[c])):
        print("  (no answers in this subset)")
        return
    print(f"  {'condition':<11}{'events':>7}{'corr.':>6}{'regr.':>6}{'unch.':>6}{'acc base':>9}{'acc':>6}"
          f"{'clusters':>9}{'up':>4}{'down':>5}{'same':>5}")
    for c in CONDITIONS:
        t = transitions(arms[c], base, evals, events)
        if t["events"]:
            print(f"  {c:<11}{t['events']:>7}{t['corrections']:>6}{t['regressions']:>6}{t['unchanged']:>6}"
                  f"{t['acc_base']:>9.3f}{t['acc']:>6.3f}{t['clusters']:>9}{t['cl_up']:>4}{t['cl_down']:>5}{t['cl_same']:>5}")


def report_descriptive(arms, evals, pairs, path):
    base = arms["baseline"]
    raw = load(path)
    print(f"\n{'=' * 100}\nDESCRIPTIVE (primary lenient parse unless stated)\n{'=' * 100}")
    describe(arms, evals, "Corrections (baseline wrong -> correct), regressions (correct -> wrong), unchanged; "
             "clusters whose score went up / down / stayed the same")
    print("\nConfidence and calibration (answers with a valid confidence; baseline on the same events)")
    print(f"  {'condition':<11}{'n':>5}{'left out':>9}{'conf base':>10}{'conf':>7}{'change':>8}{'Brier base':>11}"
          f"{'Brier':>7}{'ECE base':>9}{'ECE':>7}")
    for c in CONDITIONS:
        us = [u for u in arms[c] if arms[c][u]["confidence"] is not None and base[u]["confidence"] is not None]
        if not us:
            continue
        cb, ca = (sum(arm[u]["confidence"] for u in us) / len(us) for arm in (base, arms[c]))
        bb, eb, _ = calibration(base, us)
        ba, ea, _ = calibration(arms[c], us)
        print(f"  {c:<11}{len(us):>5}{len(arms[c]) - len(us):>9}{cb:>10.1f}{ca:>7.1f}{ca - cb:>+8.1f}"
              f"{bb:>11.3f}{ba:>7.3f}{eb:>9.3f}{ea:>7.3f}")
    print(f"  (left out = answers without a valid confidence, in this condition or its baseline; ECE: {ECE_BINS} "
          "equal-width confidence bins; Brier and ECE treat confidence/100 as P(answer correct))")

    print("\nNon-JSON rate (no valid JSON object with predicted_technique)")
    print(f"  {'condition':<11}{'answers':>8}{'lenient (primary)':>19}{'strict':>14}{'max_tokens stops':>18}")
    for c in CONDITIONS:
        rs = [r for r in raw if r["condition"] == c]
        if not rs:
            continue
        nl = sum("predicted_technique" not in parse_lenient(r.get("raw")) for r in rs)
        ns = sum("predicted_technique" not in parse_strict(r.get("raw")) for r in rs)
        mt = sum(r.get("stop_reason") == "max_tokens" for r in rs)
        print(f"  {c:<11}{len(rs):>8}{nl:>10} ({nl / len(rs) * 100:4.1f}%){ns:>7} ({ns / len(rs) * 100:4.1f}%){mt:>12}")

    t59 = {u for u, e in evals.items() if e["technique_label"] == "T1059.001"}
    describe(arms, evals, "T1059.001 alone (descriptive, no test)", events=t59)

    for name, flag in (("same log channel as the original", True), ("different log channel", False)):
        print(f"\nEvidence from the {name} (genuine and misleading only)")
        print(f"  {'condition':<11}{'events':>7}{'corr.':>6}{'regr.':>6}{'unch.':>6}{'acc base':>9}{'acc':>6}")
        for c in ("genuine", "misleading"):
            sel = {r["event_uid"] for r in pairs if r["condition"] == c and r.get("evidence_text") and r["same_channel"] is flag}
            t = transitions({u: v for u, v in arms[c].items() if u in sel}, base, evals)
            if t["events"]:
                print(f"  {c:<11}{t['events']:>7}{t['corrections']:>6}{t['regressions']:>6}{t['unchanged']:>6}"
                      f"{t['acc_base']:>9.3f}{t['acc']:>6.3f}")


def exploratory_confidence(arms, evals):
    """PR4 exploratory question: under misleading evidence, baseline confidence of the events that regressed
    vs those that stayed correct (event level, baseline-correct events only)."""
    base, mis = arms["baseline"], arms["misleading"]
    groups = {"regressed": [], "stayed correct": []}
    for u in mis:
        if base[u]["correct"] and base[u]["confidence"] is not None:
            groups["stayed correct" if mis[u]["correct"] else "regressed"].append(base[u]["confidence"])
    print(f"\n{'=' * 100}\nEXPLORATORY: baseline confidence of misleading-condition events, by outcome (descriptive)\n{'=' * 100}")
    print(f"  {'group':<16}{'n':>5}{'mean':>8}{'median':>8}")
    for g, xs in groups.items():
        print(f"  {g:<16}{len(xs):>5}" + (f"{np.mean(xs):>8.1f}{np.median(xs):>8.1f}" if xs else f"{'-':>8}{'-':>8}"))
    print("  (events whose baseline answer was correct; 'regressed' = scored not correct under misleading evidence)")


def primary_row(arms, evals, clusters, label):
    cs = {c for c in clusters if not c.startswith(EXCLUDED_FROM_PRIMARY + "|")}
    cd = cluster_diffs(arms[PRIMARY[0]], arms[PRIMARY[1]], evals, cs)
    diffs = [x - y for x, y in cd.values()]
    p, method, _ = sign_flip_test(diffs)
    mean = lambda i: float(sum(v[i] for v in cd.values()) / len(cd)) if cd else float("nan")
    d = float(sum(diffs) / len(diffs)) if diffs else float("nan")
    print(f"  {label:<34}{len(cd):>9}{mean(0):>9.3f}{mean(1):>9.3f}{d:>+11.3f}{p:>9.4f}  {method}")


def sensitivity(arms, evals):
    """Primary contrast (misleading vs baseline, all clusters) under (a) one event per cluster drawn with
    ONE_PER_CLUSTER_SEED and (b) each technique left out in turn."""
    allc = cluster_sets(evals)[0][1]
    print(f"\n{'=' * 100}\nSENSITIVITY: primary contrast (misleading vs baseline, all clusters)\n{'=' * 100}")
    print(f"  {'variant':<34}{'clusters':>9}{'score A':>9}{'score B':>9}{'mean diff':>11}{'p':>9}  method")
    primary_row(arms, evals, allc, "main analysis")
    rng = random.Random(ONE_PER_CLUSTER_SEED)
    both = sorted(set(arms[PRIMARY[0]]) & set(arms[PRIMARY[1]]))
    by = defaultdict(list)
    for u in both:
        by[evals[u]["cluster_id"]].append(u)
    keep = {rng.choice(by[c]) for c in sorted(by)}
    one = {a: {u: v for u, v in arm.items() if u in keep} for a, arm in arms.items()}
    primary_row(one, evals, allc, f"(a) one event per cluster")
    for t in sorted({e["technique_label"] for e in evals.values()} - {EXCLUDED_FROM_PRIMARY}):
        primary_row(arms, evals, {c for c in allc if not c.startswith(t + "|")}, f"(b) without {t}")
    print(f"  ((a) seed '{ONE_PER_CLUSTER_SEED}'; {EXCLUDED_FROM_PRIMARY} has no misleading condition and is never in "
          "the primary contrast. Cap 5 and the reboot-window sensitivity are not run: they need new calls or a new pool)")


def post_hoc_local_install(arms, evals):
    """POST HOC (2026-11-08, decided after the Stage 3 results): every test again without the T1021.002 clusters
    that scripts/t1021_002_local_remote.py shows to be a local service install (POST_HOC_LOCAL_INSTALL)."""
    print(f"\n{'=' * 100}\nPOST HOC, EXPLORATORY (2026-11-08, after the results): without the T1021.002 clusters that are "
          f"a local service install\n{'=' * 100}")
    for c, why in POST_HOC_LOCAL_INSTALL.items():
        print(f"  left out: {c}  ({why})")
    for set_name, clusters in cluster_sets(evals):
        cs = clusters - set(POST_HOC_LOCAL_INSTALL)
        print_rows(f"{set_name}, without local install", cs, contrast_rows(arms, evals, cs))
    print(f"  (lenient parse; Holm within each set as in the main tests. {EXCLUDED_FROM_PRIMARY} is never in the primary "
          "contrast, so only the contrasts that include it can change. Not part of the evaluation plan written before Stage 3.)")


def main(path):
    evals = {e["event_uid"]: e for e in load(EVAL)}
    pairs = load(PAIRS)
    rows = load(path)
    print(f"Stage 3 analysis of {path}: {len(rows)} answers "
          + ", ".join(f"{c} {sum(r['condition'] == c for r in rows)}" for c in CONDITIONS)
          + f"; {len({r['cluster_id'] for r in rows})} clusters with an answer")
    lenient = {"baseline": baseline_arm(evals), **answers(path, evals, parse_lenient)}
    strict = {"baseline": baseline_arm(evals), **answers(path, evals, parse_strict)}
    for c in CONDITIONS:
        lenient.setdefault(c, {})
        strict.setdefault(c, {})
    run_tests(lenient, evals, "TESTS: primary lenient parse")
    run_tests(strict, evals, "TESTS: strict parse (sensitivity analysis)")
    sensitivity(lenient, evals)
    report_descriptive(lenient, evals, pairs, path)
    exploratory_confidence(lenient, evals)
    post_hoc_local_install(lenient, evals)


class Tee:
    """Writes everything printed to the terminal and to a file."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else FULL_RESULTS
    # the output is also saved to OUTPUT_FILE when the full results are analysed (not for pilot files)
    if os.path.abspath(path) == os.path.abspath(FULL_RESULTS):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
            sys.stdout = Tee(sys.__stdout__, fh)
            try:
                main(path)
            finally:
                sys.stdout = sys.__stdout__
        print(f"\n(output saved to {OUTPUT_FILE})")
    else:
        main(path)
