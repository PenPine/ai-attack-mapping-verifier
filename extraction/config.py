"""
extraction/config.py
Per-technique extraction rules: which Event IDs are candidates, and an
optional extra filter function to cut down false positives within that ID.
"""
def _powershell_scriptblock_filter(e):
    text = str(e.get("ScriptBlockText","")).strip()
    # skip trivial/default script blocks (e.g. the "prompt" function PowerShell logs on every session start)
    if len(text) < 15:
        return False
    return True

def _dcsync_filter(e):
    props = str(e.get("Properties", ""))
    return "1131f6aa-9c07" in props or "1131f6ad-9c07" in props

def _lsass_access_filter(e):
    target = str(e.get("TargetImage", "")).lower()
    # common suspicious access masks seen with credential-dumping tools
    suspicious_masks = {"0x1010", "0x1410", "0x1438", "0x143a", "0x1fffff"}
    return "lsass.exe" in target and str(e.get("GrantedAccess", "")).lower() in suspicious_masks

def _schtask_filter(e):
    cmd = str(e.get("CommandLine", "")).lower()
    img = str(e.get("Image", "")).lower()
    return "schtasks" in cmd or "schtasks.exe" in img

def _run_key_filter(e):
    target = str(e.get("TargetObject", ""))
    return "\\Run\\" in target or "CurrentVersion\\Run" in target

def _eventlog_disable_filter(e):
    target = str(e.get("TargetObject", "")).lower()
    # Exclude false positives caused by the DiagTrack telemetry 
    # service ("SevilleEventlogManager" contains "eventlog" in its path name by coincidence, but it is a legitimate Windows Diagnostic service and not malicious activity).
    if "diagtrack" in target:
        return False
    return "eventlog" in target or "minint" in target

def _svcctl_filter(e):
    img = str(e.get("Image", "")) + str(e.get("TargetImage", ""))
    return "services.exe" in img.lower() or e.get("EventID") == 7045  # New Service Installed

def _wmi_filter(e):
    # Only Sysmon EventIDs 19/20/21 are WMI events; other log channels reuse
    # the same IDs for unrelated events (e.g. Kernel-Boot, TerminalServices)
    return "sysmon" in str(e.get("Channel", "")).lower()

def _cmd_parent_filter(e):
    # Parent basename must be exactly cmd.exe; a substring test also matches dsregcmd.exe
    parent = str(e.get("ParentImage", "")).replace("\\", "/").split("/")[-1].lower()
    return parent == "cmd.exe"


EXTRACTION_CONFIG = {
    "T1059.001": {"event_ids": [4104], "filter": _powershell_scriptblock_filter},
    "T1059.003": {"event_ids": [1], "filter": _cmd_parent_filter},
    "T1053.005": {"event_ids": [1, 4698], "filter": _schtask_filter},
    "T1547.001": {"event_ids": [13], "filter": _run_key_filter},
    "T1546.003": {"event_ids": [19, 20, 21], "filter": _wmi_filter},
    "T1003.001": {"event_ids": [10], "filter": _lsass_access_filter},
    "T1003.006": {"event_ids": [4662], "filter": _dcsync_filter},
    "T1055":     {"event_ids": [8], "filter": None},  # already rare/specific enough
    "T1562.002": {"event_ids": [12, 13], "filter": _eventlog_disable_filter},
    "T1021.002": {"event_ids": [1, 7045], "filter": _svcctl_filter},
}