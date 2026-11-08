"""
run_pipeline_baseline.py
Runs Stage 2 (baseline prediction) across the FULL candidate pool
(results/candidate_pool.jsonl) instead of the 3 hardcoded pilot events.
Writes incrementally so a crash or interruption partway through doesn't
lose completed work or cost you re-running already-done calls.
"""
import json
import os
from llm.client import call_llm
from llm.prompts import BASELINE_SYSTEM_PROMPT, build_baseline_user_prompt
from extraction.clean_event import clean_event

INPUT_PATH = "results/candidate_pool.jsonl"
OUTPUT_PATH = "results/baseline_full_results.jsonl"


def load_candidates(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def already_done_ids(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["candidate_id"])
    return done


if __name__ == "__main__":
    candidates = load_candidates(INPUT_PATH)
    done = already_done_ids(OUTPUT_PATH)
    print(f"Loaded {len(candidates)} candidates, {len(done)} already done, resuming.")

    with open(OUTPUT_PATH, "a") as out:
        for i, cand in enumerate(candidates):
            candidate_id = f"{cand['technique_label']}_{i}"
            if candidate_id in done:
                continue

            cleaned = clean_event(cand["event"])
            user_prompt = build_baseline_user_prompt(cleaned)

            raw = None
            try:
                raw = call_llm(BASELINE_SYSTEM_PROMPT, user_prompt, max_tokens=300)
                parsed = json.loads(raw)
            except Exception as e:
                parsed = {"error": str(e), "raw": raw}

            record = {
                "candidate_id": candidate_id,
                "technique_label": cand["technique_label"],  # ground truth — stored alongside, never sent to the model above
                "source_file": cand["source_file"],
                "prediction": parsed,
            }
            out.write(json.dumps(record) + "\n")
            out.flush()
            print(f"[{i+1}/{len(candidates)}] {candidate_id} -> {parsed.get('predicted_technique', 'ERROR')}")