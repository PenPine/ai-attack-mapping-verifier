"""
dev_checks/run_verification_pilot.py
Runs Stage 2 (verification) on the 3 pilot events, both genuine and misleading conditions.
Requires results/baseline_pilot_results.json to already exist (dev_checks/run_baseline_pilot.py first).
Run from the project root:  python dev_checks/run_verification_pilot.py   (API calls)
"""
import json
import sys

sys.path.insert(0, ".")          # run from the project root; run_baseline_pilot is found next to this file
from llm.client import call_llm
from llm.prompts import VERIFICATION_SYSTEM_PROMPT, build_verification_user_prompt
from evidence.pilot_evidence import PILOT_EVIDENCE
from run_baseline_pilot import PILOT_EVENTS

if __name__ == "__main__":
    with open("results/baseline_pilot_results.json") as f:
        baseline_results = json.load(f)

    all_results = {}
    for label, event_fields in PILOT_EVENTS.items():
        baseline = baseline_results[label]
        all_results[label] = {}
        for condition in ["genuine", "misleading"]:
            evidence_text = PILOT_EVIDENCE[label][condition]
            user_prompt = build_verification_user_prompt(event_fields, baseline, evidence_text)
            raw = call_llm(VERIFICATION_SYSTEM_PROMPT, user_prompt, max_tokens=300)
            print(f"=== {label} [{condition}] ===")
            print(raw)
            print()
            try:
                all_results[label][condition] = json.loads(raw)
            except json.JSONDecodeError:
                print("  (warning: not valid JSON)")
                all_results[label][condition] = {"raw": raw}

    with open("results/verification_pilot_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Saved to results/verification_pilot_results.json")