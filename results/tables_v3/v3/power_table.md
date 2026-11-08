# Power of the Stage 3 paired test (v3 counts)

Values are exact power: the rejection probability summed over both binomials, no simulation error. Exact two-sided McNemar on the discordant pairs, alpha = 0.05. The last column is a Monte Carlo check of the exact value (20,000 trials, seed 20261028). Each cluster is one binary unit and changes independently. Misleading also fixes 2% of wrong clusters; genuine also breaks 3% of correct ones. The misleading test leaves out T1021.002.

## 63 clusters

Baseline counts used: genuine / neutral 54 correct / 9 wrong; misleading 46 correct / 9 wrong.

| scenario | correct / wrong | exact power | simulation check (20,000 trials) |
|---|---|---|---|
| misleading breaks 15% | 46 / 9 | 65.0% | 66.0% |
| misleading breaks 25% | 46 / 9 | 97.2% | 97.2% |
| misleading breaks 35% | 46 / 9 | 99.9% | 99.9% |
| genuine fixes 50% | 54 / 9 | 5.5% | 5.6% |
| genuine fixes 80% | 54 / 9 | 31.7% | 31.5% |

## 40 clusters, excl. T1059.001

Baseline counts used: genuine / neutral 36 correct / 4 wrong; misleading 28 correct / 4 wrong.

| scenario | correct / wrong | exact power | simulation check (20,000 trials) |
|---|---|---|---|
| misleading breaks 15% | 28 / 4 | 22.1% | 22.5% |
| misleading breaks 25% | 28 / 4 | 71.0% | 70.7% |
| misleading breaks 35% | 28 / 4 | 94.9% | 95.1% |
| genuine fixes 50% | 36 / 4 | 0.0% | 0.0% |
| genuine fixes 80% | 36 / 4 | 0.0% | 0.0% |
