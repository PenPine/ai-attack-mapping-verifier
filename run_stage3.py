"""
run_stage3.py
Stage 3: re-examination of the baseline answer under genuine, misleading and neutral evidence.
Prompt: STAGE3_SYSTEM_PROMPT / build_stage3_user_prompt (llm/prompts.py), fixed 2026-10-30. Inputs:
results/stage3_v3/evidence_pairs.jsonl and the baseline answers in results/eval_set_v3.jsonl. Pairs without
evidence (R-G1 exclusions) are not run. Model: LLM_MODEL (default claude-sonnet-4-6), API default sampling,
max_tokens 1024 (decided 2026-10-30).

Every returned model response is logged: pair, prompt SHA-1, model, stop_reason, request ID, input and output
tokens, raw text, both parses, time. It is final and scored, JSON or not. Primary parse (`prediction`):
lenient, the last valid JSON object in the reply that contains predicted_technique. Sensitivity parse
(`prediction_strict`): the whole reply must be that object. A reply without one is stored as {"error", "raw"}
and counts as not correct. Rows are appended as calls finish; a rerun skips pairs already answered.
An API failure (network, rate limit, 5xx, timeout: no model response) is not an answer: it goes to a
separate *_api_failures.jsonl, is never scored, and the pair is called again on the next run.

  python run_stage3.py --render 3e74cf0cc7262865   print the prompts for one event, no API call
  python run_stage3.py --pilot                     15 calls: 5 events x 3 conditions (seed stage3-pilot-v1)
  python run_stage3.py --pilot2                    3 calls: the pilot calls affected by the 2026-10-30 fixes
  python run_stage3.py --report full               non-JSON rates by condition, no API call
  python run_stage3.py --full                      all pairs with evidence, plus neutral (315 calls)
  python run_stage3.py --render-followup EVENT_UID print the follow-up prompt for one misleading pair, no API call
  python run_stage3.py --followup                  exploratory post hoc follow-up: misleading pairs only, closing
                                                   line STAGE3_FOLLOWUP_CLOSING (102 calls; planned 2026-11-08)
  python run_stage3.py --followup-genuine          the same follow-up for the genuine pairs with evidence
                                                   (103 calls; planned 2026-11-08)

Outputs: results/stage3_v3/pilot_results.jsonl (pilot, not used in the analysis),
results/stage3_v3/stage3_results.jsonl (full run), results/stage3_v3/followup_results.jsonl and
followup_genuine_results.jsonl (follow-ups, exploratory, never part of the main analysis).
"""
import argparse
import hashlib
import json
import os
import random
import time

from llm.prompts import (STAGE3_CLOSING, STAGE3_FOLLOWUP_CLOSING, STAGE3_NEUTRAL_EVIDENCE, STAGE3_SYSTEM_PROMPT,
                         build_stage3_user_prompt)

PAIRS = "results/stage3_v3/evidence_pairs.jsonl"
EVAL = "results/eval_set_v3.jsonl"
SENSITIVITY = "results/stage3_v3/sensitivity_clusters.json"
OUT = {m: f"results/stage3_v3/{m}_results.jsonl" for m in ("pilot", "pilot2", "followup", "followup_genuine")}
OUT["full"] = "results/stage3_v3/stage3_results.jsonl"
FAILURES = {m: p.replace("_results.jsonl", "_api_failures.jsonl") for m, p in OUT.items()}
PILOT_SEED = "stage3-pilot-v1"
# check after the 2026-10-30 fixes: the three pilot calls affected by them (max_tokens, prose before the JSON,
# technique ID in a file name)
PILOT2_PAIRS = ["3e74cf0cc7262865|misleading", "54d7bbb55bb2c128|misleading", "ae4b62e1857e1a39|genuine"]
ORDER_SEED = "stage3-v1|order"
CONDITIONS = ("genuine", "misleading", "neutral")
MAX_TOKENS = 1024        # 2026-10-30 (was 300, as in the baseline; the pilot hit it once)


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def runnable(pairs):
    """Neutral pairs and pairs that have evidence (R-G1 exclusions have none)."""
    return [r for r in pairs if r["condition"] == "neutral" or r.get("evidence_text")]


def user_prompt(r, evals, closing=STAGE3_CLOSING):
    evidence = STAGE3_NEUTRAL_EVIDENCE if r["condition"] == "neutral" else r["evidence_text"]
    return build_stage3_user_prompt(r["original_fields"], evals[r["event_uid"]]["baseline"], evidence, closing)


def closing_of(mode):
    return STAGE3_FOLLOWUP_CLOSING if mode in ("followup", "followup_genuine") else STAGE3_CLOSING


def pilot_events(rows, evals):
    """5 events from 5 different techniques, all three conditions available, outside the sensitivity
    clusters: techniques sampled, then per technique a cluster, then an event, with PILOT_SEED."""
    with open(SENSITIVITY, encoding="utf-8") as f:
        sens = {c["cluster_id"] for c in json.load(f)["clusters"]}
    conds = {}
    for r in rows:
        conds.setdefault(r["event_uid"], set()).add(r["condition"])
    cands = sorted(u for u, s in conds.items() if s == set(CONDITIONS) and evals[u]["cluster_id"] not in sens)
    rng = random.Random(PILOT_SEED)
    techs = rng.sample(sorted({evals[u]["technique_label"] for u in cands}), 5)
    chosen = []
    for t in sorted(techs):
        c = rng.choice(sorted({evals[u]["cluster_id"] for u in cands if evals[u]["technique_label"] == t}))
        chosen.append(rng.choice(sorted(u for u in cands if evals[u]["cluster_id"] == c)))
    return chosen


def parse_strict(text):
    """Sensitivity analysis: the whole reply must be one JSON object with predicted_technique."""
    try:
        d = json.loads(text)
        if isinstance(d, dict) and "predicted_technique" in d:
            return d
        return {"error": "no predicted_technique", "raw": text}
    except (json.JSONDecodeError, TypeError) as e:
        return {"error": str(e), "raw": text}


def parse_lenient(text):
    """Primary: the last valid JSON object in the reply that contains predicted_technique. A reply with none
    is {"error", "raw"} and counts as not correct."""
    dec, found, i = json.JSONDecoder(), None, 0
    while (i := (text or "").find("{", i)) != -1:
        try:
            d, end = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            i += 1
            continue
        if isinstance(d, dict) and "predicted_technique" in d:
            found = d
        i = end
    return found if found is not None else {"error": "no JSON object with predicted_technique", "raw": text}


def run(mode, rows, evals):
    from llm.client import APICallFailed, call_llm_logged   # imported here: --render never loads the client
    out_path, fail_path = OUT[mode], FAILURES[mode]
    done = {r["pair_id"] for r in load(out_path)} if os.path.exists(out_path) else set()
    todo = [r for r in rows if r["pair_id"] not in done]
    random.Random(ORDER_SEED).shuffle(todo)          # fixed call order, conditions interleaved
    print(f"{mode}: {len(rows)} pairs, {len(done)} already answered, {len(todo)} to call -> {out_path}")
    tot_in = tot_out = failed = 0
    with open(out_path, "a", encoding="utf-8") as out, open(fail_path, "a", encoding="utf-8") as fails:
        for i, r in enumerate(todo, 1):
            up = user_prompt(r, evals, closing_of(mode))
            sha = hashlib.sha1((STAGE3_SYSTEM_PROMPT + "\n\n" + up).encode("utf-8")).hexdigest()
            rec = {"pair_id": r["pair_id"], "event_uid": r["event_uid"], "cluster_id": r["cluster_id"],
                   "technique_label": r["technique_label"], "condition": r["condition"],
                   "decoy_technique": r["decoy_technique"], "prompt_sha1": sha, "max_tokens": MAX_TOKENS}
            try:
                res = call_llm_logged(STAGE3_SYSTEM_PROMPT, up, max_tokens=MAX_TOKENS)
            except APICallFailed as e:
                # no model response: logged apart, not scored, retried on the next run
                failed += 1
                fails.write(json.dumps({**rec, "error": str(e), "ts": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
                fails.flush()
                print(f"[{i}/{len(todo)}] {r['pair_id']:<30} API FAILURE (not scored, retried next run): {e}")
                continue
            # a returned model response is final and scored, JSON or not
            rec.update({k: res[k] for k in ("model", "stop_reason", "request_id", "input_tokens",
                                            "output_tokens", "attempts")},
                       raw=res["text"], prediction=parse_lenient(res["text"]),
                       prediction_strict=parse_strict(res["text"]), ts=time.strftime("%Y-%m-%d %H:%M:%S"))
            tot_in += res["input_tokens"]
            tot_out += res["output_tokens"]
            out.write(json.dumps(rec) + "\n")
            out.flush()
            print(f"[{i}/{len(todo)}] {r['pair_id']:<30} {r['technique_label']:<10} -> "
                  f"{rec['prediction'].get('predicted_technique', 'NOT JSON')}  "
                  f"in {rec['input_tokens']} out {rec['output_tokens']} stop {rec['stop_reason']}")
    print(f"tokens this session: input {tot_in}, output {tot_out}; API failures: {failed} (see {fail_path})")
    report(out_path)


def report(path):
    """Non-JSON rate by condition, for the primary (lenient) and the strict parse. No API calls."""
    rows = load(path)
    print(f"\n{path}: {len(rows)} answers")
    print(f"{'condition':<12}{'answers':>8}{'no JSON (lenient, primary)':>28}{'not strict JSON':>17}{'max_tokens stops':>18}")
    for c in CONDITIONS + ("all",):
        rs = [r for r in rows if c in ("all", r["condition"])]
        if not rs:
            continue
        n_len = sum("predicted_technique" not in r["prediction"] for r in rs)
        n_str = sum("predicted_technique" not in r.get("prediction_strict", r["prediction"]) for r in rs)
        print(f"{c:<12}{len(rs):>8}{n_len:>14} ({n_len / len(rs) * 100:4.1f}%){n_str:>10} ({n_str / len(rs) * 100:4.1f}%)"
              f"{sum(r['stop_reason'] == 'max_tokens' for r in rs):>12}")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--render", metavar="EVENT_UID", help="print the prompts for one event and exit (no API call)")
    g.add_argument("--pilot", action="store_true")
    g.add_argument("--pilot2", action="store_true", help="the three PILOT2_PAIRS only")
    g.add_argument("--full", action="store_true")
    g.add_argument("--followup", action="store_true", help="exploratory post hoc follow-up, misleading pairs only")
    g.add_argument("--followup-genuine", action="store_true",
                   help="exploratory post hoc follow-up, genuine pairs with evidence only (same closing line)")
    g.add_argument("--render-followup", metavar="EVENT_UID", help="print the follow-up prompt for one pair (no API call)")
    g.add_argument("--report", choices=sorted(OUT), help="non-JSON rates of a results file (no API call)")
    a = ap.parse_args()
    evals = {e["event_uid"]: e for e in load(EVAL)}
    rows = runnable(load(PAIRS))
    followup_rows = [r for r in rows if r["condition"] == "misleading"]
    if a.render_followup:
        print("=" * 30 + " SYSTEM (same as Stage 3) " + "=" * 30)
        print(STAGE3_SYSTEM_PROMPT)
        for r in (r for r in followup_rows if r["event_uid"] == a.render_followup):
            print("\n" + "=" * 30 + f" USER: follow-up ({r['pair_id']}) " + "=" * 30)
            print(user_prompt(r, evals, STAGE3_FOLLOWUP_CLOSING))
        return
    if a.render:
        print("=" * 30 + " SYSTEM (same for every call) " + "=" * 30)
        print(STAGE3_SYSTEM_PROMPT)
        for r in sorted((r for r in rows if r["event_uid"] == a.render), key=lambda r: CONDITIONS.index(r["condition"])):
            print("\n" + "=" * 30 + f" USER: {r['condition']} ({r['pair_id']}) " + "=" * 30)
            print(user_prompt(r, evals))
        return
    if a.report:
        report(OUT[a.report])
    elif a.pilot:
        uids = set(pilot_events(rows, evals))
        run("pilot", [r for r in rows if r["event_uid"] in uids], evals)
    elif a.pilot2:
        run("pilot2", [r for r in rows if r["pair_id"] in PILOT2_PAIRS], evals)
    elif a.followup:
        run("followup", followup_rows, evals)
    elif a.followup_genuine:
        run("followup_genuine", [r for r in rows if r["condition"] == "genuine"], evals)
    else:
        run("full", rows, evals)


if __name__ == "__main__":
    main()
