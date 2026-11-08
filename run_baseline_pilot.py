"""
run_baseline_pilot.py
Runs Stage 1 (baseline prediction) on the 3 hand-picked pilot events.
"""
import json
from llm.client import call_llm
from llm.prompts import BASELINE_SYSTEM_PROMPT, build_baseline_user_prompt

PILOT_EVENTS = {
    "T1003.006_DCSync": {
        "EventID": 4662, "Channel": "Security", "Category": "Directory Service Access",
        "SubjectUserName": "pgustavo", "SubjectDomainName": "THESHIRE",
        "ObjectType_GUID": "19195a5b-6da0-11d0-afd3-00c04fd930c9",
        "Properties_GUIDs": "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2, 19195a5b-6da0-11d0-afd3-00c04fd930c9",
        "Hostname": "MORDORDC.theshire.local",
    },
    "T1055_ProcessInjection": {
        "EventID": 8, "Channel": "Microsoft-Windows-Sysmon/Operational",
        "SourceImage": "C:\\Users\\wardog\\Desktop\\PurpleSharp.exe",
        "TargetImage": "C:\\Windows\\System32\\notepad.exe",
        "StartModule": "-", "StartFunction": "-",
        "Hostname": "WORKSTATION5",
    },
    "T1059.003_SharpView": {
        "EventID": 1, "Channel": "Microsoft-Windows-Sysmon/Operational",
        "Image": "C:\\ProgramData\\SharpView.exe",
        "CommandLine": "SharpView.exe  Get-ObjectAcl -SamAccountName \"Domain Admins\"",
        "ParentImage": "C:\\Windows\\System32\\cmd.exe",
        "User": "THESHIRE\\pgustavo",
        "Hostname": "WORKSTATION5.theshire.local",
    },
}

if __name__ == "__main__":
    results = {}
    for label, fields in PILOT_EVENTS.items():
        user_prompt = build_baseline_user_prompt(fields)
        raw = call_llm(BASELINE_SYSTEM_PROMPT, user_prompt, max_tokens=300)
        print(f"=== {label} ===")
        print(raw)
        print()
        try:
            results[label] = json.loads(raw)
        except json.JSONDecodeError:
            print("  (warning: response was not valid JSON)")
            results[label] = {"raw": raw}

    with open("results/baseline_pilot_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved to results/baseline_pilot_results.json")