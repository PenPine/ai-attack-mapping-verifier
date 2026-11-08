"""
extraction/extract_pool.py
Walks data/raw/<technique_folder>/*.json, applies that technique's
EXTRACTION_CONFIG, writes surviving candidate events to results/candidate_pool.jsonl
for later spot-check labeling.
"""
import json
import glob
from extraction.config import EXTRACTION_CONFIG


def load_events(path):
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
        if content.startswith("["):
            events = json.loads(content)
        else:
            for line in content.splitlines():
                if line.strip():
                    events.append(json.loads(line))
    return events


def extract_for_technique(technique_id, json_paths):
    config = EXTRACTION_CONFIG[technique_id]
    candidates = []
    for path in json_paths:
        events = load_events(path)
        for e in events:
            if e.get("EventID") in config["event_ids"]:
                if config["filter"] is None or config["filter"](e):
                    candidates.append({"source_file": path, "technique_label": technique_id, "event": e})
    return candidates


if __name__ == "__main__":
    TECHNIQUE_FOLDERS = {
        "T1059.001": ["psh_cmstp_execution_bypassuac", "psh_mshta_html_application_execution",
                      "psh_register_cimprovider_execute_dll", "psh_lsass_memory_dump_comsvcs",
                      "psh_disable_eventlog_service_startuptype_modification",
                      "apt29_evals_day1_manual"],
        "T1059.003": ["cmd_sharpview_pcre_net", "cmd_bitsadmin_download_psh_script",
                      "cmd_mshta_javascript_getobject_sct", "cmd_netsh_fw_mod_open_ports",
                      "cmd_dumping_ntds_dit_file_ntdsutil",
                      "apt29_evals_day1_manual"],
        "T1053.005": ["empire_schtasks_creation_execution_elevated_user", "empire_schtasks_creation_standard_user",
                      "schtask_create", "schtask_modification",
                      "apt29_evals_day1_manual"],
        "T1547.001": ["empire_persistence_registry_modification_run_keys_elevated_user",
                      "empire_persistence_registry_modification_run_keys_standard_user",
                      "apt29_evals_day1_manual"],
        "T1546.003": ["empire_wmi_local_event_subscriptions_elevated_user", "covenant_persistwmi",
                      "covenant_wmi_remote_event_subscription_ActiveScriptEventConsumers",
                      "apt29_evals_day1_manual"],
        "T1003.001": ["empire_mimikatz_logonpasswords", "empire_mimikatz_lsadump_patch",
                      "empire_over_pth_patch_lsass", "cmd_lsass_memory_dumpert_syscalls",
                      "rdp_interactive_taskmanager_lsass_dump", "cmd_psexec_lsa_secrets_dump",
                      "apt29_evals_day1_manual"],
        "T1003.006": ["empire_dcsync_dcerpc_drsuapi_DsGetNCChanges", "covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges",
                      "apt29_evals_day1_manual"],
        "T1055": ["purplesharp_pe_injection_createremotethread", "covenant_lolbin_wuauclt_createremotethread",
                  "empire_dllinjection_LoadLibrary_CreateRemoteThread", "empire_psinject_PEinjection",
                  "apt29_evals_day1_manual"],
        "T1562.002": ["psh_stop_event_logging_controlset001_minint_key",
                      "reg_stop_event_logging_controlset001_minint_key",
                      "cmd_stop_event_logging_controlset001_minint_key",
                      "psh_disable_eventlog_service_startuptype_modification",
                      "apt29_evals_day1_manual"],
        "T1021.002": ["empire_psexec_dcerpc_tcp_svcctl", "empire_smbexec_dcerpc_smb_svcctl",
                      "covenant_sharpsc_create_dcerpc_smb_svcctl", "covenant_sharpsc_start_dcerpc_smb_svcctl",
                      "apt29_evals_day1_manual"],
    }

    all_candidates = []
    for tid, folders in TECHNIQUE_FOLDERS.items():
        tid_count = 0
        for folder in folders:
            json_paths = glob.glob(f"data/raw/{folder}/*.json")
            found = extract_for_technique(tid, json_paths)
            tid_count += len(found)
            all_candidates.extend(found)
        print(f"{tid}: {tid_count} candidate events across {len(folders)} file(s)")

    with open("results/candidate_pool.jsonl", "w") as f:
        for c in all_candidates:
            f.write(json.dumps(c) + "\n")
    print(f"\nTotal: {len(all_candidates)} candidates saved to results/candidate_pool.jsonl")