# Table 3. Noise floor and masking ablation (v3 pool, one event per cluster)

|  | Correct (all, n=63) | Lost / gained | exact McNemar p | Correct (excl. T1059.001, n=40) | Lost / gained | exact McNemar p | Answers that differ from the baseline |
|---|---|---|---|---|---|---|---|
| Baseline (stored) | 55/63 (87%) |  |  | 36/40 (90%) |  |  |  |
| Noise floor: same prompt, repeated | 54/63 (86%) | 1 / 0 | 1.000 | 36/40 (90%) | 0 / 0 | 1.000 | 1 of 63 |
| Mask 1: event-type cues hidden | 54/63 (86%) | 4 / 3 | 1.000 | 34/40 (85%) | 3 / 1 | 0.625 | 7 of 63 |
| Mask 2: event-type cues + process/tool names hidden | 52/63 (83%) | 6 / 3 | 0.508 | 32/40 (80%) | 5 / 1 | 0.219 | 9 of 61 (2 had no valid answer) |
| Mask 2, lenient parsing (sensitivity) | 52/63 (83%) | 6 / 3 | 0.508 | 32/40 (80%) | 5 / 1 | 0.219 | 10 of 62 (1 had no valid answer) |

n = 63 in every row: the PR4 sample of 66 clusters minus the 3 clusters removed in v3 (no re-sampling, no new runs). An answer that is not valid JSON counts as not correct. Lost = correct in the baseline, not correct in the check; gained = the reverse. Answers that differ: valid answers naming a different technique (or NONE) than the stored baseline answer, out of the valid answers. Answers that were not valid JSON: noise 0, mask 1 0, mask 2 2. Lenient parsing (take the JSON object that follows some prose) changes only the Mask 2 row, so it is shown for Mask 2 only.
