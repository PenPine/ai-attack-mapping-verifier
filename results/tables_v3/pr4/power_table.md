# Power of the Stage 3 paired test (pr4 counts)

Values are exact power: the rejection probability summed over both binomials, no simulation error. Exact two-sided McNemar on the discordant pairs, alpha = 0.05. The last column is a Monte Carlo check of the exact value (20,000 trials, seed 20261028). Each cluster is one binary unit and changes independently. Misleading also fixes 2% of wrong clusters; genuine also breaks 3% of correct ones. The misleading test leaves out T1021.002.

## 66 clusters

Baseline counts used: genuine / neutral 54 correct / 12 wrong; misleading 46 correct / 12 wrong.

| scenario | correct / wrong | exact power | PR4 Table 7 | simulation check (20,000 trials) |
|---|---|---|---|---|
| misleading breaks 15% | 46 / 12 | 63.2% | 63% | 64.0% |
| misleading breaks 25% | 46 / 12 | 96.6% | 96% | 96.6% |
| misleading breaks 35% | 46 / 12 | 99.9% | 100% | 99.9% |
| genuine fixes 50% | 54 / 12 | 18.6% | 18% | 18.6% |
| genuine fixes 80% | 54 / 12 | 64.9% | 65% | 64.8% |

## 43 clusters, excl. T1059.001

Baseline counts used: genuine / neutral 36 correct / 7 wrong; misleading 28 correct / 7 wrong.

| scenario | correct / wrong | exact power | PR4 Table 7 | simulation check (20,000 trials) |
|---|---|---|---|---|
| misleading breaks 15% | 28 / 7 | 21.0% | 21% | 21.5% |
| misleading breaks 25% | 28 / 7 | 69.0% | 69% | 68.4% |
| misleading breaks 35% | 28 / 7 | 94.0% | 94% | 94.2% |
| genuine fixes 50% | 36 / 7 | 2.1% | 2% | 2.1% |
| genuine fixes 80% | 36 / 7 | 19.3% | 19% | 18.6% |
