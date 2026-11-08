"""
data/techniques.py
The 10 finalized candidate techniques the model must choose from.
Descriptions are paraphrased from MITRE ATT&CK, kept short since
they go into every prompt (token cost).
"""

CANDIDATE_TECHNIQUES = [
    {"id": "T1059.001", "name": "PowerShell", "tactic": "Execution",
     "desc": "Adversary runs commands or scripts via the PowerShell interpreter."},
    {"id": "T1059.003", "name": "Windows Command Shell", "tactic": "Execution",
     "desc": "Adversary runs commands via cmd.exe."},
    {"id": "T1053.005", "name": "Scheduled Task", "tactic": "Persistence",
     "desc": "Adversary creates/modifies a Windows Scheduled Task to run code on a trigger."},
    {"id": "T1547.001", "name": "Registry Run Keys / Startup Folder", "tactic": "Persistence",
     "desc": "Adversary adds a program to a Registry Run key or Startup folder to execute at logon."},
    {"id": "T1546.003", "name": "WMI Event Subscription", "tactic": "Persistence",
     "desc": "Adversary establishes persistence via a WMI event filter/consumer that triggers on a system event."},
    {"id": "T1003.001", "name": "LSASS Memory", "tactic": "Credential Access",
     "desc": "Adversary dumps credentials from LSASS process memory."},
    {"id": "T1003.006", "name": "DCSync", "tactic": "Credential Access",
     "desc": "Adversary abuses AD replication permissions (DS-Replication-Get-Changes) to pull password hashes from a domain controller."},
    {"id": "T1055", "name": "Process Injection", "tactic": "Defense Evasion",
     "desc": "Adversary injects code into the address space of another live process."},
    {"id": "T1562.002", "name": "Disable Windows Event Logging", "tactic": "Defense Evasion",
     "desc": "Adversary stops or disables Windows event logging to avoid detection."},
    {"id": "T1021.002", "name": "SMB/Windows Admin Shares", "tactic": "Lateral Movement",
     "desc": "Adversary moves laterally via SMB admin shares, often creating/starting a remote service."},
]

def format_candidate_list() -> str:
    """Render the candidate list as text for the prompt."""
    return "\n".join(
        f"- {t['id']} ({t['name']}, {t['tactic']}): {t['desc']}"
        for t in CANDIDATE_TECHNIQUES
    )