"""
evidence/pilot_evidence.py
"""

PILOT_EVIDENCE = {
    "T1003.006_DCSync": {
        "genuine": (
            "Two Sysmon Event ID 3 (network connection) records show the SAME ProcessGuid "
            "(powershell.exe, PID matching the requesting session) connecting from a WORKSTATION "
            "(WORKSTATION5.theshire.local) to the domain controller's RPC endpoint mapper (port 135) "
            "and then to a dynamic RPC port (49674), immediately before the 4662 event. Legitimate "
            "AD replication traffic normally originates from another domain controller, not a "
            "workstation-hosted PowerShell process. GUID 1131f6aa-9c07-11d1-f79f-00c04fc2dcd2 is the "
            "well-documented DS-Replication-Get-Changes extended right."
        ),
        "misleading": (
            "Network logs show the source host (172.18.39.5) is registered in DNS as "
            "'DC02.theshire.local', a secondary domain controller performing scheduled AD "
            "replication with the primary DC as part of routine directory synchronization. "
            "This is expected, benign inter-DC replication traffic."
        ),
    },
    "T1055_ProcessInjection": {
        "genuine": (
            "The Sysmon Event ID 1 process-creation record immediately preceding this event shows "
            "SourceImage (PurpleSharp.exe) was launched from C:\\Users\\wardog\\Desktop\\ — a user "
            "desktop folder, not a standard installation path — approximately 0.1 seconds before the "
            "CreateRemoteThread call. StartModule and StartFunction are both empty, meaning the new "
            "thread's start address does not correspond to any loaded module's exported function, "
            "consistent with injected shellcode rather than a legitimate API-based thread."
        ),
        "misleading": (
            "PurpleSharp.exe is a code-signed diagnostic utility distributed by the IT department for "
            "automated application compatibility testing, and CreateRemoteThread calls into common "
            "utility processes like notepad.exe are a routine part of its automated UI testing "
            "workflow, occurring on a regular schedule across the fleet."
        ),
    },
    "T1059.003_SharpView": {
        "genuine": (
            "A Sysmon Event ID 3 (network connection) record with the same ProcessGuid as this event "
            "shows SharpView.exe connecting from the workstation to a domain controller "
            "(172.18.38.5) on port 389 (LDAP) approximately 1 second after process launch — "
            "consistent with SharpView performing an LDAP-based ACL query, as indicated by its "
            "command line 'Get-ObjectAcl -SamAccountName \"Domain Admins\"'. The parent process is "
            "cmd.exe, and there is no PowerShell host process (powershell.exe) anywhere in this "
            "process's ancestry."
        ),
        "misleading": (
            "PowerShell Script Block Logging (Event ID 4104) on this host captured a script block "
            "executed moments earlier containing 'Get-ADGroupMember -Identity \"Domain Admins\"', "
            "indicating the actual reconnaissance was performed through a PowerShell script that "
            "then shelled out to cmd.exe as an intermediate step."
        ),
    },
}