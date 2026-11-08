"""
scripts/replace_audit_pair20.py
Replaces only pair 20 of results/stage3_v3/audit_20.md (its pair was excluded by rule R-G1). Pairs 1-19 are
left byte for byte as they are. No API calls.

The new pair is drawn with a fixed seed from the genuine and misleading pairs that have evidence, whose
technique is not T1059.001 and that are not already among pairs 1-19. Before writing, pairs 1-19 are
re-rendered from the current evidence_pairs.jsonl and must match the file exactly.

Run from the project root:  python scripts/replace_audit_pair20.py
"""
import os
import random
import re
import sys

sys.path.insert(0, ".")
from scripts.export_audit_v3 import OUT, PAIRS, load, section, table_row

SEED = "stage3-v1|audit|pair20"


def enc(s):
    """The export wrote in text mode, so every "\n" became os.linesep; reproduce that to compare raw text."""
    return s.replace("\n", os.linesep)


def main():
    with open(OUT, encoding="utf-8", newline="") as f:
        text = f.read()
    ids = dict((int(n), pid) for n, pid in re.findall(r"\r?\n## (\d+)\. [^\r\n]*(?:\r?\n)+- pair: `([^`]+)`", text))
    assert sorted(ids) == list(range(1, 21)), "audit_20.md does not have pairs 1-20"
    pairs = {r["pair_id"]: r for r in load(PAIRS)}
    keep = {i: pairs[ids[i]] for i in range(1, 20)}

    head, sep, rest = text.partition(enc("\n---\n\n## 1. "))
    body_1_19, _, old20 = (sep + rest).partition(enc("\n---\n\n## 20. "))
    expected = enc("\n".join(line for i in range(1, 20) for line in section(i, keep[i])) + "\n")
    assert body_1_19 == expected, "pairs 1-19 no longer render as in the file; stopping"
    head_lines = head.split(os.linesep)
    old_row = next(l for l in head_lines if l.startswith("| 20 |"))
    for i in range(1, 20):
        assert table_row(i, keep[i]) in head_lines, f"table row {i} differs"

    taken = set(ids[i] for i in range(1, 20))
    cands = sorted((r for r in pairs.values()
                    if r["condition"] in ("genuine", "misleading") and r.get("evidence_text")
                    and r["technique_label"] != "T1059.001" and r["pair_id"] not in taken),
                   key=lambda r: r["pair_id"])
    new = random.Random(SEED).choice(cands)
    new_text = head.replace(old_row, table_row(20, new)) + body_1_19 + enc("\n".join(section(20, new)) + "\n")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)
    print(f"pair 20: {ids[20]} -> {new['pair_id']} ({new['technique_label']}, {new['condition']}, "
          f"link {new['link_type']}); drawn from {len(cands)} candidates with seed '{SEED}'")


if __name__ == "__main__":
    main()
