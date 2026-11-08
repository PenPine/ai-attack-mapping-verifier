"""
scripts/export_audit_v3.py
Exports 20 Stage 3 evidence pairs for hand audit. No API calls.

Stratified: one genuine and one misleading pair per technique (T1021.002 has no misleading condition: 19
pairs), plus one genuine pair whose evidence contains a technique name other than PowerShell (the case that
needs a decision), else a second T1059.001 genuine pair. Picks within a stratum use a fixed seed. Pairs
without evidence (neutral, excluded, no link found) are not exported.
The evidence is shown exactly as the model would receive it.

Run from the project root (after python -m evidence.stage3_builder):  python scripts/export_audit_v3.py
Output: results/stage3_v3/audit_20.md
"""
import json
import random
from collections import defaultdict

SEED = "stage3-v1|audit"
PAIRS = "results/stage3_v3/evidence_pairs.jsonl"
OUT = "results/stage3_v3/audit_20.md"
MAX_CHARS = 2500


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def block(text):
    text = str(text)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n... [{len(text) - MAX_CHARS} more characters not shown here; the model sees all of them]"
    return "```text\n" + text.replace("```", "'''") + "\n```"


def pick():
    rows = [r for r in load(PAIRS) if r["condition"] != "neutral" and r.get("evidence_text")]
    strata = defaultdict(list)
    for r in rows:
        strata[(r["technique_label"], r["condition"])].append(r)
    rng = random.Random(SEED)
    chosen = [rng.choice(sorted(strata[k], key=lambda r: r["pair_id"])) for k in sorted(strata)]
    taken = {r["pair_id"] for r in chosen}
    flagged = [r for r in rows if r["pair_id"] not in taken and set(r["technique_name_hits"]) - {"PowerShell"}]
    extra = flagged or [r for r in strata[("T1059.001", "genuine")] if r["pair_id"] not in taken]
    chosen.append(rng.choice(sorted(extra, key=lambda r: r["pair_id"])))
    return chosen


def table_row(i, r):
    flags = []
    if r["technique_name_hits"]:
        flags.append("names: " + ", ".join(r["technique_name_hits"]))
    pl = r["evidence_source"].get("pool_label")
    if r["condition"] == "genuine" and pl:
        flags.append(f"evidence is a {pl} pool event")
    return (f"| {i} | {r['technique_label']} | {r['condition']} | {r['link_type'] or ''} | "
            f"{r['evidence_event_id']} | {'yes' if r['same_channel'] else 'no'} | {'; '.join(flags)} |")


def section(i, r):
    """Lines of the audit section for pair number i."""
    src = r["evidence_source"]
    out = [f"\n---\n\n## {i}. {r['technique_label']}, {r['condition']}\n",
           f"- pair: `{r['pair_id']}`  (cluster `{r['cluster_id']}`)",
           f"- baseline correct on this event: {r['baseline_correct']}",
           f"- original Event ID {r['original_event_id']}, channel `{r['original_fields'].get('Channel')}`; "
           f"evidence Event ID {r['evidence_event_id']}, channel `{r['evidence_fields'].get('Channel')}`; "
           f"same channel: {r['same_channel']}"]
    if r["condition"] == "genuine":
        dt = "" if r["dt_seconds"] is None else f", |dt| = {r['dt_seconds']} s"
        out.append(f"- link: **{r['link_type']}**{dt}; raw file `{src['source_file']}`, index {src['raw_index']}"
                   + (f"; this evidence event is itself a **{src['pool_label']}** pool event" if src.get("pool_label") else ""))
    else:
        out.append(f"- decoy technique: **{r['decoy_technique']}**; evidence from cluster `{src['cluster_id']}` "
                   f"(event `{src['event_uid']}`)")
    out.append(f"- fields removed or masked: {', '.join(r['stripped']) or 'none'}")
    out.append(f"- technique names in evidence text: {', '.join(r['technique_name_hits']) or 'none'}; "
               f"automatic leak check: {', '.join(r['leaks']) or 'clean'}")
    out.append("\n**Original event**\n")
    out.append(block("\n".join(f"{k}: {v}" for k, v in r["original_fields"].items())))
    out.append("\n**Evidence (as the model sees it)**\n")
    out.append(block(r["evidence_text"]))
    related = ("evidence is really related to the original (same process / same activity)" if r["condition"] == "genuine"
               else "evidence is a plausible event of the decoy technique")
    out.append("\n- [ ] no host name, timestamp or GUID left\n- [ ] no technique ID, name or description added\n"
               f"- [ ] {related}\n- [ ] nothing outside the event itself gives the condition away\n- notes:\n")
    return out


def main():
    chosen = pick()
    out = ["# Stage 3 evidence: hand audit (20 pairs, v3)\n",
           "For each pair, check the boxes and add a note. The original event is shown as the baseline saw it; the "
           "evidence is exactly the text the model will receive under 'Additional evidence'. Neutral pairs carry no "
           "evidence and are not included.\n",
           "| # | technique | condition | link | evidence Event ID | same channel | flags |",
           "|---|---|---|---|---|---|---|"]
    out += [table_row(i, r) for i, r in enumerate(chosen, 1)]
    for i, r in enumerate(chosen, 1):
        out += section(i, r)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {OUT}: {len(chosen)} pairs")
    for i, r in enumerate(chosen, 1):
        print(f"  {i:>2}. {r['technique_label']:<10} {r['condition']:<10} {r['link_type'] or '':<5} "
              f"EID {r['original_event_id']} -> {r['evidence_event_id']}  {', '.join(r['technique_name_hits'])}")


if __name__ == "__main__":
    main()
