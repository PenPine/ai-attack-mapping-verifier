"""
pr4_review_sheets.py
Builds two sheets for the manual checks. No API calls. Reads the frozen pool and the baseline.

 1. results/t1059_review.csv       the T1059.001 events the model answered with another technique
 2. results/blind_items.md         events for a second labeler (NO rule label, NO model answer)
    results/blind_answers_template.csv   where the labeler writes the answers
    results/blind_key.csv           the answer key. Do NOT share this one.
"""
import csv
import json
import random
from collections import defaultdict

SEED = "pr4-blind-v1"
N_CLUSTERS = 25        # one event per cluster. Your decision: 20-30 was the plan in PR3.
MAX_STR = 1500         # long strings are cut in the labeler's sheet for readability

try:
    from extraction.clean_event import clean_event       # same fields the model saw
except ImportError:
    clean_event = lambda e: e
try:
    from llm.prompts import format_candidate_list         # same candidate list the model saw
    CANDIDATES = format_candidate_list()
except Exception:
    CANDIDATES = "\n".join([
        "T1003.001  OS Credential Dumping: LSASS Memory",
        "T1003.006  OS Credential Dumping: DCSync",
        "T1021.002  Remote Services: SMB/Windows Admin Shares",
        "T1053.005  Scheduled Task/Job: Scheduled Task",
        "T1055      Process Injection",
        "T1059.001  Command and Scripting Interpreter: PowerShell",
        "T1059.003  Command and Scripting Interpreter: Windows Command Shell",
        "T1546.003  Event Triggered Execution: WMI Event Subscription",
        "T1547.001  Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder",
        "T1562.002  Impair Defenses: Disable Windows Event Logging",
        "NONE       None of the above fits"])


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def squash(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[:n] + f" [... {len(s)} chars in total]"


pool = {p["event_uid"]: p for p in load("results/pool_clean.jsonl")}
base = {b["event_uid"]: b for b in load("results/baseline_clean.jsonl")}

# ---------- 1. T1059.001 review sheet ----------
rows = []
for uid, b in base.items():
    p = b["prediction"]
    if b["technique_label"] != "T1059.001" or "error" in p or "predicted_technique" not in p:
        continue
    if p["predicted_technique"] == "T1059.001":
        continue
    e = pool[uid]["event"]
    rows.append({
        "review_id": "", "event_uid": uid, "cluster_id": b["cluster_id"],
        "script_text": squash(e.get("ScriptBlockText"), 700), "script_path": e.get("Path") or "",
        "my_reading_of_the_script": "",   # fill this BEFORE you look at the model columns
        "judgment": "",                    # model_error / defensible_alternative / both / unclear
        "note": "",
        "model_answer": p["predicted_technique"], "model_confidence": p.get("confidence"),
        "model_reasoning": p.get("reasoning"),
    })
rows.sort(key=lambda r: (r["cluster_id"], r["event_uid"]))
for i, r in enumerate(rows, 1):
    r["review_id"] = f"R{i:02d}"
with open("results/t1059_review.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["review_id"])
    w.writeheader()
    w.writerows(rows)
print(f"t1059_review.csv: {len(rows)} events (expected 23)")

# ---------- 2. blind relabel sheet ----------
by_cluster = defaultdict(list)
for uid, b in base.items():
    p = b["prediction"]
    if "error" in p or "predicted_technique" not in p:
        continue
    by_cluster[b["cluster_id"]].append(uid)
tech_of = {c: base[u[0]]["technique_label"] for c, u in by_cluster.items()}

rng = random.Random(SEED)
chosen = []
for t in sorted(set(tech_of.values())):                     # at least one cluster per technique
    pick = rng.choice(sorted(c for c in by_cluster if tech_of[c] == t))
    chosen.append(pick)
rest = sorted(c for c in by_cluster if c not in chosen)
chosen += rng.sample(rest, max(0, min(N_CLUSTERS - len(chosen), len(rest))))
rng.shuffle(chosen)

items = []
for i, cid in enumerate(chosen, 1):
    uid = random.Random(f"{SEED}|{cid}").choice(sorted(by_cluster[cid]))
    items.append((f"B{i:02d}", uid, cid))


def trim(v):
    if isinstance(v, str) and len(v) > MAX_STR:
        return v[:MAX_STR] + f" [... {len(v)} chars in total]"
    return v


with open("results/blind_items.md", "w", encoding="utf-8") as f:
    f.write("# Labeling sheet\n\n")
    f.write("Each item below is one Windows event. For each item, choose the ONE ATT&CK technique from the "
            "list that the event most likely shows, or NONE if none fits. Use only the event itself. "
            "You may look up ATT&CK pages or Windows Event ID documentation, but please do not ask the "
            "person who gave you this sheet. Write your answers in blind_answers_template.csv.\n\n")
    f.write("## Candidate techniques\n\n```\n" + CANDIDATES + "\n```\n")
    for item_id, uid, cid in items:
        ev = {k: trim(v) for k, v in clean_event(pool[uid]["event"]).items()}
        f.write(f"\n## Item {item_id}\n\n```json\n{json.dumps(ev, indent=2, ensure_ascii=False)}\n```\n")
with open("results/blind_answers_template.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["item_id", "technique_or_NONE", "confidence_1_to_5", "notes"])
    for item_id, _, _ in items:
        w.writerow([item_id, "", "", ""])
with open("results/blind_key.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["item_id", "event_uid", "cluster_id", "rule_label", "model_prediction"])
    for item_id, uid, cid in items:
        w.writerow([item_id, uid, cid, base[uid]["technique_label"], base[uid]["prediction"]["predicted_technique"]])
print(f"blind sheet: {len(items)} items from {len(items)} clusters; techniques covered: {len({tech_of[c] for _, _, c in items})}")
print("share blind_items.md and blind_answers_template.csv only. blind_key.csv is the answer key.")