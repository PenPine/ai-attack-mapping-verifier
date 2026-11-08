"""
scripts/power_table.py
Power of the Stage 3 paired test (PR4 Table 7 settings). No API calls.

Each cluster is one binary unit (baseline correct or wrong) and changes independently:
  misleading  breaks BREAK of the correct clusters (15%, 25%, 35%) and also fixes 2% of the wrong ones
  genuine     fixes FIX of the wrong clusters (50%, 80%) and also breaks 3% of the correct ones
Test: exact two-sided McNemar on the discordant pairs (pr4_checks.exact_mcnemar), alpha = 0.05.
The table reports exact power (sum over the two binomials); a 20,000-trial simulation (fixed seed) is
shown alongside as a check.
The misleading test leaves out T1021.002 (no misleading condition).

Run from the project root:  python scripts/power_table.py
The PR4 counts are run first and compared with the PR4 Table 7 values; the v3 table is only written if
every PR4 cell is reproduced. PR4 Table 7 is itself a rounded 20,000-trial simulation with an unknown seed, so a
cell counts as reproduced when the exact power lies within 0.5 points (rounding) + 3 Monte Carlo standard
errors of the PR4 value (about 1 point at 50% power, less near 0% or 100%).
Outputs: results/tables_v3/pr4/power_table.md, results/tables_v3/v3/power_table.md
"""
import os
import sys
from math import comb

import numpy as np

sys.path.insert(0, ".")
from pr4_checks import exact_mcnemar

ALPHA = 0.05
TRIALS = 20_000
SEED = 20261028
MIS_BREAK, MIS_FIX = (0.15, 0.25, 0.35), 0.02
GEN_FIX, GEN_BREAK = (0.50, 0.80), 0.03

# (correct, wrong) clusters: genuine test, misleading test (without T1021.002)
COUNTS = {
    "pr4": {"all": {"label": "66 clusters", "genuine": (54, 12), "misleading": (46, 12)},
            "excl": {"label": "43 clusters, excl. T1059.001", "genuine": (36, 7), "misleading": (28, 7)}},
    "v3": {"all": {"label": "63 clusters", "genuine": (54, 9), "misleading": (46, 9)},
           "excl": {"label": "40 clusters, excl. T1059.001", "genuine": (36, 4), "misleading": (28, 4)}},
}
PR4_TABLE7 = {"all": [63, 96, 100, 18, 65], "excl": [21, 69, 94, 2, 19]}   # misleading 15/25/35, genuine 50/80


def scenarios():
    return ([("misleading", f"misleading breaks {int(b * 100)}%", b, MIS_FIX) for b in MIS_BREAK]
            + [("genuine", f"genuine fixes {int(f * 100)}%", GEN_BREAK, f) for f in GEN_FIX])


def reject_table(n_correct, n_wrong):
    """reject[b, c] for b broken (of the correct) and c fixed (of the wrong)."""
    return np.array([[exact_mcnemar(b, c) <= ALPHA for c in range(n_wrong + 1)] for b in range(n_correct + 1)])


def binom_pmf(n, p):
    return np.array([comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)])


def power(n_correct, n_wrong, p_break, p_fix, rng):
    rej = reject_table(n_correct, n_wrong)
    b = rng.binomial(n_correct, p_break, TRIALS)
    c = rng.binomial(n_wrong, p_fix, TRIALS)
    sim = rej[b, c].mean()
    exact = float(binom_pmf(n_correct, p_break) @ rej @ binom_pmf(n_wrong, p_fix))
    return sim, exact


def run(version):
    rng = np.random.default_rng(SEED)
    res = {}
    for subset, cfg in COUNTS[version].items():
        res[subset] = [(name, cfg[test], *power(*cfg[test], pb, pf, rng)) for test, name, pb, pf in scenarios()]
    return res


def write(version, res, check=None):
    lines = [f"# Power of the Stage 3 paired test ({version} counts)\n",
             "Values are exact power: the rejection probability summed over both binomials, no simulation error. "
             f"Exact two-sided McNemar on the discordant pairs, alpha = {ALPHA}. The last column is a Monte Carlo "
             f"check of the exact value ({TRIALS:,} trials, seed {SEED}). "
             "Each cluster is one binary unit and changes independently. Misleading also fixes "
             f"{int(MIS_FIX * 100)}% of wrong clusters; genuine also breaks {int(GEN_BREAK * 100)}% of correct ones. "
             "The misleading test leaves out T1021.002.\n"]
    for subset, cfg in COUNTS[version].items():
        lines.append(f"## {cfg['label']}\n")
        lines.append(f"Baseline counts used: genuine / neutral {cfg['genuine'][0]} correct / {cfg['genuine'][1]} wrong; "
                     f"misleading {cfg['misleading'][0]} correct / {cfg['misleading'][1]} wrong.\n")
        head = (["scenario", "correct / wrong", "exact power"] + (["PR4 Table 7"] if check else [])
                + [f"simulation check ({TRIALS:,} trials)"])
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "---|" * len(head))
        for k, (name, (nc, nw), sim, exact) in enumerate(res[subset]):
            row = [name, f"{nc} / {nw}", f"{exact * 100:.1f}%"]
            if check:
                row.append(f"{check[subset][k]}%")
            row.append(f"{sim * 100:.1f}%")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    path = f"results/tables_v3/{version}/power_table.md"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"wrote {path}\n")


if __name__ == "__main__":
    pr4 = run("pr4")
    write("pr4", pr4, PR4_TABLE7)
    bad = []
    for s in pr4:
        for k, (name, _, sim, exact) in enumerate(pr4[s]):
            p = PR4_TABLE7[s][k] / 100
            tol = 0.5 + 3 * 100 * max(p * (1 - p), 1 / TRIALS) ** 0.5 / TRIALS ** 0.5
            off = abs(exact * 100 - PR4_TABLE7[s][k])
            print(f"  check {s:<5}{name:<24} exact {exact * 100:5.1f}  PR4 {PR4_TABLE7[s][k]:>3}  "
                  f"|diff| {off:.2f}  tolerance {tol:.2f}  {'ok' if off <= tol else 'NOT REPRODUCED'}")
            if off > tol:
                bad.append((s, name))
    if bad:
        print("PR4 Table 7 NOT reproduced; v3 table not written:", bad)
        sys.exit(1)
    print("PR4 Table 7 reproduced (every cell within tolerance). Running v3 counts.\n")
    write("v3", run("v3"))
