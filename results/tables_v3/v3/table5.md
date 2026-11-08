# Table 5. Event ID lookup baseline vs the LLM (v3 pool)

|  | event level | cluster level | predictions decided by a tie (clusters) |
|---|---|---|---|
| LLM baseline | 86.5% | 85.7% |  |
| Event ID lookup, in-sample (ceiling) | 98.3% | 92.1% | 0 (0) |
| Event ID lookup, leave-one-cluster | 86.5% | 89.1% | 2 (1) |
|   same, ties resolved to the true label (upper bound) | 87.2% | 90.7% | 2 (1) |

Scored events: 288; clusters: 63. Lookup = majority technique label per Event ID. Leave-one-cluster builds the lookup without the cluster being predicted. Unseen Event IDs and ties both get NONE (counted wrong); the upper-bound row resolves each tie to the true label.

Ties in the leave-one-cluster lookup:
- left out T1053.005|schtask_create_2020-12-1907003032.json|2020-12-19 12:00 (2 events): Event ID 1 counts {"T1053.005": 2, "T1059.003": 2} -> NONE (true label T1053.005)

Cluster-level accuracy by technique

| technique | clusters | LLM | lookup in-sample | lookup leave-one-cluster | upper bound |
|---|---|---|---|---|---|
| T1003.001 | 6 | 100% | 100% | 100% | 100% |
| T1003.006 | 3 | 100% | 100% | 100% | 100% |
| T1021.002 | 8 | 100% | 100% | 100% | 100% |
| T1053.005 | 3 | 100% | 100% | 67% | 100% |
| T1055 | 5 | 80% | 100% | 100% | 100% |
| T1059.001 | 23 | 79% | 100% | 100% | 100% |
| T1059.003 | 2 | 100% | 0% | 0% | 0% |
| T1546.003 | 6 | 100% | 100% | 100% | 100% |
| T1547.001 | 3 | 100% | 0% | 0% | 0% |
| T1562.002 | 4 | 17% | 100% | 78% | 78% |

Event IDs that carry more than one technique label (the lookup cannot separate these):
- Event ID 13: T1562.002: 33, T1547.001: 3
- Event ID 1: T1053.005: 4, T1059.003: 2
