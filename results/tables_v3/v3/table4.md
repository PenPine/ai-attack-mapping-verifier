# Table 4. Sensitivity of the cluster definition to the time window (v3 pool)

| window | clusters | excl. T1059.001 | singletons | accuracy (all) | accuracy (excl.) | correct/wrong (all) | correct/wrong (excl.) |
|---|---|---|---|---|---|---|---|
| 30 s | 71 | 40 | 37 | 86.0% | 89.2% | 61/10 | 36/4 |
| 60 s (original) | 63 | 40 | 36 | 85.7% | 89.2% | 54/9 | 36/4 |
| 120 s | 51 | 39 | 27 | 86.3% | 89.0% | 44/7 | 35/4 |
| 300 s | 41 | 35 | 22 | 85.7% | 87.7% | 35/6 | 31/4 |

Clusters per technique

| technique | 30 s | 60 s | 120 s | 300 s |
|---|---|---|---|---|
| T1003.001 | 6 | 6 | 6 | 6 |
| T1003.006 | 3 | 3 | 3 | 3 |
| T1021.002 | 8 | 8 | 7 | 6 |
| T1053.005 | 3 | 3 | 3 | 3 |
| T1055 | 5 | 5 | 5 | 5 |
| T1059.001 | 31 | 23 | 12 | 6 |
| T1059.003 | 2 | 2 | 2 | 2 |
| T1546.003 | 6 | 6 | 6 | 4 |
| T1547.001 | 3 | 3 | 3 | 2 |
| T1562.002 | 4 | 4 | 4 | 4 |

Cluster = same technique label + same source file + same W-second bucket; 60 s is the definition used everywhere else. Accuracy is cluster-level; correct/wrong rounds the summed cluster shares.
