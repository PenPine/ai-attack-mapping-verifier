"""
scripts/regenerate_audit_pairs.py
Re-renders chosen pairs of results/stage3_v3/audit_20.md from the current evidence_pairs.jsonl (same pair
IDs, fresh checkboxes and notes). Every other section and table row is left byte for byte as it is, including
hand-audit notes. No API calls.

Run from the project root:  python scripts/regenerate_audit_pairs.py 1 2 3 6 10 13
"""
import re
import sys

sys.path.insert(0, ".")
from scripts.export_audit_v3 import OUT, PAIRS, load, section, table_row


def main(numbers):
    with open(OUT, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    enc = lambda s: s.replace("\n", nl)
    ids = dict((int(n), pid) for n, pid in re.findall(r"\r?\n## (\d+)\. [^\r\n]*(?:\r?\n)+- pair: `([^`]+)`", text))
    assert sorted(ids) == list(range(1, 21)), "audit_20.md does not have pairs 1-20"
    pairs = {r["pair_id"]: r for r in load(PAIRS)}
    starts = [text.index(enc(f"\n---\n\n## {i}. ")) for i in range(1, 21)] + [len(text)]
    head, segs = text[:starts[0]], [text[starts[i]:starts[i + 1]] for i in range(20)]
    lines = head.split(nl)
    for i in numbers:
        r = pairs[ids[i]]
        assert r.get("evidence_text"), f"pair {i} ({ids[i]}) has no evidence now"
        k = next(n for n, l in enumerate(lines) if l.startswith(f"| {i} |"))
        lines[k] = table_row(i, r)
        segs[i - 1] = enc("\n".join(section(i, r)) + "\n")
    new = nl.join(lines) + "".join(segs)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print(f"re-rendered pairs {numbers} of {OUT}: " + ", ".join(f"{i} {ids[i]}" for i in numbers))


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]])
