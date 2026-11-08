# ai-attack-mapping-verifier

Evidence-based self-verification of LLM-generated MITRE ATT&CK mappings (Georgia Tech Cybersecurity Practicum).

An LLM (Claude Sonnet 4.6, API default sampling) maps single Windows/Sysmon events from the Mordor datasets to one
of ten ATT&CK techniques, with a confidence score. It then re-examines its own answer under three conditions:
**genuine** evidence (another real event from the same activity), **misleading** evidence (a real event of a
confusable decoy technique) and a **neutral** re-ask with no evidence. Labels come from per-technique extraction
rules, not from people, so "accuracy" means agreement with the rule label. The unit of analysis is the
attack-action cluster (same technique, same source file, same minute): 289 events in 63 clusters.

## Main findings

- **Baseline:** the model agrees with the rule label on 85.7% of clusters (86.5% of events). A lookup that uses
  only the Event ID reaches 89.1% (leave-one-cluster-out), so the agreement is largely explained by event type.
- **Neutral re-ask:** changed none of the 110 answers.
- **Misleading evidence (primary test):** lowered the mean cluster score from 0.824 to 0.691 on 55 clusters
  (exact paired permutation test, p = 0.002), and from 0.865 to 0.635 outside T1059.001. All 11 changed events
  went from correct to wrong, 10 of them to the decoy technique. The result holds in every planned sensitivity check.
- **Genuine evidence:** 2 corrections and 4 regressions, a change not detectable with this data (Holm p = 0.69).
- **Exploratory, post hoc:** when the closing question names the original event ("... for the original telemetry
  event above?"), none of the 11 misleading regressions recurs, while the genuine condition is almost unchanged.

Full results, decisions and deviations from the plan are in [results/CHANGELOG.md](results/CHANGELOG.md).

## Folder structure

```
data/
  techniques.py          the ten candidate techniques (IDs, names, tactics, descriptions)
  raw/                   Mordor datasets, downloaded by you (not in the repository, see below)
  labeled/               placeholder
extraction/
  config.py              per-technique extraction rules (Event ID + field filter) that assign the labels
  extract_pool.py        applies the rules to the raw files; load_events reads Mordor JSON
  clean_event.py         the fields the model sees (collector bookkeeping removed)
clean_pool.py            builds the cleaned pool: extraction, cleaning rules R1-R7, clusters, stable event IDs
build_eval_set.py        Stage 3 evaluation set: at most 3 events per cluster, fixed seed
llm/
  client.py              Anthropic API client; logs tokens, stop reason and request ID per call
  prompts.py             baseline and Stage 3 prompts (and the follow-up closing line)
evidence/
  stage3_builder.py      genuine / misleading / neutral evidence, masking, rules R-G1 and R-M1
run_pipeline_baseline.py Stage 2 baseline run (API calls)
run_stage3.py            Stage 3 runs: render, pilot, full, follow-ups (API calls except --render / --report)
evaluation/
  eventid_lookup.py      the Event ID lookup baseline
analysis/
  stage3_analysis.py     Stage 3 tests and descriptive results (no API calls)
  followup_analysis.py   exploratory follow-up analysis (no API calls)
scripts/                 table builders, power table, audits, label checks, exports (no API calls)
tests/                   unit tests for the Event ID lookup
pr4_*.py, check_*.py     baseline checks and one-off inspections from Progress Reports 3-4
results/                 every stored input and output (see below)
```

## Data: Mordor / Security-Datasets

The events come from the OTRF Security-Datasets project (formerly Mordor):
<https://github.com/OTRF/Security-Datasets>. Download each dataset below from the repository (atomic Windows
datasets, and the compound APT29 evaluation dataset), unzip it, and put the JSON file in a folder of the same
name under `data/raw/`:

```
data/raw/<dataset name>/<the dataset's .json file>
e.g. data/raw/apt29_evals_day1_manual/apt29_evals_day1_manual_2020-05-01225525.json
```

The code finds files by `data/raw/*/<file name>` and `data/raw/<dataset name>/*.json`. Datasets used, by technique
(the APT29 day-1 file, `apt29_evals_day1_manual`, is used for every technique):

| Technique | Datasets |
|---|---|
| T1059.001 | psh_cmstp_execution_bypassuac, psh_mshta_html_application_execution, psh_register_cimprovider_execute_dll, psh_lsass_memory_dump_comsvcs, psh_disable_eventlog_service_startuptype_modification |
| T1059.003 | cmd_sharpview_pcre_net, cmd_bitsadmin_download_psh_script, cmd_mshta_javascript_getobject_sct, cmd_netsh_fw_mod_open_ports, cmd_dumping_ntds_dit_file_ntdsutil |
| T1053.005 | empire_schtasks_creation_execution_elevated_user, empire_schtasks_creation_standard_user, schtask_create, schtask_modification |
| T1547.001 | empire_persistence_registry_modification_run_keys_elevated_user, empire_persistence_registry_modification_run_keys_standard_user |
| T1546.003 | empire_wmi_local_event_subscriptions_elevated_user, covenant_persistwmi, covenant_wmi_remote_event_subscription_ActiveScriptEventConsumers |
| T1003.001 | empire_mimikatz_logonpasswords, empire_mimikatz_lsadump_patch, empire_over_pth_patch_lsass, cmd_lsass_memory_dumpert_syscalls, rdp_interactive_taskmanager_lsass_dump, cmd_psexec_lsa_secrets_dump |
| T1003.006 | empire_dcsync_dcerpc_drsuapi_DsGetNCChanges, covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges |
| T1055 | purplesharp_pe_injection_createremotethread, covenant_lolbin_wuauclt_createremotethread, empire_dllinjection_LoadLibrary_CreateRemoteThread, empire_psinject_PEinjection |
| T1562.002 | psh_stop_event_logging_controlset001_minint_key, reg_stop_event_logging_controlset001_minint_key, cmd_stop_event_logging_controlset001_minint_key, psh_disable_eventlog_service_startuptype_modification |
| T1021.002 | empire_psexec_dcerpc_tcp_svcctl, empire_smbexec_dcerpc_smb_svcctl, covenant_sharpsc_create_dcerpc_smb_svcctl, covenant_sharpsc_start_dcerpc_smb_svcctl |

The exact file names that reached the pool are the `source_file` values in `results/pool_clean_v3.jsonl`. The raw
files total about 1.2 GB with the zips; the APT29 day-1 file alone is about 385 MB unzipped.

## Setup

```bash
python -m venv venv
venv\Scripts\activate             # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt   # tested with Python 3.13
```

**API key** (only needed for the steps marked *API*): copy `.env.example` to `.env` and fill in your key.

```
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-6
```

`.env` is in `.gitignore`; never commit it. `python test_api_connection.py` checks the key with one short call.

## Reproduction

Run every command from the project root. Steps without *API* make no API calls. Most steps rewrite their output
file in `results/`, so the stored results are replaced by your rebuild; compare against a fresh clone to check.

1. **Rebuild the pool** (needs `data/raw/`):
   `python clean_pool.py` writes `results/pool_clean_v3.jsonl`, `excluded_v3.jsonl` and `baseline_clean_v3.jsonl`
   (the stored first-pass baseline answers, re-keyed by event). `python scripts/verify_rebuild_v3.py` rebuilds the
   pool in memory and diffs it against the stored pools.
2. **Baseline answers** (*API*, optional): `python run_pipeline_baseline.py` produced
   `results/baseline_full_results.jsonl` in Progress Report 3. The stored answers are used for everything below.
3. **Recompute the baseline tables:** `python scripts/recompute_tables_v3.py`, then
   `python scripts/build_tables_v3.py` (Tables 1-5 in `results/tables_v3/v3/`), and `python scripts/power_table.py`
   (power table).
4. **Run the tests:** `python -m unittest discover -s tests -t . -v`
5. **Build the Stage 3 inputs:** `python build_eval_set.py` (evaluation set, seed `stage3-v1`), then
   `python -m evidence.stage3_builder` (needs `data/raw/`; writes `results/stage3_v3/evidence_pairs.jsonl` and
   `summary.txt`). `python run_stage3.py --render 3e74cf0cc7262865` prints the prompts for one event without a call.
6. **Stage 3 runs** (*API*): `python run_stage3.py --full` (315 calls, about $2.20). A run appends to its results
   file and skips pairs already answered, so move the stored file away to repeat it. API failures go to a separate
   `*_api_failures.jsonl` and are retried on the next run.
7. **Exploratory follow-ups** (*API*, post hoc): `python run_stage3.py --followup` (misleading, 102 calls) and
   `python run_stage3.py --followup-genuine` (genuine, 103 calls), about $0.80 each.
8. **Analysis** (no API calls, uses the stored answers):
   `python analysis/stage3_analysis.py` (tests, sensitivity checks, calibration; saved to
   `results/stage3_v3/analysis_output.txt`), `python analysis/followup_analysis.py misleading` and
   `python analysis/followup_analysis.py genuine`.
9. **Checks of the answers and labels** (no API calls): `scripts/artifact_check.py`, `scripts/artifact_check2.py`,
   `scripts/label_verify_*.py`, `scripts/t1021_002_local_remote.py` (the last two need `data/raw/`), and
   `scripts/export_changed_answers.py` (writes `results/stage3_v3/changed_answers.csv`).

Each script's header says what it reads and writes.

## Main entry points and development checks

The steps above use only these entry points:

| Role | Files |
|---|---|
| Pipeline | `clean_pool.py`, `build_eval_set.py`, `python -m evidence.stage3_builder`, `run_stage3.py`, `run_pipeline_baseline.py` (*API*), `test_api_connection.py` (*API*) |
| Analysis and tables | `analysis/stage3_analysis.py`, `analysis/followup_analysis.py`, `scripts/recompute_tables_v3.py`, `scripts/build_tables_v3.py`, `scripts/power_table.py` |
| Checks of the results | the other files in `scripts/`, and `tests/` |
| Called by the table scripts | `pr4_checks.py` (also the noise and masking runs, *API*), `pr4_baseline_metrics.py`, `pr4_eventid_baseline.py`, `pr4_cluster_window.py` |

The other Python files in the root folder are one-off development checks from Progress Reports 2-4, kept for the
record and not needed to reproduce the results: `check_*.py`, the remaining `pr4_*.py`, `accuracy_by_group.py`,
`cluster_report.py`, `compute_accuracy.py`, `filter_by_id.py`, `find_adjacent.py` (feasibility check; its Event ID
set is reused in `evidence/stage3_builder.py`), `inspect_events.py`, `remove_diagtrack_noise.py`, `tag_t1059.py`,
`run_baseline_pilot.py` and `run_verification_pilot.py` (the 3-event feasibility pilots, *API*), and
`evidence/pilot_evidence.py`. Some of them read files from earlier stages and may not run on the current pool.

## Stored results

- `results/CHANGELOG.md`: every decision that changed the data, the evidence or the analysis, dated, with the
  numbers behind it.
- `results/pool_clean_v3.jsonl`, `excluded_v3.jsonl`, `baseline_clean_v3.jsonl`: the v3 pool, the excluded events
  and the baseline answers. Earlier versions (`pool_clean.jsonl`, `candidate_pool.jsonl`, ...) are kept unchanged.
- `results/tables_v3/`: baseline Tables 1-5 and the power table.
- `results/eval_set_v3.jsonl`: the Stage 3 evaluation set.
- `results/stage3_v3/`: evidence pairs, the hand audit of 20 pairs, the label check, the sensitivity clusters,
  every Stage 3 and follow-up answer with its raw reply, tokens and request ID (`*_results.jsonl`), the run logs,
  the analysis outputs and `changed_answers.csv`.

The volunteer relabel material is not in the repository; the final report does not use the volunteer relabel.
`pr4_score_blind.py`, `pr4_volunteer_pack.py` and `pr4_review_sheets.py` refer to those files and do not run
without them.

The stored event data is public Mordor telemetry. It contains lab account names and lab passwords that appear in
the attack commands, for example in the APT29 PsExec command lines.
