"""
pr4_checks.py  -  noise floor and masking ablation for the baseline (PR4 must-do checks).

Run from the project root:
  python pr4_checks.py preview             no API: shows what the masking does to 3 events
  python pr4_checks.py noise  [--limit N]  repeat the baseline prompt, unchanged
  python pr4_checks.py mask1  [--limit N]  hide Event ID / channel / log-source cues
  python pr4_checks.py mask2  [--limit N]  mask1, plus replace process and tool names
  python pr4_checks.py report              compare with the stored baseline (no API); an answer that is
                                           not valid JSON counts as not correct, so n = sample size
  python pr4_checks.py report --lenient    same, but also accept an answer whose JSON comes after some prose

Sample: ONE event per cluster (about 66 events), drawn with a fixed seed and saved to
results/checks_sample.json, so every check uses the same events. One event per cluster
means the units are clusters, so the paired comparisons below are on independent units.

Each run appends to results/checks_<mode>.jsonl and skips events already done, so you can
stop and restart. Try --limit 2 first.
"""
import argparse
import hashlib
import json
import os
import random
import re
import time
from collections import defaultdict
from math import comb

SEED = "pr4-checks-v1"
SAMPLE_PATH = "results/checks_sample.json"

TYPE_FIELDS = {"EventID", "Channel", "SourceName", "ProviderName", "Provider", "Category",
               "LogName", "EventType", "Task", "Opcode"}                 # mask1: event-type cues
NAME_FIELDS = {"Image", "ParentImage", "SourceImage", "TargetImage", "ParentProcessName",
               "NewProcessName", "ProcessName", "CallerProcessName", "OriginalFileName"}
DESC_FIELDS = {"Description", "Product", "Company"}                      # mask2: names in metadata
HIDE = "[hidden]"


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ---------------- masking ----------------
def mask_type(ev):
    out = {}
    for k, v in ev.items():
        if k in TYPE_FIELDS:
            out[k] = HIDE
        elif isinstance(v, str) and "(rule:" in v:          # Sysmon category text, e.g. "(rule: ProcessAccess)"
            out[k] = re.sub(r"\s*\(rule:[^)]*\)", "", v)
        else:
            out[k] = v
    return out


def mask_names(ev):
    """Replace executable names by consistent placeholders ([PROCESS_1], ...). ScriptBlockText is left alone."""
    names = {}
    for k in NAME_FIELDS:
        v = ev.get(k)
        if isinstance(v, str) and v and v != HIDE:
            base = re.split(r"[\\/]", v)[-1].lower()
            if base and base not in names:
                names[base] = f"[PROCESS_{len(names) + 1}]"
    out = {}
    for k, v in ev.items():
        if k in NAME_FIELDS and isinstance(v, str) and v != HIDE:
            out[k] = names.get(re.split(r"[\\/]", v)[-1].lower(), v)
        elif k in DESC_FIELDS:
            out[k] = HIDE
        elif isinstance(v, str) and k != "ScriptBlockText":
            for base, tok in names.items():
                forms = [base] + ([base[:-4]] if base.endswith(".exe") else [])   # full name first, then without .exe
                for form in forms:
                    v = re.sub(rf"(?<![\w.-]){re.escape(form)}(?![\w-])", tok, v, flags=re.I)
            out[k] = v
        else:
            out[k] = v
    return out


def prepare(mode, raw_event):
    from extraction.clean_event import clean_event
    ev = clean_event(raw_event)
    if mode == "mask1":
        ev = mask_type(ev)
    elif mode == "mask2":
        ev = mask_names(mask_type(ev))
    return ev


# ---------------- sample ----------------
def get_sample():
    if os.path.exists(SAMPLE_PATH):
        return json.load(open(SAMPLE_PATH, encoding="utf-8"))
    by_cluster = defaultdict(list)
    for b in load("results/baseline_clean.jsonl"):
        p = b["prediction"]
        if "error" not in p and "predicted_technique" in p:
            by_cluster[b["cluster_id"]].append(b)
    sample = []
    for cid in sorted(by_cluster):
        b = random.Random(f"{SEED}|{cid}").choice(sorted(by_cluster[cid], key=lambda x: x["event_uid"]))
        sample.append({"event_uid": b["event_uid"], "cluster_id": cid, "technique_label": b["technique_label"]})
    json.dump(sample, open(SAMPLE_PATH, "w", encoding="utf-8"), indent=1)
    print(f"created {SAMPLE_PATH}: {len(sample)} events, one per cluster")
    return sample


# ---------------- API runs ----------------
def run(mode, limit):
    from llm.client import call_llm
    from llm.prompts import BASELINE_SYSTEM_PROMPT, build_baseline_user_prompt
    sha = hashlib.sha1(BASELINE_SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:10]
    try:
        if os.path.getmtime("llm/prompts.py") > os.path.getmtime("results/baseline_full_results.jsonl"):
            print("WARNING: llm/prompts.py is newer than results/baseline_full_results.jsonl.\n"
                  "         If the prompt changed after the baseline run, the differences below include "
                  "the prompt change, not only noise.")
    except OSError:
        pass
    print(f"prompt fingerprint: {sha}  (written into every record)")
    pool = {p["event_uid"]: p for p in load("results/pool_clean.jsonl")}
    sample = get_sample()
    out_path = f"results/checks_{mode}.jsonl"
    done = set()
    if os.path.exists(out_path):
        done = {r["event_uid"] for r in load(out_path)}
    todo = [s for s in sample if s["event_uid"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"{mode}: {len(done)} done, {len(todo)} to run now (sample size {len(sample)})")
    with open(out_path, "a", encoding="utf-8") as out:
        for i, s in enumerate(todo, 1):
            ev = prepare(mode, pool[s["event_uid"]]["event"])
            raw = None
            try:
                raw = call_llm(BASELINE_SYSTEM_PROMPT, build_baseline_user_prompt(ev), max_tokens=300)
                parsed = json.loads(raw)
            except Exception as e:
                parsed = {"error": str(e), "raw": raw}
            rec = {**s, "mode": mode, "prompt_sha1": sha, "prediction": parsed,
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
            out.write(json.dumps(rec) + "\n")
            out.flush()
            print(f"[{i}/{len(todo)}] {s['technique_label']:<10} -> {parsed.get('predicted_technique', 'ERROR')}")


# ---------------- preview (no API) ----------------
def preview():
    pool = {p["event_uid"]: p for p in load("results/pool_clean.jsonl")}
    sample = get_sample()
    seen = set()
    for s in random.Random("preview").sample(sample, min(3, len(sample))):
        raw = pool[s["event_uid"]]["event"]
        print("=" * 78)
        print(f"{s['technique_label']}  (cluster {s['cluster_id']})")
        for mode in ("none", "mask1", "mask2"):
            ev = prepare(mode, raw)
            short = {k: (v[:160] + "...") if isinstance(v, str) and len(v) > 160 else v for k, v in ev.items()}
            print(f"\n--- {mode} ---\n{json.dumps(short, indent=1, ensure_ascii=False)}")
    for s in sample:
        seen |= set(prepare("mask1", pool[s["event_uid"]]["event"]).keys())
    print("\nfield NAMES present in the masked events (the values of the type fields are hidden, "
          "but other field names can still hint at the event type):")
    print(", ".join(sorted(seen)))


# ---------------- report (no API) ----------------
def parse_prediction(pred, lenient):
    """Strict: the stored answer must already be parsed JSON. Lenient: if the model wrote prose and then
    a JSON object, take that last object. Strict stays the primary analysis; lenient is a sensitivity check."""
    if "predicted_technique" in pred:
        return pred
    raw = pred.get("raw") if lenient else None
    if raw:
        i, j = raw.rfind("{"), raw.rfind("}")
        if 0 <= i < j:
            try:
                d = json.loads(raw[i:j + 1])
                if "predicted_technique" in d:
                    d["_recovered"] = True
                    return d
            except Exception:
                pass
    return None


def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


def report(lenient=False):
    sample = {s["event_uid"]: s for s in get_sample()}
    base = {b["event_uid"]: b["prediction"] for b in load("results/baseline_clean.jsonl")}
    for mode, title in (("noise", "NOISE FLOOR: same prompt, repeated"),
                        ("mask1", "MASK 1: event-type cues hidden"),
                        ("mask2", "MASK 2: event-type cues + process/tool names hidden")):
        path = f"results/checks_{mode}.jsonl"
        if not os.path.exists(path):
            continue
        recs = {r["event_uid"]: r for r in load(path)}
        pairs, recovered = [], []      # p2 is None when the answer is not valid JSON: kept, counted as not correct
        for uid, r in recs.items():
            p2, p1 = parse_prediction(r["prediction"], lenient), base.get(uid, {})
            if "predicted_technique" in p1:
                pairs.append((sample[uid]["technique_label"], p1, p2 or {"predicted_technique": None}))
                if p2 and p2.get("_recovered"):
                    recovered.append((sample[uid]["technique_label"], p2["predicted_technique"]))
        n = len(pairs)
        invalid = sum(p2["predicted_technique"] is None for _, _, p2 in pairs)
        mark = "  [lenient parsing]" if lenient else "  [strict parsing]"
        print("\n" + "=" * 78 + f"\n{title}{mark}\npaired events (one per cluster): {n}   "
              f"not valid JSON (counted as not correct): {invalid}")
        if recovered:
            print("answers recovered from prose + JSON (rule label -> model answer):",
                  "; ".join(f"{a} -> {b}" for a, b in recovered))
        if not n:
            continue

        def stats(rows):
            m = len(rows)
            a = sum(p1["predicted_technique"] == t for t, p1, _ in rows)
            b_ = sum(p2["predicted_technique"] == t for t, _, p2 in rows)
            return m, a, b_

        for name, rows in (("all", pairs), ("excluding T1059.001", [x for x in pairs if x[0] != "T1059.001"])):
            m, a, b_ = stats(rows)
            right_wrong = sum(p1["predicted_technique"] == t and p2["predicted_technique"] != t for t, p1, p2 in rows)
            wrong_right = sum(p1["predicted_technique"] != t and p2["predicted_technique"] == t for t, p1, p2 in rows)
            print(f"{name:<22} n={m:<3} baseline correct {a} ({a / m * 100:.0f}%)   this run correct {b_} ({b_ / m * 100:.0f}%)   "
                  f"right->wrong {right_wrong}  wrong->right {wrong_right}   exact McNemar p={exact_mcnemar(right_wrong, wrong_right):.3f}")
        same = sum(p1["predicted_technique"] == p2["predicted_technique"] for _, p1, p2 in pairs)
        print(f"same technique answered as in the baseline: {same}/{n} ({same / n * 100:.0f}%)")
        dc = [abs(p1["confidence"] - p2["confidence"]) for _, p1, p2 in pairs
              if isinstance(p1.get("confidence"), (int, float)) and isinstance(p2.get("confidence"), (int, float))]
        if dc:
            print(f"mean absolute change in stated confidence: {sum(dc) / len(dc):.1f} points")
        print(f"answered NONE: baseline {sum(p1['predicted_technique'] == 'NONE' for _, p1, _ in pairs)}"
              f"   this run {sum(p2['predicted_technique'] == 'NONE' for _, _, p2 in pairs)}")
        by = defaultdict(lambda: [0, 0, 0])
        for t, p1, p2 in pairs:
            by[t][0] += 1
            by[t][1] += p1["predicted_technique"] == t
            by[t][2] += p2["predicted_technique"] == t
        print(f"\n{'technique':<12}{'n':>4}{'baseline ok':>13}{'this run ok':>13}")
        for t in sorted(by):
            print(f"{t:<12}{by[t][0]:>4}{by[t][1]:>13}{by[t][2]:>13}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "noise", "mask1", "mask2", "report"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--lenient", action="store_true")
    a = ap.parse_args()
    if a.mode == "preview":
        preview()
    elif a.mode == "report":
        report(a.lenient)
    else:
        run(a.mode, a.limit)