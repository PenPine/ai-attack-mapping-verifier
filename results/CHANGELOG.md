# results/ changelog

## v3 (Progress Report 5), 2026-10-27

**Rule fix.** The T1059.003 extraction rule (`extraction/config.py`) matched any ParentImage
*containing* `cmd.exe`, so `dsregcmd.exe` matched. It now requires the parent basename to be exactly
`cmd.exe` (case-insensitive). Cleaning rule R2 (`clean_pool.py`) had the same substring problem
(`endswith("cmd.exe")`, `"conhost.exe" in image`) and now requires the image basename to be in
{`cmd.exe`, `conhost.exe`}. The R2 change alone removes nothing; all three removals come from the
extraction fix.

**Pool: 292 events / 66 clusters -> 289 events / 63 clusters.** Exactly 3 events removed, none added.
All three are T1059.003, parent `C:\Windows\System32\dsregcmd.exe`, image `conhost.exe`, from
`apt29_evals_day1_manual_2020-05-01225525.json`; each was the only event in its cluster.

| event_uid          | cluster_id (minute)                                               |
|--------------------|-------------------------------------------------------------------|
| `7907851ddc470a80` | `T1059.003\|apt29_evals_day1_manual_2020-05-01225525.json\|2020-05-02 03:06` |
| `abc5f99f17f83669` | `T1059.003\|apt29_evals_day1_manual_2020-05-01225525.json\|2020-05-02 03:24` |
| `078205eeae51f4f2` | `T1059.003\|apt29_evals_day1_manual_2020-05-01225525.json\|2020-05-02 03:25` |

**New files** (the PR4 files `pool_clean.jsonl`, `excluded.jsonl`, `baseline_clean.jsonl` and
`checks_*` are unchanged):
- `pool_clean_v3.jsonl`, `excluded_v3.jsonl`, `baseline_clean_v3.jsonl`, written by `clean_pool.py`
- `tables_v3/`, written by `scripts/recompute_tables_v3.py` from the existing baseline predictions
  (no API calls). The noise / mask1 / mask2 checks reuse the existing sample and runs with the
  3 removed clusters dropped (66 -> 63); nothing was re-sampled or re-run.

**Check:** `python scripts/verify_rebuild_v3.py` rebuilds the pool in memory and diffs it against
both pools.

**Headline numbers (PR4 -> v3):** event-level accuracy 85.6% (291 scored) -> 86.5% (288 scored);
cluster-level 81.8% (66) -> 85.7% (63); cluster-level excluding T1059.001 83.0% (43) -> 89.2% (40);
T1059.003 clusters correct 2 of 5 -> 2 of 2.

**Tables 1-5 (2026-10-28)** are in `tables_v3/v3/table1.md` ... `table5.md`, written by
`scripts/build_tables_v3.py` (run `scripts/recompute_tables_v3.py` first). Two conventions are now explicit:
- Table 3 uses n = 63 in every row; an answer that is not valid JSON counts as not correct. Under this
  convention Mask 2 is 52/63 with lost/gained 6/3 (p = 0.508). Before the fix below, `pr4_checks.py report`
  dropped the unparseable pairs (n = 61, 4/3). Lenient parsing is a separate sensitivity row.
- Event ID lookup ties (`evaluation/eventid_lookup.py`): a tie answers NONE (counted wrong), like an unseen
  Event ID. PR4 broke ties by first appearance in `baseline_clean.jsonl`. On v3 this decides 2 predictions
  (1 cluster: Event ID 1, T1053.005 2 vs T1059.003 2), and the leave-one-cluster numbers are the same as
  under the file-order rule. In PR4 it decided 5 T1059.003 predictions (4 vs 4), all in favour of the true label.

**`pr4_checks.py report` fix (2026-10-28).** The report dropped check answers that were not valid JSON
from the paired comparison (Mask 2: n = 61 on the PR4 pool). It now keeps them and counts them as not
correct, so n = sample size in every row, which is the convention the PR4 report used. Re-run on the PR4 pool:

| PR4 pool, n = 66 | before the fix | after the fix | PR4 report |
|---|---|---|---|
| Mask 2 correct (all) | 52/61 | **52/66** | 52/66 |
| Mask 2 lost / gained (all) | 4 / 3, p = 1.000 | **6 / 3, p = 0.508** | 6 / 3, p = 0.508 |
| Mask 2 excl. T1059.001 | 32/38, 3 / 1, p = 0.625 | 32/43, 5 / 1, p = 0.219 | |

Noise and Mask 1 are unchanged (every answer was valid JSON). Lenient parsing gives the same Mask 2 numbers:
its 2 recovered answers are both wrong. On v3 the fixed script gives 52/63, 6 / 3, p = 0.508, the same as
Table 3. `tables_v3/` was regenerated with the fixed script.

**Event ID lookup tests (task 4, 2026-10-28):** `tests/test_eventid_lookup.py`, 16 unittest tests, all
passing (`python -m unittest discover -s tests -t . -v`):
- (a) `without_cluster` removes every event of the left-out cluster and nothing else (toy data and every
  cluster of the v3 pool, checked against a table rebuilt from scratch), and does not modify its input;
- (b) a 2 vs 2 tie returns NONE in either insertion order, and the v3 pool has exactly that one tie
  (Event ID 1, cluster `T1053.005|schtask_create_2020-12-1907003032.json|2020-12-19 12:00`, 2 predictions);
- (c) an unseen Event ID, including one that occurs only in the left-out cluster, returns NONE;
- (d) v3 pool: 288 scored events, 63 clusters; leave-one-cluster 86.5% / 89.1%; in-sample 98.3% / 92.1%;
  upper bound 87.2% / 90.7%.

As a check that the tests can fail, they were run against three deliberately broken lookups:
file-order tie-breaking (6 failures), a leave-one-cluster that leaves one event in (72 failures) and no
leave-one-cluster at all (73 failures).

## v3 Stage 3 inputs (Progress Report 5, part 2), 2026-10-28

**Evaluation set: `eval_set_v3.jsonl`**, written by `build_eval_set.py` from the v3 pool. At most 3 events
per cluster, drawn with `random.Random(f"{SEED}|{cluster_id}")`, **seed `SEED = "stage3-v1"`** (unchanged
from PR4). The one event without a parseable baseline answer is not eligible.
110 events, 63 clusters, 102 with a misleading condition (all but T1021.002).
The per-cluster seed gives the same events as `eval_set.jsonl` in every surviving cluster (110 of 110 rows
identical). Note: the PR4 `eval_set.jsonl` (137 rows) predates R7. Besides the 3 dsregcmd.exe rows, 24 of
its rows are in clusters that R7 had already removed from the PR4 pool. `eval_set.jsonl` is left as is.

**Evidence pairs: `stage3_v3/evidence_pairs.jsonl`**, written by `python -m evidence.stage3_builder`
(no API calls). 322 pairs: genuine 110, misleading 102, neutral 110.
- Genuine: same raw file and host, different Event ID, Event ID in the find_adjacent.py INFORMATIVE set. Link
  preference: shared process GUID (21), shared PID within 120 s (56), else nearest in time in the same 60 s
  window (33). No eval event is left without genuine evidence. The link type is recorded per pair.
  PIDs are compared as integers (Security logs write hex). `ExecutionProcessID` is a link key only for
  PowerShell-channel events (there it is the powershell.exe PID; elsewhere it is the logging process).
- Misleading: one event from a v3 pool cluster of the decoy technique, cluster and event drawn with
  `random.Random(f"stage3-v1|misleading|{event_uid}")`. Decoys: T1059.001<->T1059.003, T1003.001<->T1003.006,
  T1055<->T1562.002, T1053.005->T1547.001->T1546.003->T1053.005; T1021.002 none.
- Neutral: no evidence.
- All evidence: cleaned like the baseline input, host / time / GUID fields dropped, remaining host names,
  timestamps, GUIDs and technique IDs masked. The automatic leak check finds none left. Technique *names* in
  log content are flagged, not masked: 'PowerShell' 94 (Channel, image paths, ContextInfo), 'DCSync' 2
  (a Meterpreter `Invoke-DcSyncAll` script in two genuine T1059.001 pairs).
- Per pair: `same_event_id` (and `same_field_set`). It is false for every genuine pair (by rule) and for all
  102 misleading pairs (no decoy technique shares an Event ID with its source technique).

**Audit export: `stage3_v3/audit_20.md`**, written by `scripts/export_audit_v3.py` with seed
`stage3-v1|audit`. One genuine and one misleading pair per technique (19), plus the DCSync-flagged pair.

### Stage 3 evidence rebuild after the audit decisions, 2026-10-28 (supersedes the bullets above where they differ)
- Genuine log content (channel names, image paths, script text) is kept unmasked.
- Process and thread IDs in evidence (every field ending in ProcessId / ThreadId) are replaced by [PID] / [TID].
  The leak check now also looks for the original's PIDs. One remains, inside script output (`JobPID 5220`
  printed by Write-Host in a 4103 Payload, pair `76bc91e1e13e4131|genuine`). It is left as is, because script
  content is not masked.
- `same_channel` replaces `same_event_id` / `same_field_set`. Same channel: genuine 79 of 109, misleading
  31 of 102 (T1053.005, T1055, T1546.003, T1547.001, T1562.002 decoys share the original's channel;
  T1003.x, T1059.x do not).
- Genuine evidence is never a pool event labelled with another technique. Such a candidate is passed over
  and the next link in order (GUID, PID, time) is taken; if none is left, the event has no genuine evidence.
  This changed 2 pairs: `2abb6855b6f8b93a` (T1003.001: a T1055 Event ID 8 -> Event ID 1, still GUID-linked)
  and `4fc6fdb9ffb5b639` (T1021.002: a T1059.001 4104 -> a 4103, still time-linked). No event was left
  without genuine evidence. Same-technique pool events stay allowed (9 T1546.003 pairs use another
  WMI event of the same technique).
- Excluded by hand: `10e28166046adcc9|genuine` (audit pair 20; its evidence is a Meterpreter
  `Invoke-DcSyncAll` script). It has no genuine evidence (`link_type = "excluded"`). The second DCSync pair,
  `565fa9197f8b105b|genuine` (same cluster, a different 4103 event), is still included and flagged.
- Misleading: unchanged method. Every v3 pool event of the decoy technique was already eligible (not only
  eval-set events). Decoy pool events / distinct events used: T1003.001 7/5, T1003.006 9/6, T1053.005 3/3,
  T1055 40/2, T1059.001 2/2, T1059.003 199/2, T1546.003 4/4, T1547.001 12/3, T1562.002 5/4. The draw picks a
  cluster first, then an event; T1055's 5 pairs drew 2 of the 4 T1562.002 clusters.
- Totals: 322 pairs; genuine 110 (GUID 21, PID 56, time 32, excluded 1), misleading 102, neutral 110.
  138 pairs changed evidence text (mostly the PID masking); 3 changed evidence event (2 by the
  other-technique rule, 1 excluded).
- `stage3_v3/audit_20.md` regenerated: the same 19 strata picks, plus the remaining DCSync pair.

**Power table** (`scripts/power_table.py`, PR4 Table 7 settings): exact two-sided McNemar on discordant
clusters, alpha 0.05, 20,000 trials, seed 20261028, each cluster one independent binary unit. Misleading breaks
15/25/35% of correct clusters and fixes 2% of wrong ones; genuine fixes 50/80% of wrong clusters and breaks 3%
of correct ones; the misleading test leaves out T1021.002. The script also computes exact power.
- PR4 check (54/12, 36/7; misleading 46/12, 28/7). Exact power 63.2 / 96.6 / 99.9 / 18.6 / 64.9 (66 clusters)
  and 21.0 / 69.0 / 94.0 / 2.1 / 19.3 (43), against PR4 63 / 96 / 100 / 18 / 65 and 21 / 69 / 94 / 2 / 19. Every
  cell lies within rounding + 3 Monte Carlo SE, so it is reproduced. (This run's simulation gave 64.0 for the
  first cell, seed noise.) Output: `tables_v3/pr4/power_table.md`.
- v3 (54/9, 36/4; misleading 46/9, 28/4), exact power: 63 clusters 65.0 / 97.2 / 99.9 / 5.5 / 31.7;
  40 clusters 22.1 / 71.0 / 94.9 / 0.0 / 0.0. Excluding T1059.001, the genuine test cannot reach p <= 0.05:
  even 4 fixes and 0 breaks of the 4 wrong clusters gives p = 0.125. Output: `tables_v3/v3/power_table.md`.

**Table 3**: added the column "Answers that differ from the baseline" (valid answers naming a different
technique than the stored baseline answer). v3: noise 1 of 63, mask 1 7 of 63, mask 2 9 of 61 (2 had no
valid answer), mask 2 lenient 10 of 62 (1 had no valid answer). The same code on the PR4 data gives the PR4
values 1 of 66, 7 of 66, 9 of 61 (5 invalid). The other tables are unchanged.

### 2026-10-29
- **Excluded by hand: `565fa9197f8b105b|genuine`**, same reason as `10e28166046adcc9|genuine`. It is in the same
  cluster (`psh_disable_eventlog_service_startuptype_modification.json|2022-08-04 08:36`), and its evidence is a
  different 4103 event carrying the Meterpreter `Invoke-DcSyncAll` script. Recorded in `EXCLUDE_GENUINE`
  (`evidence/stage3_builder.py`). Pairs rebuilt: genuine 110 = GUID 21, PID 56, time 31, excluded 2; no other
  pair changed. 'DCSync' no longer appears in any evidence text. `audit_20.md` was not regenerated, so its
  pair 20 is now this excluded pair; pairs 1-19 are unaffected.
- **T1059.001 genuine evidence matching another technique** (`scripts/scan_t1059_001_genuine.py`, list only,
  nothing excluded) is in `stage3_v3/t1059_001_genuine_matches.md`. 5 of 51 pairs match:
  - 4 match T1021.002: `10c9e2221a786d8e`, `df28c325f68125d2`, `2120d356ca88c930`, `d2ea07bf752be380` (APT29,
    23:11-23:14, PID-linked). The evidence is an Event ID 1 for `PsExec64.exe -accepteula \\[HOST] -u ... -p ...`.
  - 1 matches T1562.002: `71baed215173a602` (2022-08-04 08:37, time-linked). The evidence is a 4103 for
    `Set-Service -Name EventLog -StartupType Disabled`.
  No matches for DCSync (after the two exclusions), WMI subscription, Run keys, scheduled tasks or the extra
  categories (LSASS, injection, cmd.exe /c, tool loading).
- **Power table:** the values are now labelled exact power (sum over both binomials). The 20,000-trial
  simulation is shown only as a check column. The numbers are unchanged.

### Exclusion rule R-G1, 2026-10-29
**Rule:** genuine evidence for a T1059.001 event is excluded when its content matches another of the ten
candidate techniques. "Content" means every evidence field except Channel and SourceName, after stripping.
The patterns are in `OTHER_TECHNIQUE_PATTERNS` in `evidence/stage3_builder.py`: the technique categories of
`scripts/scan_t1059_001_genuine.py`; tool loading alone is not a technique. Script content is never masked, so
an excluded pair has no genuine evidence (`link_type = "excluded"`, `excluded_reason`, `excluded_matches`).
The rule replaces the two by-hand exclusions above. Those two pairs fall under it too, so all 7 are excluded
by this one rule. The builder stops if the rule excludes any pair outside this list:

| pair | cluster | matches | content |
|---|---|---|---|
| `10e28166046adcc9\|genuine` | psh_disable_eventlog 2022-08-04 08:36 | T1003.006 | Meterpreter `Invoke-DcSyncAll` script (4103) |
| `565fa9197f8b105b\|genuine` | psh_disable_eventlog 2022-08-04 08:36 | T1003.006 | Meterpreter `Invoke-DcSyncAll` script (4103) |
| `10c9e2221a786d8e\|genuine` | APT29 2020-05-01 23:11 | T1021.002 | `PsExec64.exe -accepteula \\[HOST] ...` (Event ID 1) |
| `df28c325f68125d2\|genuine` | APT29 2020-05-01 23:12 | T1021.002 | same |
| `2120d356ca88c930\|genuine` | APT29 2020-05-01 23:13 | T1021.002 | same |
| `d2ea07bf752be380\|genuine` | APT29 2020-05-01 23:14 | T1021.002 | same |
| `71baed215173a602\|genuine` | psh_disable_eventlog 2022-08-04 08:37 | T1562.002 | `Set-Service -Name EventLog -StartupType Disabled` (4103) |

Pairs rebuilt: only the 5 new pairs changed. **T1059.001 genuine pairs with evidence: 46 of 53**
(PID 43, time 3), in 19 of the 23 T1059.001 clusters; 4 clusters now have no genuine T1059.001 pair.
All techniques: 103 of 110 genuine pairs have evidence (GUID 21, PID 52, time 30, excluded 7).

**audit_20.md:** not regenerated. Only pair 20 was replaced (`scripts/replace_audit_pair20.py`): it was
`565fa9197f8b105b|genuine`, now excluded, and is now **`f75cb76d84f877ff|misleading`** (T1003.006, decoy
T1003.001). It was drawn with seed `stage3-v1|audit|pair20` from the 89 genuine and misleading pairs with
evidence, outside T1059.001 and not among pairs 1-19. Before writing, the script checked that pairs 1-19
re-render exactly as in the file. Everything before section 20 is byte-identical except table row 20.

### Sensitivity clusters, 2026-10-30 (decided before any Stage 3 call)
The hand audit of `audit_20.md` and the label check (`stage3_v3/label_check.md`, `scripts/label_check.py`,
`scripts/label_check_ps.py`) found 3 clusters whose labels are doubtful. **The v3 pool stays as it is.**
Every Stage 3 analysis reports the main result (63 clusters, 40 excluding T1059.001) and the result without
these 3 clusters (60 and 37). The list is also in `stage3_v3/sensitivity_clusters.json`.

| cluster | eval event | reason |
|---|---|---|
| `T1547.001\|empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json\|2020-09-04 07:08` | `243e55d798340ba4` | The Run key value `WindowsDefender` (pointing to `MSASCuiL.exe`) is written by the Defender engine MsMpEng.exe (wininit.exe → services.exe → MsMpEng.exe). This is Defender's own startup entry, not the Empire persistence key. |
| `T1059.003\|apt29_evals_day1_manual_2020-05-01225525.json\|2020-05-02 03:03` | `30f8bc022db8378b` | conhost.exe under a cmd.exe started by the Azure guest agent's log collector (WaAppAgent.exe → CollectGuestLogs.exe → cmd → conhost.exe). This is platform activity, not attacker use of cmd. |
| `T1003.006\|apt29_evals_day1_manual_2020-05-01225525.json\|2020-05-01 23:16` | `f75cb76d84f877ff` | The 4662 replication-rights access is by the machine account `NEWYORK$`, the pattern of normal domain controller replication. It is the only one of the 7 pool 4662 events whose SubjectUserName ends in `$`. |

Whole v3 pool: 2 events have a Defender or `C:\WindowsAzure` binary in their process or parent chain (the
first two above). 1 of the 7 4662 events has a SubjectUserName ending in `$` (the third).

### Stage 3 builder fixes, 2026-10-30 (decided before any Stage 3 call; no API calls)
Each fix was switched on in turn. With all fixes off, the build reproduces the previous
`evidence_pairs.jsonl` exactly. Pairs changed by each fix, in order:

1. **Well-known GUIDs kept.** Schema and rights GUIDs that are the same on every domain are no longer masked:
   `domainDNS` `19195a5b-6da0-11d0-afd3-00c04fd930c9` and the DS-Replication rights `1131f6aa-…`, `1131f6ad-…`,
   `1131f6ab-…`, `1131f6ac-…` and `89e95b76-…` (`WELL_KNOWN_GUIDS`). Only instance GUIDs are masked: objects,
   runspaces, activities, script blocks. **9 pairs changed**: every T1003.001 misleading pair, whose decoy is
   a T1003.006 4662 event.
2. **Timestamps inside file names and paths masked** (`PATH_TIME_RE`, for example `20200904-030800` → `[TIME]`).
   **1 pair changed**: `243e55d798340ba4|genuine` (`MpWppTracing-…bin`).
3. **The same action logged twice is not genuine evidence.** The next link is taken; if no link is left, the
   pair has no genuine evidence.
   - Sysmon 1 vs Security 4688: same host, same new-process PID and same image.
   - 4104 vs 4103: same PowerShell process (`ExecutionProcessID`), and the command the 4103 records
     (`CommandInvocation`) is written in the 4104 script block, by name, by a built-in alias, or without `Get-`.

   Each pair records what was passed over in `skipped_same_action`. **16 genuine pairs changed**:
   - 2 T1053.005 pairs (`0793212750e00b04`, `f1f7f5f2d849a95e`)
   - 14 T1059.001 pairs
   
   All 16 found another link: 13 another 4103, 1 an Event ID 1 (`76bc91e1e13e4131`, whose `JobPID 5220` PID
   leak is gone) and the 2 T1053.005 pairs another 4688. No new pair is excluded.
4. **Base64 decoded before every scan** (leak check, R-G1, R-M1). Strings of 20 or more characters are decoded
   as UTF-16LE (PowerShell `-enc`) or UTF-8, kept when at least 95% printable, nested up to depth 3. **Fixed in
   advance:** the Empire launcher's standard code that turns off script block logging is not a T1562.002
   match. Statements that touch the script block logging settings (`EMPIRE_SBL_RE`) are removed before the
   T1562.002 check. **0 pairs changed.** The decoded Empire stagers (20 evidence texts) match no pattern and
   leak no host, time, GUID or PID. With the current T1562.002 pattern, the removed statements would not have
   matched anyway. No T1059.001 genuine evidence contains Base64.
5. **Rule R-M1 (2026-10-30), mirroring R-G1:** misleading evidence must not match a candidate technique other
   than its decoy (`OTHER_TECHNIQUE_PATTERNS`, Base64 decoded, Channel and SourceName ignored). A matching event
   is dropped and the cluster-then-event draw is repeated with the same generator, so pairs whose first draw
   was clean are unchanged. Rejected events are recorded in `rejected_rule_m1`. If no clean event is left, the
   pair has no misleading evidence (none needed). **6 misleading pairs changed**:
   - `ae4b62e1857e1a39` (T1059.003, decoy T1059.001): the DCSync script `4d3f8fd71a731ced` was rejected.
   - 5 T1546.003 pairs (decoy T1053.005): `cmd.exe /C schtasks …` matches T1059.003. The 12 T1546.003
     misleading pairs now use 2 distinct decoy events.

   R-G1 and R-M1 use the same nine patterns, so T1059.001 itself has no pattern. A decoy event that only runs
   `powershell.exe` is not rejected.

After the fixes: genuine 103 of 110 with evidence (GUID 21, PID 52, time 30, R-G1 excluded 7, the same 7
pairs); misleading 102 of 102. Leak check: none on 205 evidence texts. Tests: 16 OK.

| technique | genuine pairs (clusters) with evidence | misleading pairs (clusters) with evidence |
|---|---|---|
| T1003.001 | 9 of 9 (6 of 6) | 9 of 9 (6 of 6) |
| T1003.006 | 7 of 7 (3 of 3) | 7 of 7 (3 of 3) |
| T1021.002 | 8 of 8 (8 of 8) | no misleading condition |
| T1053.005 | 4 of 4 (3 of 3) | 4 of 4 (3 of 3) |
| T1055 | 5 of 5 (5 of 5) | 5 of 5 (5 of 5) |
| T1059.001 | 46 of 53 (19 of 23) | 53 of 53 (23 of 23) |
| T1059.003 | 2 of 2 (2 of 2) | 2 of 2 (2 of 2) |
| T1546.003 | 12 of 12 (6 of 6) | 12 of 12 (6 of 6) |
| T1547.001 | 3 of 3 (3 of 3) | 3 of 3 (3 of 3) |
| T1562.002 | 7 of 7 (4 of 4) | 7 of 7 (4 of 4) |
| **all** | 103 of 110 (59 of 63) | 102 of 102 (55 of 55) |
| **all excl. T1059.001** | 57 of 57 (40 of 40) | 49 of 49 (32 of 32) |
| **all, without the 3 sensitivity clusters** | 100 of 107 (56 of 60) | 99 of 99 (52 of 52) |
| **excl. T1059.001, without the 3** | 54 of 54 (37 of 37) | 46 of 46 (29 of 29) |

**audit_20.md:** only pairs 1, 2, 3, 6, 10 and 13 were re-rendered (`scripts/regenerate_audit_pairs.py`,
same pair IDs, fresh checkboxes and notes). All other sections and table rows are byte for byte as they
were, including the hand-audit notes. The full round-1 audit with all notes is kept in
`stage3_v3/audit_20_round1.md`.
- Pairs 1 and 3 render the same as before (no fix touches them).
- Pair 2 now shows the rights GUIDs.
- Pair 6 is now the parent `cmd.exe /C schtasks` 4688.
- Pair 10 is now a different 4103 (`Out-Default`).
- Pair 13 is now the 4104 `View-Job -JobName "Keystrokes"`.
- Pair 16 (`243e55d798340ba4|genuine`) changed under fix 2 but was not re-rendered, so its section still
  shows the unmasked path timestamp.

### Content, not carrier: R-G1 and R-M1, 2026-10-30 (decided before any Stage 3 call)
**Principle:** R-G1 and R-M1 judge content, not the carrier. A command interpreter (cmd.exe or powershell.exe)
that only launches an action counts as that action. It therefore does not match T1059.003 or T1059.001 on
its own. The principle is recorded in `evidence/stage3_builder.py` (`CARRIER_PRINCIPLE`).
- The T1059.003 pattern `cmd(.exe) /c|/k` was the only T1059.003 pattern, and it describes exactly the
  carrier case, so it was removed from `OTHER_TECHNIQUE_PATTERNS`. No PowerShell pattern is added.
- Both rules use that pattern set. R-G1 is unchanged: it still excludes the same 7 pairs.
- Everything else from the fixes above is kept, including the R-M1 rejection of the DCSync script for
  `ae4b62e1857e1a39|misleading`.

**Pairs changed: 5.** The 5 T1546.003 misleading pairs rejected under R-M1 (`5245ac53f9dc00d0`, `5ced8e2750f407b9`,
`81ce69fde1c8881b`, `20cb0aba5a87932e`, `d44191689158627a`) are back to their original decoys (`cmd.exe /C
schtasks …`, `0793212750e00b04` / `f1f7f5f2d849a95e`), identical to the build before R-M1. R-M1 now redraws
only 1 pair. Misleading 102 of 102 with evidence. Tests: 16 OK.

Distinct decoy events used per technique:

| technique | decoy | misleading pairs | decoy pool events | distinct decoy events used |
|---|---|---|---|---|
| T1003.001 | T1003.006 | 9 | 7 | 5 |
| T1003.006 | T1003.001 | 7 | 9 | 6 |
| T1053.005 | T1547.001 | 4 | 3 | 3 |
| T1055 | T1562.002 | 5 | 40 | 2 |
| T1059.001 | T1059.003 | 53 | 2 | 2 |
| T1059.003 | T1059.001 | 2 | 199 | 2 |
| T1546.003 | T1053.005 | 12 | 4 | 4 |
| T1547.001 | T1546.003 | 3 | 12 | 3 |
| T1562.002 | T1055 | 7 | 5 | 4 |

**audit_20.md:** pairs 13 and 16 were re-rendered (`scripts/regenerate_audit_pairs.py 13 16`). Pair 13 is
unchanged by this decision. Pair 16 now shows the masked path timestamp. All other sections are untouched.

### Stage 3 prompt and runner, 2026-10-30 (fixed before any Stage 3 call; no API calls made)
**Changes from the Stage 2 verification prompt** (`VERIFICATION_SYSTEM_PROMPT` / `build_verification_user_prompt`,
left unchanged for the earlier pilot scripts):
1. **System prompt, first line:** "using additional evidence" is dropped. The rest of the system prompt is
   unchanged, including the paragraph on weighing the evidence critically.
2. **One closing line for all conditions:** "Taking everything above into account, what is your revised
   prediction?" It replaces "Given this additional evidence, what is your revised prediction?"
3. **Identical across conditions except the evidence block.** The neutral evidence block is "None provided."

In code: `STAGE3_SYSTEM_PROMPT`, `STAGE3_NEUTRAL_EVIDENCE` and `build_stage3_user_prompt` in `llm/prompts.py`.

**Final system prompt** (the same in every call):

```text
You are a security analyst re-examining a previous MITRE ATT&CK technique prediction.

You must choose exactly one technique from this candidate list (or "NONE"):

- T1059.001 (PowerShell, Execution): Adversary runs commands or scripts via the PowerShell interpreter.
- T1059.003 (Windows Command Shell, Execution): Adversary runs commands via cmd.exe.
- T1053.005 (Scheduled Task, Persistence): Adversary creates/modifies a Windows Scheduled Task to run code on a trigger.
- T1547.001 (Registry Run Keys / Startup Folder, Persistence): Adversary adds a program to a Registry Run key or Startup folder to execute at logon.
- T1546.003 (WMI Event Subscription, Persistence): Adversary establishes persistence via a WMI event filter/consumer that triggers on a system event.
- T1003.001 (LSASS Memory, Credential Access): Adversary dumps credentials from LSASS process memory.
- T1003.006 (DCSync, Credential Access): Adversary abuses AD replication permissions (DS-Replication-Get-Changes) to pull password hashes from a domain controller.
- T1055 (Process Injection, Defense Evasion): Adversary injects code into the address space of another live process.
- T1562.002 (Disable Windows Event Logging, Defense Evasion): Adversary stops or disables Windows event logging to avoid detection.
- T1021.002 (SMB/Windows Admin Shares, Lateral Movement): Adversary moves laterally via SMB admin shares, often creating/starting a remote service.

Respond with ONLY a JSON object, no other text, in this exact format:
{"predicted_technique": "<technique ID or NONE>", "confidence": <integer 0-100>, "changed_from_baseline": <true/false>, "reasoning": "<one or two sentences>"}

Weigh the new evidence critically. It may support, refute, or be irrelevant to the original prediction. Do not assume the evidence is automatically correct just because it is presented as evidence — evaluate whether it is actually consistent with the original telemetry.
```

**Final user prompt** (`<EVIDENCE>` is the pair's `evidence_text` for genuine and misleading, and
`None provided.` for neutral):

```text
Original telemetry event:
<original event: the cleaned fields the baseline saw, one "key: value" per line, not masked>

Your previous baseline prediction: <baseline predicted_technique> (confidence: <baseline confidence>)
Your previous reasoning: <baseline reasoning>

Additional evidence:
<EVIDENCE>

Taking everything above into account, what is your revised prediction?
```

**Output and parsing.**
- The model must return one JSON object with `predicted_technique`, `confidence`, `changed_from_baseline` and
  `reasoning`.
- Primary rule (strict): the whole reply must parse with `json.loads` and contain `predicted_technique`.
  Otherwise it is stored as `{"error", "raw"}` and counts as not correct, with n kept at the full sample, as in
  the baseline checks.
- A lenient last-`{…}` parse is a separate sensitivity row.
- Correct means `predicted_technique` equals the label. `changed_from_baseline` is recorded, not scored.

**Client.** `llm/client.py` now has `call_llm_logged`. It returns the text plus `usage.input_tokens`,
`usage.output_tokens`, `stop_reason`, `model`, the request ID and the number of attempts. `call_llm` wraps
it and still returns only the text, for the existing scripts. No sampling parameters and no `thinking`
setting are sent (API default sampling, as in the baseline).

**Runner `run_stage3.py`.**
- **Call settings:** Claude Sonnet 4.6 (`LLM_MODEL`), `max_tokens` 300.
- **What it runs:** 315 calls (genuine 103, misleading 102, neutral 110). The 7 R-G1 pairs have no evidence
  and are not run.
- **Call order:** shuffled with seed `stage3-v1|order`.
- **Logging and resume:** every call is logged (pair, prompt SHA-1, model, `stop_reason`, request ID, input
  and output tokens, raw text, parsed answer, time) and appended as it finishes. A rerun skips pairs already
  logged.
- **`--render <event_uid>`** prints the prompts with no API client loaded.
- **`--pilot`** makes 15 calls: 5 events × 3 conditions, drawn with seed `stage3-pilot-v1` from events with
  all three conditions outside the sensitivity clusters. The events are `3e74cf0cc7262865` (T1003.001),
  `897e82cd22af2fbd` (T1003.006), `54d7bbb55bb2c128` (T1055), `ae4b62e1857e1a39` (T1059.003) and
  `d2d8a80c7c8a667f` (T1547.001). Results go to `stage3_v3/pilot_results.jsonl` and are not used in the
  analysis: the full run calls every pair fresh.
- **`--full`** writes `stage3_v3/stage3_results.jsonl`.

**Estimated cost of the full run:** 430-620 k input tokens and about 41 k output tokens, so about $1.90-2.50
at $3 / $15 per M ($3.30 if every answer used all 300 output tokens). The pilot is about $0.10.

### Stage 3 pilot, 2026-10-30
`python run_stage3.py --pilot`: 15 calls, `stage3_v3/pilot_results.jsonl` (not used in the analysis).
- **Calls:** no API failures; all 15 answered by `claude-sonnet-4-6` at the first attempt.
- **Tokens and cost:** input 16,457 and output 2,088 tokens, $0.081 (estimate about $0.10).
- **Stops:** 14 `end_turn`, 1 `max_tokens`.
- **Parsing:** 13 of 15 were strict JSON and 14 of 15 lenient. Both failures were misleading pairs:
  - `54d7bbb55bb2c128|misleading` wrote prose, then a valid JSON object.
  - `3e74cf0cc7262865|misleading` hit the 300-token limit before writing any JSON.
- **`changed_from_baseline`:** matched the actual change in all 14 parseable answers.
- **Technique-ID leak:** the model cited `ntds_T1003` in `ae4b62e1857e1a39|genuine` and changed to T1003.006.

### Decisions after the pilot, 2026-10-30 (before `--full`)
1. **Technique-ID boundary.** The ID mask and the leak check now treat any non-alphanumeric character
   (underscore and dot included) before or after `T1xxx` as a boundary: `TECH_ID_RE`,
   `(?<![A-Za-z0-9])T1\d{3}(?:\.\d{3})?(?![A-Za-z0-9])`.
   - The old pattern treated `_` as part of a word, so `ntds_T1003` escaped both the mask and the leak check.
   - After the rebuild, **1 evidence text changed**: `ae4b62e1857e1a39|genuine`, where `TargetFilename:
     C:\Windows\Temp\ntds_T1003` is now `C:\Windows\Temp\ntds_[TECHNIQUE_ID]`.
   - No other evidence text changed. Leak check: none on 205 texts. No `T1xxx` string is left in any evidence
     text.
2. **R-G1 extended to T1059.003** genuine evidence: cmd.exe is a carrier like PowerShell (`CARRIER_PRINCIPLE`).
   `RULE_G1_TECHNIQUES = {T1059.001, T1059.003}`; the rule text is updated.
   - **It excludes nothing.** Both T1059.003 genuine pairs keep their evidence: `30f8bc022db8378b` (PID link)
     and `ae4b62e1857e1a39` (GUID link). R-G1 still excludes the same 7 T1059.001 pairs.
   - Only the stored `excluded_reason` text of those 7 pairs changed. Tests: 16 OK.
3. **Stage 3 settings** (`run_stage3.py`):
   - **`max_tokens` 1024** (was 300, as in the baseline).
   - **Primary parse = lenient:** the last valid JSON object in the reply that contains `predicted_technique`,
     found by decoding at every `{`. It is stored as `prediction`.
   - **Strict parse = sensitivity analysis:** the whole reply must be that object. It is stored as
     `prediction_strict`.
   - **A reply with no valid JSON object counts as not correct.**
   - `--report <mode>` prints the non-JSON rate by condition for both parses, plus `max_tokens` stops, with no
     API call.
   - On the first pilot's replies the parsers give 14 of 15 (lenient) and 13 of 15 (strict), as above.
4. **Check run `--pilot2`:** only the three pilot calls affected by these fixes (`3e74cf0cc7262865|misleading`,
   `54d7bbb55bb2c128|misleading`, `ae4b62e1857e1a39|genuine`), written to `stage3_v3/pilot2_results.jsonl`.
   It is not used in the analysis.
   - Result: all 3 parse under the primary rule, with no `max_tokens` stop (`3e74…` used 561 tokens). The two
     misleading replies still put prose before the JSON (strict parse fails).
   - `ae4b…|genuine` still answers T1003.006, now from the `ntds` file name.
   - Cost $0.024 (3,451 input and 916 output tokens).

### Decisions before the full run, 2026-11-01
- **Known carrier case, kept as it is: `ae4b62e1857e1a39|genuine`.** The original is `conhost.exe` under
  `cmd.exe`, labelled T1059.003. The genuine evidence is cmd.exe writing `C:\Windows\Temp\ntds_[REDACTED]`,
  part of the ntdsutil NTDS.dit dump in that cluster.
  - The real activity is an NTDS.dit dump (T1003.003). That is not one of the ten candidates, so R-G1, which
    matches only the ten candidates, stays unchanged and does not exclude the pair.
  - The pair is recorded for the error analysis. In the pilot the model changed to T1003.006 here, so genuine
    evidence of the real activity behind a carrier-labelled event can move a correct answer away from the label.
- **Technique-ID placeholder `[TECHNIQUE_ID]` → `[REDACTED]`** (a neutral word, so the placeholder no longer
  says a technique ID was there).
  - Rebuild: 2 evidence texts changed, only in the placeholder: `ae4b62e1857e1a39|genuine` (`ntds_[REDACTED]`)
    and `8e3d9584157cfe02|genuine` (`PurpleSharp.exe /t [REDACTED]`, masked before as well).
  - These are the only two evidence texts with a masked technique ID. Leak check: none.

### Stage 3 analysis script, 2026-11-01 (written and tested on the pilot data before any look at the full results)
`analysis/stage3_analysis.py`, following the PR4 Evaluation plan.

**Scoring and contrasts**
- **Unit: cluster.** A cluster's score is the share of its sampled events scored correct under the primary
  lenient parse. Its baseline is the stored baseline answers of the same events. Each contrast uses only the
  events answered in both arms.
- **Primary contrast:** misleading vs baseline, two-sided, alpha 0.05, T1021.002 excluded.
- **Secondary contrasts:** genuine vs baseline, neutral vs baseline and misleading vs neutral, Holm-corrected
  together.

**Test and cluster sets**
- **Paired permutation test** on the per-cluster score differences (sign flips, statistic = sum).
  - It is exact (dynamic programming over the exact distribution) when at most 25 clusters have a non-zero
    difference. Otherwise it uses 1,000,000 random sign flips, seed `20261101`, p = (hits + 1) / (N + 1).
  - The method used is printed per test.
  - Checked on synthetic data: the exact result equals brute-force enumeration, and the Monte Carlo result
    agrees within ±0.0005.
- **Four cluster sets:** all 63, 40 excluding T1059.001, and both without the 3 sensitivity clusters (60 and
  37). A conclusion needs the 63 and 40 sets to agree in direction.
- **All tests are repeated with the strict parse** as a sensitivity analysis.

**Sensitivity of the primary contrast**
- **(a)** One event per cluster, drawn with seed `stage3-analysis|one-per-cluster`.
- **(b)** Each technique left out in turn.

**Descriptive outputs**
- Per condition:
  - corrections, regressions and unchanged, at event and cluster level
  - mean confidence and its change
  - Brier score and 5-bin ECE, with the number of answers left out for lack of a valid confidence
  - the non-JSON rate (lenient and strict) and `max_tokens` stops
- T1059.001 alone, with no test.
- Genuine and misleading evidence split by same vs different log channel.
- **Exploratory (PR4 plan):** under misleading evidence, the baseline confidence of events that regressed vs
  events that stayed correct (n, mean and median, event level).

### Stage 3 full run, 2026-11-01
`python run_stage3.py --full` → `stage3_v3/stage3_results.jsonl` (per-call log `stage3_v3/stage3_run.log`).
- **Calls:** 315 calls, 07:34-07:50. All 315 expected pairs were answered once (genuine 103, misleading 102,
  neutral 110). There were no missing or duplicate pairs.
- **API failures:** none, and no retries were needed.
- **Responses:** every `stop_reason` was `end_turn`. All were answered by `claude-sonnet-4-6`, and all carry
  a request ID.
- **Tokens:** 524,855 input and 40,613 output (mean 1,666 / 129 per call, maximum output 566).
- **Cost:** $2.18 ($1.57 input + $0.61 output), against an estimate of about $2-3.

**Analysis output saved, 2026-11-01.** `analysis/stage3_analysis.py` now also writes its printed output to
`stage3_v3/analysis_output.txt` when it runs on the full results (`stage3_v3/stage3_results.jsonl`). Pilot
files are only printed.
- No computation changed: a `Tee` on stdout, active only around `main()`.
- Checked: the saved file (141 lines, 11,794 characters) is identical to the printed output, and the values
  are the same as the earlier run.

**Artifact check of the changed answers, 2026-11-01** (`scripts/artifact_check.py`, `scripts/artifact_check2.py`;
read-only, no API calls). The check covers the 17 answers whose correctness changed: misleading 11
regressions, genuine 4 regressions and 2 corrections.
- **What it does:** extracts every specific artifact the reasoning cites, using fixed rules: GUIDs, event IDs,
  registry keys, paths, file and process names, hex values, quoted strings, cmdlets, host-like names and a
  fixed list of tool names. Each artifact is checked case-insensitively against the prompt that was sent. The
  prompt is rebuilt, and all 17 match the logged `prompt_sha1`.
- **Result:** 56 of 62 artifacts appear literally in the prompt. All 8 cited Event IDs equal the `EventID`
  line of the original or the evidence event.
- **Not found literally (6, in 5 answers):**
  - `ae4b62e1857e1a39|genuine`: `NTDS.dit`. The prompt has only `ntds_[REDACTED]`.
  - `0793212750e00b04|misleading` and `b7d819458bfa1246|misleading`:
    `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\Updater`. The prompt has
    `HKU\S-1-5-21-…-1104\Software\…\Run\Updater`, which matches after `HKU\<SID>\` → `HKCU\`.
  - `30f8bc022db8378b|misleading`: two citations.
    - `HKCU:\Software\Classes\Folder\shell`. The prompt has
      `New-Item -Path HKCU:\Software\Classes\Folder -Name shell -Force;`.
    - `HKCU\Software\Classes`, which matches `HKCU:\Software\Classes` after normalising.
  - `ae4b62e1857e1a39|misleading`: `'View-Job -JobName Keystrokes'`. The prompt has
    `View-Job -JobName "Keystrokes"`, with quotes.
- **Limits:** artifacts cited in free prose without one of these forms are not checked. One extraction
  ("Replication-Get", from "DS-Replication-Get-Changes") is spurious and appears only in the system prompt.

**Deviation from the PR4 plan:** the Cap 5 and reboot-window sensitivity analyses are not run. Cap 5 would need
new calls on a re-capped sample, and the reboot window would need a new pool.

### Label checks from the raw events, 2026-11-08 (found after the Stage 3 results; pool unchanged)
Scripts: `scripts/label_verify_a.py`, `scripts/label_verify_a2.py`, `scripts/label_verify_b.py`,
`scripts/label_verify_b2.py` (read-only, no API calls). The sensitivity list of 2026-10-30 is not changed: these
findings came after the results and are reported as post hoc.
- **`4fc6fdb9ffb5b639` (T1021.002, javamtsup, APT29 day 1): local service install, not lateral movement.**
  - Host: SCRANTON. 7045, 4697 (subject pbeesly, logon 0x372e81) and the `services.exe` writes to
    `HKLM\...\Services\javamtsup` are all on SCRANTON at 23:04:15.
  - Created by: 4103 `Move-Item` of `javamtsup.exe` into `C:\Windows\System32`, then 4103 `New-Service -Name
    javamtsup ... -StartupType Automatic`. Host Application `powershell.exe` (ConsoleHost), Script Name
    `C:\Program Files\SysinternalsSuite\readme.ps1`, User `DMEVALS\pbeesly`, empty Connected User.
  - Process chain (Sysmon 1, ParentProcessGuid): `cod.3aka3.scr /S` (RTLO name) -> `cmd.exe` -> `sdclt.exe` ->
    `control.exe /name Microsoft.BackupAndRestoreCenter` (UAC bypass, High integrity from here) -> hidden
    PowerShell stager reading `monkey.png` -> `powershell.exe` (PID 3876) -> `New-Service`.
  - Remote signs on SCRANTON, 23:00-23:06: none. The only type-3 logon is `SCRANTON$` from `::1`; no 5140/5145,
    no 4648; SMB/RPC traffic is outbound from SCRANTON (10.0.1.4) to NEWYORK (10.0.0.4).
  - After a reboot (23:19:14) `services.exe` starts `javamtsup.exe`, which starts `rundll32.exe`: persistence.
- **`f75cb76d84f877ff` (T1003.006, APT29 day 1): NEWYORK is the domain controller; the event fits routine DC
  activity.**
  - Of the four hosts in the file, only NEWYORK logs 4768 (14) and 4769 (28), runs `dns.exe` and `dfsrs.exe`,
    and has a 4662 with ObjectServer `DS`. Its IP is 10.0.0.4.
  - The event: 4662 by `NEWYORK$` (S-1-5-18) on the domainDNS object with only DS-Replication-Get-Changes
    (`1131f6aa`). Its logon session 0x167eda has no other event in the file. It is the only replication-rights
    event in the file. The six other T1003.006 pool events (Empire and Covenant DCSync) are by a user account
    and include an event with Get-Changes-All (`1131f6ad`).

### T1021.002 local-or-remote check and post hoc sensitivity row, 2026-11-08 (after the Stage 3 results)
`scripts/t1021_002_local_remote.py` (read-only, no API calls) checks all 8 T1021.002 pool events (8 clusters,
all System 7045): the 4697 for the service and the 4624 that opened its logon session, remote-creation signs on
the installing host from 120 s before to 5 s after (4624 type 3/10 from another address, 4648, 5140/5145,
inbound Sysmon 3 on 135/139/445, Sysmon 11 of the service binary by System), and the creating process.
- **Remote, 7 events:** the 4 APT29 `PSEXESVC` installs on NASHUA (4697 logon from a type-3 Kerberos logon by
  pbeesly from SCRANTON 10.0.1.4; ADMIN$ write of `PSEXESVC.exe` by System; IPC$ `svcctl`; created by
  `PsExec64.exe \\nashua` on SCRANTON), and the Covenant SharpSC, Empire PsExec and Empire SMBExec installs on
  WORKSTATION6 (4697 logon from a type-3 logon by pgustavo from WORKSTATION5 172.18.39.5; IPC$ `svcctl` except
  Empire PsExec, which uses RPC over TCP 135).
- **Local, 1 event:** `4fc6fdb9ffb5b639` (javamtsup), see the label check above.

`analysis/stage3_analysis.py`: a new last section, **"POST HOC, EXPLORATORY (2026-11-08, after the results)"**,
runs every test again without the local-install cluster (`POST_HOC_LOCAL_INSTALL`) on the four cluster sets (62,
39, 59, 36). The row computation moved into `contrast_rows` / `print_rows`. Checked: the first 141 lines of
`stage3_v3/analysis_output.txt` (now 175 lines; previous version kept outside the repo) are byte-identical to the
2026-11-01 output. Result: the primary contrast and misleading vs neutral are unchanged (T1021.002 is not in
them); genuine vs baseline goes from -0.031 (Holm p 0.69) to -0.014 (Holm p 1.00) on 62 clusters and from -0.029
to -0.004 on 39; neutral stays 0.000.

### Exploratory follow-up of the misleading condition: plan, 2026-11-08 (post hoc; recorded before any call)
**Exploratory and post hoc.** Decided after the Stage 3 results, motivated by the reading of the 11 misleading
regressions. It is reported after the main results and does not replace or change them.
- **Question:** do the regressions under misleading evidence come partly from the closing line not saying that
  the revised prediction is about the original event?
- **Pairs:** the same 102 misleading pairs (`stage3_v3/evidence_pairs.jsonl`), the same evidence text.
- **Prompt:** `STAGE3_SYSTEM_PROMPT` unchanged; the user prompt is `build_stage3_user_prompt` with only the
  closing line changed (`STAGE3_FOLLOWUP_CLOSING`):
  "Taking everything above into account, what is your revised prediction for the original telemetry event above?"
  The default closing is unchanged: all 315 logged `prompt_sha1` values are reproduced, and all 102 follow-up
  prompts equal the Stage 3 prompts except the closing line.
- **Settings:** as the full run: `claude-sonnet-4-6`, API default sampling, `max_tokens` 1024, one call per pair,
  call order shuffled with `stage3-v1|order`, lenient parse primary and strict as sensitivity, API failures
  logged apart and retried.
- **Runner:** `python run_stage3.py --followup` -> `stage3_v3/followup_results.jsonl` (failures in
  `stage3_v3/followup_api_failures.jsonl`); `--render-followup EVENT_UID` prints the prompt without a call.
- **Report:** follow-up vs baseline with the primary test (exact paired sign flip on cluster scores, the four
  cluster sets), plus follow-up vs the Stage 3 misleading answers, descriptive (events and clusters that differ),
  and the non-JSON rate. One answer per pair, so differences of an event or two are within run-to-run noise.
- **Cost estimate:** the Stage 3 misleading calls used 187,900 input and 17,080 output tokens ($0.82). The
  follow-up adds about 6 tokens per call: about $0.82, at most $2.13 if every answer used 1,024 output tokens.

### Exploratory follow-up of the misleading condition: run and results, 2026-11-08 (post hoc)
**Exploratory and post hoc; the main results are unchanged.** `python run_stage3.py --followup` ->
`stage3_v3/followup_results.jsonl` (log `stage3_v3/followup_run.log`); analysis `analysis/followup_analysis.py` ->
`stage3_v3/followup_analysis_output.txt`.
- **Run:** 102 calls, every pair answered once, no API failures, no retries, every `stop_reason` `end_turn`, all
  `claude-sonnet-4-6`. Tokens: 188,716 input, 16,600 output (max 488). Cost $0.82.
- **Against the baseline (lenient, primary parse):** 0 corrections and 0 regressions in 102 events; 55 clusters,
  none up or down. Follow-up vs baseline: mean difference 0.000 on the 55, 32, 52 and 29 cluster sets (no
  non-zero cluster, p = 1).
- **Against the original misleading run:** none of the 11 original regressions regresses under the follow-up,
  and there is no new regression. 14 answers name a different technique: the 11, plus 3 events that were wrong at
  baseline and stay wrong (`6d7a28d24599d714` T1055 -> NONE, `edfd71c1fc0e6d92` not JSON -> T1003.001,
  `210eb98244a082ba` T1055 -> T1003.001). Follow-up vs original misleading: +0.133 (p 0.0020) on 55 clusters,
  +0.229 (p 0.0020) on 32.
- **Strict parse:** 25 of 102 replies (24.5%) are not strict JSON (13.7% in the original run); none lacks a
  valid JSON object (lenient 0%). Under strict parsing these count as wrong: 20 regressions, 15 clusters down,
  -0.227 (p 0.0001) on 55 clusters.
- **Confidence:** 87.3 -> 84.6 (-2.7) against the baseline on the same events; Brier 0.111 -> 0.117, ECE 0.077
  -> 0.067 (original misleading run: -5.9, Brier 0.103 -> 0.174, ECE 0.088 -> 0.132).
- **Limits:** one answer per pair, no repeat of the original wording in the same session, so the comparison with
  the original run mixes the wording change with run-to-run variation; the neutral re-ask (0 of 110 changed) and
  the noise check (1 of 63) suggest that variation is small.

### Exploratory follow-up of the genuine condition: plan, 2026-11-08 (post hoc; recorded before any call)
**Exploratory and post hoc.** Decided after the misleading follow-up results, to see whether the follow-up
closing line also changes answers under genuine evidence. It does not replace or change the main results.
- **Pairs:** the 103 genuine pairs with evidence (the 7 R-G1 exclusions have none), the same evidence text.
- **Prompt and settings:** exactly as the misleading follow-up: `STAGE3_SYSTEM_PROMPT`, closing line
  `STAGE3_FOLLOWUP_CLOSING`, `claude-sonnet-4-6`, API default sampling, `max_tokens` 1024, one call per pair, call
  order shuffled with `stage3-v1|order`, lenient parse primary and strict as sensitivity. Checked: all 103 prompts
  equal the Stage 3 genuine prompts except the closing line.
- **Runner:** `python run_stage3.py --followup-genuine` -> `stage3_v3/followup_genuine_results.jsonl` (failures in
  `stage3_v3/followup_genuine_api_failures.jsonl`).
- **Report:** in the misleading follow-up's format: corrections and regressions against the baseline (event and
  cluster), the exact sign-flip test against the baseline on the 59 and 40 cluster sets (and 56 / 37), whether the
  2 original genuine corrections still correct and the 4 original genuine regressions still regress, new
  changes, non-JSON rates, confidence.
- **Cost estimate:** the Stage 3 genuine calls used 197,461 input and 12,741 output tokens ($0.78); the follow-up
  is about $0.79, at most $2.18 if every answer used 1,024 output tokens.

### Exploratory follow-up of the genuine condition: run and results, 2026-11-08 (post hoc)
**Exploratory and post hoc; the main results are unchanged.** `python run_stage3.py --followup-genuine` ->
`stage3_v3/followup_genuine_results.jsonl` (log `stage3_v3/followup_genuine_run.log`); analysis
`python analysis/followup_analysis.py genuine` -> `stage3_v3/followup_genuine_analysis_output.txt`.
`analysis/followup_analysis.py` now takes the condition as an argument. It also prints the follow-up reasoning of
every original change, and the text before the JSON is cut where the answer object starts, not at the first `{`.
`stage3_v3/followup_analysis_output.txt` (misleading) was regenerated with that section; its numbers are unchanged.
- **Run:** 103 calls, every pair answered once, no API failures, no retries, every `stop_reason` `end_turn`, all
  `claude-sonnet-4-6`. Tokens: 198,285 input, 12,832 output (max 304). Cost $0.79.
- **Against the baseline (lenient):** 1 correction, 3 regressions (original run: 2 and 4); clusters 1 up, 3 down,
  55 same. Follow-up vs baseline: -0.023 (p 0.50) on 59 clusters, -0.017 (p 1.00) on 40; follow-up vs original
  genuine: +0.008 (p 1.00) on 59.
- **Original changes:** corrections `6d7a28d24599d714` still corrects, `8d33096e36564250` no longer corrects (back
  to NONE). Regressions `9cf314d6ca8bdd28`, `f5cc7a45f8c0d69c` (both T1059.001 -> T1546.003, PowerShell under
  `wmiprvse.exe`) and `ae4b62e1857e1a39` (T1059.003 -> T1003.006, `ntds_` file) still regress;
  `4fc6fdb9ffb5b639` (javamtsup) returns to its label T1021.002, with reasoning that calls the 7045 "lateral
  movement via remote service creation"; the 2026-11-08 label check found a local install.
- **New changes against the baseline:** none. Answers that differ from the original run: 3 (the two above and
  `410c5575c9c1516f`, wrong at baseline and in both runs: T1059.001 -> T1055).
- **Non-JSON:** lenient 0 (0%), strict 3 (2.9%; original 2, 1.9%). **Confidence:** 86.7 -> 87.8 (+1.1); Brier
  0.078 -> 0.082, ECE 0.079 -> 0.070.

### Changed answers export, 2026-11-08
`scripts/export_changed_answers.py` (read-only on the results, no API calls) -> `stage3_v3/changed_answers.csv`
(UTF-8 with BOM): the 17 Stage 3 answers whose correctness changed, misleading regressions (11), genuine
regressions (4) and genuine corrections (2). Per row: pair and cluster, label and decoy, baseline answer,
confidence and reasoning, new answer, confidence and full reasoning, new = decoy, T1059.001, sensitivity
cluster, same channel, link type, Event IDs, strict parse valid, stop reason, request ID, prompt SHA-1.
**Hand-coded columns** (misleading regressions only; `n/a` for the 6 genuine rows):
- `acknowledges_original` (the reasoning says the original event still supports the first answer) and
  `describes_evidence_as_classified_event`: **coded by hand by the author after reading the reasoning**,
  2026-11-08. `acknowledges_original` is yes for 9 (no for `15a2624605c9e3d3`, `691ea664af0c6825`);
  `describes_evidence_as_classified_event` is yes for 1 (`b7d819458bfa1246`).
- `other_environment`: from the 2026-11-01 listing of the misleading regressions (domain and user names
  compared; yes 3, no 3, unknown 5), adopted by the author.
The artifact check of these answers is in `scripts/artifact_check.py` and `scripts/artifact_check2.py`
(2026-11-01 entry above).
