"""
tag_t1059.py
Describes the T1059.001 pool by script-block content. Nothing is deleted or modified.
The two lists below are FIXED now. Do not edit them after looking at the accuracy numbers;
if a different list is needed, replace it with one from a published source and cite it.
"""
import json
import random
import re
from collections import defaultdict

INDICATORS = re.compile(
    r"\biex\b|invoke-expression|frombase64string|downloadstring|downloadfile|"
    r"net\.webclient|-encodedcommand|psexec|msf\.powershell", re.I)
BOILERPLATE_STARTS = ("function __cmdletization", "set-alias -name", "#requires -version",
                      "# localized", "# culture")


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def kind(e):
    text = str(e.get("ScriptBlockText", ""))
    head = " ".join(text.split()).lower()
    if INDICATORS.search(text):
        return "indicator"
    path = str(e.get("Path") or "").lower()
    if head.startswith(BOILERPLATE_STARTS) or path.endswith((".psm1", ".psd1")):
        return "boilerplate"
    return "other"


pool = [p for p in load("results/pool_clean.jsonl") if p["technique_label"] == "T1059.001"]
base = {b["event_uid"]: b for b in load("results/baseline_clean.jsonl")}

by_kind = defaultdict(list)
for p in pool:
    by_kind[kind(p["event"])].append(p)

print(f"{'class':<13}{'events':>7}{'clusters':>9}{'baseline acc':>14}")
for k in ("indicator", "boilerplate", "other"):
    ps = by_kind.get(k, [])
    if not ps:
        continue
    ok = n = 0
    for p in ps:
        b = base.get(p["event_uid"])
        if b is None or "error" in b["prediction"]:
            continue
        n += 1
        ok += b["prediction"].get("predicted_technique") == "T1059.001"
    print(f"{k:<13}{len(ps):>7}{len({p['cluster_id'] for p in ps}):>9}{ok / n * 100:>13.0f}%  ({ok}/{n})")

rng = random.Random("t1059-audit")
others = sorted(by_kind.get("other", []), key=lambda p: p["event_uid"])
print("\nsix random 'other' blocks (judge each: attack / benign / unsure):")
for p in rng.sample(others, min(6, len(others))):
    t = " ".join(str(p["event"].get("ScriptBlockText", "")).split())[:160]
    print(f"  [{p['stratum']}] {t}")