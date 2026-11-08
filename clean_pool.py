"""
clean_pool.py  (v2)
Rebuilds the candidate pool from the raw Mordor files with every cleaning rule in one place,
assigns stable IDs, tags each event with its source stratum, and re-keys the first-pass
baseline results by event_uid.

v2 adds R7: events inside a reboot window of the SAME raw file are dropped (system start-up
activity, not a technique demonstration). The window is defined by the log's own markers
(EventLog 6005/6009), never by model output.

v3 (PR5): T1059.003 extraction and R2 compare the exact process basename (cmd.exe / conhost.exe)
instead of a substring, so dsregcmd.exe no longer matches. Outputs get a _v3 suffix; the PR4 files
(pool_clean.jsonl, excluded.jsonl, baseline_clean.jsonl) are left as they are.

Does NOT overwrite results/candidate_pool.jsonl or results/baseline_full_results.jsonl.
Outputs: results/pool_clean_v3.jsonl, results/excluded_v3.jsonl, results/baseline_clean_v3.jsonl
"""
import glob
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime

from extraction.extract_pool import extract_for_technique, load_events

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

OLD_POOL = "results/candidate_pool.jsonl"
OLD_BASELINE = "results/baseline_full_results.jsonl"
OUT_POOL = "results/pool_clean_v3.jsonl"
OUT_EXCLUDED = "results/excluded_v3.jsonl"
OUT_BASELINE = "results/baseline_clean_v3.jsonl"
BOOT_PRE = 60     # seconds before the boot marker
BOOT_POST = 300   # seconds after the boot marker (see sensitivity table in the output)
BOOTS = {}        # raw file basename -> list of boot datetimes


def basename(path):
    return path.replace("\\", "/").split("/")[-1]


def minute_of(e):
    ts = e.get("UtcTime") or e.get("TimeCreated") or e.get("EventTime") or "NA"
    return str(ts).replace("T", " ")[:16]


def parse_ts(e):
    # one consistent clock for markers and events (EventTime, else TimeCreated)
    v = e.get("EventTime") or e.get("TimeCreated")
    if not v:
        return None
    s = str(v).replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def boot_markers(path):
    times = []
    for e in load_events(path):
        if e.get("EventID") in (6005, 6009) and str(e.get("SourceName", "")) == "EventLog":
            t = parse_ts(e)
            if t:
                times.append(t)
    return times


def in_boot_window(rec, post=BOOT_POST):
    t = parse_ts(rec["event"])
    if t is None:
        return False
    for b in BOOTS.get(basename(rec["source_file"]), []):
        if -BOOT_PRE <= (t - b).total_seconds() <= post:
            return True
    return False


def event_uid(rec):
    raw = f"{rec['technique_label']}|{basename(rec['source_file'])}|{json.dumps(rec['event'], sort_keys=True)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def cluster_id(rec):
    return f"{rec['technique_label']}|{basename(rec['source_file'])}|{minute_of(rec['event'])}"


def exclusion_reason(rec, seen, psinject_keep):
    tech, e, src = rec["technique_label"], rec["event"], rec["source_file"]
    image = str(e.get("Image", "")).lower()
    if tech == "T1055" and "empire_psinject" in src and rec is not psinject_keep:
        return "R1_same_target_burst"
    if tech == "T1059.003" and basename(image) not in ("cmd.exe", "conhost.exe"):
        return "R2_cmd_only_launcher"
    if tech == "T1562.002" and "diagtrack" in str(e.get("TargetObject", "")).lower():
        return "R3_diagtrack_telemetry"
    if tech == "T1562.002" and image.endswith("explorer.exe"):
        return "R4_user_hive_write"
    if tech == "T1546.003" and "sysmon" not in str(e.get("Channel", "")).lower():
        return "R5_non_sysmon_wmi_id"
    if in_boot_window(rec):
        return "R7_boot_window"
    key = (tech, json.dumps(e, sort_keys=True))
    if key in seen:
        return "R6_exact_duplicate"
    seen.add(key)
    return None


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    raw = []
    for tech, folders in TECHNIQUE_FOLDERS.items():
        for folder in folders:
            raw.extend(extract_for_technique(tech, glob.glob(f"data/raw/{folder}/*.json")))
    print(f"raw candidates: {len(raw)}")

    paths = sorted({p for folders in TECHNIQUE_FOLDERS.values()
                    for f in folders for p in glob.glob(f"data/raw/{f}/*.json")})
    for p in paths:
        if not basename(p).startswith("apt29"):
            continue   # R7 only for compound datasets; in atomic datasets a reboot can be part of the test
        m = boot_markers(p)
        if m:
            BOOTS[basename(p)] = m
    print("files with a reboot marker:", {k: len(v) for k, v in BOOTS.items()})

    widths = (120, 300, 600, 1800)
    sens = defaultdict(Counter)
    for rec in raw:
        for w in widths:
            if in_boot_window(rec, w):
                sens[rec["technique_label"]][w] += 1
    print("\nboot-window sensitivity (raw events inside [-60s, +W]):")
    print(f"  {'':<11}" + "".join(f"{'+' + str(w) + 's':>9}" for w in widths))
    for t in sorted(TECHNIQUE_FOLDERS):
        print(f"  {t:<11}" + "".join(f"{sens[t][w]:>9}" for w in widths))

    ps = [r for r in raw if r["technique_label"] == "T1055" and "empire_psinject" in r["source_file"]]
    psinject_keep = min(ps, key=lambda r: r["event"].get("UtcTime", "")) if ps else None

    seen, kept, excluded = set(), [], []
    for rec in raw:
        reason = exclusion_reason(rec, seen, psinject_keep)
        if reason:
            excluded.append((reason, rec))
        else:
            kept.append(rec)

    pool = [{
        "event_uid": event_uid(r),
        "cluster_id": cluster_id(r),
        "technique_label": r["technique_label"],
        "stratum": "apt29" if basename(r["source_file"]).startswith("apt29") else "atomic",
        "source_file": basename(r["source_file"]),
        "event": r["event"],
    } for r in kept]
    assert len({p["event_uid"] for p in pool}) == len(pool), "event_uid collision"

    with open(OUT_POOL, "w") as f:
        for p in pool:
            f.write(json.dumps(p) + "\n")
    with open(OUT_EXCLUDED, "w") as f:
        for reason, r in excluded:
            f.write(json.dumps({"reason": reason, "event_uid": event_uid(r),
                                "technique_label": r["technique_label"],
                                "source_file": basename(r["source_file"]),
                                "event": r["event"]}) + "\n")

    old_pool, old_base = load_jsonl(OLD_POOL), load_jsonl(OLD_BASELINE)
    if len(old_pool) != len(old_base):
        print(f"WARNING: old pool ({len(old_pool)}) and old baseline ({len(old_base)}) differ in size")
    uid_by_cid = {f"{c['technique_label']}_{i}": event_uid(c) for i, c in enumerate(old_pool)}
    base_by_uid = {}
    for r in old_base:
        uid = uid_by_cid.get(r["candidate_id"])
        if uid:
            base_by_uid[uid] = r

    joined, missing = [], 0
    for p in pool:
        r = base_by_uid.get(p["event_uid"])
        if r is None:
            missing += 1
            continue
        joined.append({"event_uid": p["event_uid"], "cluster_id": p["cluster_id"],
                       "technique_label": p["technique_label"], "prediction": r["prediction"]})
    with open(OUT_BASELINE, "w") as f:
        for j in joined:
            f.write(json.dumps(j) + "\n")

    print("\nexcluded by rule:")
    for rule, c in sorted(Counter(r for r, _ in excluded).items()):
        print(f"  {rule:<26}{c:>5}")
    r7 = Counter(basename(r["source_file"]) for reason, r in excluded if reason == "R7_boot_window")
    print("R7 by source file:", dict(r7))
    print(f"\nkept events: {len(pool)}   clusters: {len({p['cluster_id'] for p in pool})}")
    print(f"baseline joined: {len(joined)}   kept events without baseline: {missing}")

    by_cluster = defaultdict(list)
    ev_ok = ev_n = 0
    for j in joined:
        p = j["prediction"]
        if "error" in p:
            continue
        ok = int(p.get("predicted_technique") == j["technique_label"])
        by_cluster[j["cluster_id"]].append(ok)
        ev_ok += ok
        ev_n += 1
    cl_acc = sum(sum(v) / len(v) for v in by_cluster.values()) / len(by_cluster)
    print(f"event-level accuracy:   {ev_ok / ev_n * 100:.1f}%  ({ev_ok}/{ev_n})")
    print(f"cluster-level accuracy: {cl_acc * 100:.1f}%  ({len(by_cluster)} clusters)")

    print("\nper technique (events / clusters):")
    ev_t, cl_t = Counter(p["technique_label"] for p in pool), defaultdict(set)
    for p in pool:
        cl_t[p["technique_label"]].add(p["cluster_id"])
    for t in sorted(ev_t):
        print(f"  {t:<11}{ev_t[t]:>5}{len(cl_t[t]):>5}")

    print("\nby stratum (events / clusters):")
    for s in ("atomic", "apt29"):
        ev = [p for p in pool if p["stratum"] == s]
        print(f"  {s:<8}{len(ev):>5}{len({p['cluster_id'] for p in ev}):>5}")


if __name__ == "__main__":
    main()