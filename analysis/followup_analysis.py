"""
analysis/followup_analysis.py
EXPLORATORY, POST HOC (planned 2026-11-08 after the Stage 3 results; results/CHANGELOG.md). Analysis of a
follow-up run with the closing line STAGE3_FOLLOWUP_CLOSING, for the misleading pairs (followup_results.jsonl)
or the genuine pairs (followup_genuine_results.jsonl). No API calls. Does not change the main analysis: it reads
stage3_results.jsonl only for comparison.

Reports: calls, API failures, stop reasons, tokens and cost; corrections / regressions against the baseline at
event and cluster level; the exact paired sign-flip test of follow-up vs baseline (and vs the original run) on the
four cluster sets (misleading: 55, 32, 52, 29 without T1021.002; genuine: 59, 40, 56, 37), lenient and strict;
for each original correction and regression whether it still holds, and new changes; the full reasoning of every
follow-up change and the follow-up reasoning of every original change; non-JSON rates; confidence.

Run from the project root:  python analysis/followup_analysis.py [misleading|genuine]   (default misleading)
Output also saved to results/stage3_v3/followup_analysis_output.txt (misleading) or
results/stage3_v3/followup_genuine_analysis_output.txt (genuine).
"""
import os
import sys
from collections import Counter

sys.path.insert(0, ".")
sys.path.insert(0, "analysis")
import stage3_analysis as A                                     # noqa: E402
from run_stage3 import parse_lenient, parse_strict             # noqa: E402

RUNS = {
    "misleading": ("results/stage3_v3/followup_results.jsonl", "results/stage3_v3/followup_api_failures.jsonl",
                   "results/stage3_v3/followup_analysis_output.txt"),
    "genuine": ("results/stage3_v3/followup_genuine_results.jsonl",
                "results/stage3_v3/followup_genuine_api_failures.jsonl",
                "results/stage3_v3/followup_genuine_analysis_output.txt"),
}
ORIGINAL = A.FULL_RESULTS
PRICE_IN, PRICE_OUT = 3 / 1e6, 15 / 1e6
LABEL = "EXPLORATORY, POST HOC"


def main(cond):
    followup, failures, _ = RUNS[cond]
    evals = {e["event_uid"]: e for e in A.load(A.EVAL)}
    rows = A.load(followup)
    fails = A.load(failures) if os.path.exists(failures) else []
    print(f"{LABEL}: {cond}-condition follow-up, closing line names the original event ({followup}). "
          f"Not part of the main analysis.\n")

    ti, to = sum(r["input_tokens"] for r in rows), sum(r["output_tokens"] for r in rows)
    print("RUN")
    print(f"  answers {len(rows)} (distinct pairs {len({r['pair_id'] for r in rows})}); API failures logged: {len(fails)}")
    print(f"  stop reasons: {dict(Counter(r['stop_reason'] for r in rows))}; models: {dict(Counter(r['model'] for r in rows))}")
    print(f"  retries: {sum(r['attempts'] > 1 for r in rows)} answers needed more than one attempt")
    print(f"  tokens: input {ti:,}, output {to:,} (max output {max(r['output_tokens'] for r in rows)}); "
          f"cost ${ti * PRICE_IN + to * PRICE_OUT:.2f} (${ti * PRICE_IN:.2f} input + ${to * PRICE_OUT:.2f} output)")

    base = A.baseline_arm(evals)
    fu = A.answers(followup, evals, parse_lenient)[cond]
    fu_s = A.answers(followup, evals, parse_strict)[cond]
    orig = A.answers(ORIGINAL, evals, parse_lenient)[cond]
    orig_name = f"original {cond}"

    print(f"\nAGAINST THE BASELINE ({LABEL})")
    print(f"  {'arm':<22}{'events':>7}{'corr.':>6}{'regr.':>6}{'unch.':>6}{'acc base':>9}{'acc':>6}"
          f"{'clusters':>9}{'up':>4}{'down':>5}{'same':>5}")
    for name, arm in (("follow-up", fu), ("follow-up (strict)", fu_s), (orig_name, orig)):
        t = A.transitions(arm, base, evals)
        print(f"  {name:<22}{t['events']:>7}{t['corrections']:>6}{t['regressions']:>6}{t['unchanged']:>6}"
              f"{t['acc_base']:>9.3f}{t['acc']:>6.3f}{t['clusters']:>9}{t['cl_up']:>4}{t['cl_down']:>5}{t['cl_same']:>5}")

    sets = dict(A.cluster_sets(evals))
    if cond == "misleading":
        restrict = lambda cs: {c for c in cs if not c.startswith(A.EXCLUDED_FROM_PRIMARY + "|")}
    else:
        restrict = lambda cs: cs
    print(f"\nPERMUTATION TESTS ({LABEL}; exact paired sign flip on cluster scores, two-sided, no correction)")
    print(f"  {'contrast':<34}{'set':<38}{'clusters':>9}{'score A':>9}{'score B':>9}{'mean diff':>11}{'p':>9}  method")
    for a_name, a, b_name, b in (("follow-up", fu, "baseline", base), ("follow-up (strict)", fu_s, "baseline", base),
                                 ("follow-up", fu, orig_name, orig)):
        for set_name in ("all", "excl. T1059.001", "all, without sensitivity", "excl. T1059.001, without sensitivity"):
            cd = A.cluster_diffs(a, b, evals, restrict(sets[set_name]))
            diffs = [x - y for x, y in cd.values()]
            p, method, _ = A.sign_flip_test(diffs)
            ma = float(sum(x for x, _ in cd.values()) / len(cd))
            mb = float(sum(y for _, y in cd.values()) / len(cd))
            print(f"  {a_name + ' vs ' + b_name:<34}{set_name:<38}{len(cd):>9}{ma:>9.3f}{mb:>9.3f}"
                  f"{float(sum(diffs) / len(diffs)):>+11.3f}{p:>9.4f}  {method}")

    fu_rows = {r["event_uid"]: r for r in rows}
    orig_rows = {r["event_uid"]: r for r in A.load(ORIGINAL) if r["condition"] == cond}
    pred = lambda r: parse_lenient(r["raw"]).get("predicted_technique", "NOT JSON")
    changed_vs_base = lambda arm: {u: ("regression" if base[u]["correct"] else "correction")
                                   for u in arm if base[u]["correct"] != arm[u]["correct"]}
    orig_ch, fu_ch = changed_vs_base(orig), changed_vs_base(fu)

    print(f"\nTHE {len(orig_ch)} ORIGINAL {cond.upper()} CHANGES UNDER THE FOLLOW-UP ({LABEL})")
    print(f"  {'event':<18}{'label':<11}{'original':<12}{'baseline':<11}{'original':<11}{'follow-up':<11}status")
    for u in sorted(orig_ch, key=lambda u: (orig_ch[u], u)):
        e, kind = evals[u], orig_ch[u]
        holds = fu_ch.get(u) == kind
        status = (f"still {'regresses' if kind == 'regression' else 'corrects'}" if holds
                  else f"no longer {'regresses' if kind == 'regression' else 'corrects'}")
        print(f"  {u:<18}{e['technique_label']:<11}{kind:<12}{e['baseline']['predicted_technique']:<11}"
              f"{pred(orig_rows[u]):<11}{pred(fu_rows[u]):<11}{status}")
    for kind in ("regression", "correction"):
        n_o = sum(v == kind for v in orig_ch.values())
        n_h = sum(v == kind and fu_ch.get(u) == kind for u, v in orig_ch.items())
        print(f"  original {kind}s that still hold: {n_h} of {n_o}")
    new = {u: k for u, k in fu_ch.items() if u not in orig_ch}
    print(f"  new changes against the baseline, not in the original run: {len(new)}")
    for u, k in sorted(new.items()):
        print(f"    new {k}: {u} label {evals[u]['technique_label']} baseline {evals[u]['baseline']['predicted_technique']} "
              f"original {pred(orig_rows[u])} follow-up {pred(fu_rows[u])}")
    differ = [u for u in fu if pred(fu_rows[u]) != pred(orig_rows[u])]
    print(f"  answers whose predicted technique differs between follow-up and original: {len(differ)}")
    for u in differ:
        print(f"    {u} label {evals[u]['technique_label']}: original {pred(orig_rows[u])} -> follow-up {pred(fu_rows[u])}")

    def show(u, tag):
        e, r = evals[u], fu_rows[u]
        p = parse_lenient(r["raw"])
        print(f"\n  {u}  label {e['technique_label']}  decoy {e['decoy_technique']}  baseline "
              f"{e['baseline']['predicted_technique']} ({e['baseline']['confidence']})  original {pred(orig_rows[u])}"
              f"  -> follow-up {p.get('predicted_technique', 'NOT JSON')} ({p.get('confidence')})  [{tag}]")
        print(f"  reasoning: {p.get('reasoning') or r['raw']}")
        start = r["raw"].rfind('{"predicted_technique"')        # the answer object, not a "{" in the prose
        prose = r["raw"][:start].strip() if start > 0 else ""
        if prose:
            print(f"  text before the JSON: {prose}")

    print(f"\nFULL REASONING OF EVERY FOLLOW-UP CHANGE AGAINST THE BASELINE ({LABEL})")
    if not fu_ch:
        print("  (none)")
    for u in sorted(fu_ch, key=lambda u: (fu_ch[u], u)):
        show(u, f"follow-up {fu_ch[u]}, {'also in the original run' if u in orig_ch else 'NEW'}")

    print(f"\nFOLLOW-UP REASONING OF EVERY ORIGINAL CHANGE ({LABEL})")
    for u in sorted(orig_ch, key=lambda u: (orig_ch[u], u)):
        show(u, f"original {orig_ch[u]}; follow-up {fu_ch.get(u, 'unchanged against the baseline')}")

    print(f"\nNON-JSON RATE AND CONFIDENCE ({LABEL})")
    n = len(rows)
    nl = sum("predicted_technique" not in parse_lenient(r["raw"]) for r in rows)
    ns = sum("predicted_technique" not in parse_strict(r["raw"]) for r in rows)
    ol = sum("predicted_technique" not in parse_lenient(r["raw"]) for r in orig_rows.values())
    os_ = sum("predicted_technique" not in parse_strict(r["raw"]) for r in orig_rows.values())
    no = len(orig_rows)
    print(f"  follow-up: lenient {nl} ({nl / n * 100:.1f}%), strict {ns} ({ns / n * 100:.1f}%)   "
          f"{orig_name}: lenient {ol} ({ol / no * 100:.1f}%), strict {os_} ({os_ / no * 100:.1f}%)")
    for name, arm in (("follow-up", fu), (orig_name, orig)):
        us = [u for u in arm if arm[u]["confidence"] is not None and base[u]["confidence"] is not None]
        cb = sum(base[u]["confidence"] for u in us) / len(us)
        ca = sum(arm[u]["confidence"] for u in us) / len(us)
        bb, eb, _ = A.calibration(base, us)
        ba, ea, _ = A.calibration(arm, us)
        print(f"  {name:<20} n {len(us)} (left out {len(arm) - len(us)}): confidence {cb:.1f} -> {ca:.1f} ({ca - cb:+.1f}); "
              f"Brier {bb:.3f} -> {ba:.3f}; ECE {eb:.3f} -> {ea:.3f}")


if __name__ == "__main__":
    cond = sys.argv[1] if len(sys.argv) > 1 else "misleading"
    out_file = RUNS[cond][2]
    with open(out_file, "w", encoding="utf-8") as fh:
        sys.stdout = A.Tee(sys.__stdout__, fh)
        try:
            main(cond)
        finally:
            sys.stdout = sys.__stdout__
    print(f"\n(output saved to {out_file})")
