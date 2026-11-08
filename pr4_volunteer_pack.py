"""
pr4_volunteer_pack.py
Builds the labeling documents for volunteers, from the items already chosen by pr4_review_sheets.py
(results/blind_key.csv). No API calls. The documents contain NO rule label, NO model answer and NO cluster id.

Output (open the .html in a browser, then Print -> Save as PDF, and share the PDF):
    results/volunteer_set_A.html   first half of the items
    results/volunteer_set_B.html   second half of the items
Keep results/blind_key.csv private. It is the answer key.
"""
import csv
import html
import json

MAX_STR = 1500          # long values are cut for readability
SETS = 2                # how many sets to split the items into (2 = about 12-13 items each)

try:
    from extraction.clean_event import clean_event       # the same fields the model saw
except ImportError:
    clean_event = lambda e: e

TECHNIQUES = [
    ("T1003.001", "OS Credential Dumping: LSASS Memory", "T1003/001"),
    ("T1003.006", "OS Credential Dumping: DCSync", "T1003/006"),
    ("T1021.002", "Remote Services: SMB/Windows Admin Shares", "T1021/002"),
    ("T1053.005", "Scheduled Task/Job: Scheduled Task", "T1053/005"),
    ("T1055", "Process Injection", "T1055"),
    ("T1059.001", "Command and Scripting Interpreter: PowerShell", "T1059/001"),
    ("T1059.003", "Command and Scripting Interpreter: Windows Command Shell", "T1059/003"),
    ("T1546.003", "Event Triggered Execution: Windows Management Instrumentation Event Subscription", "T1546/003"),
    ("T1547.001", "Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder", "T1547/001"),
    ("T1562.002", "Impair Defenses: Disable Windows Event Logging", "T1562/002"),
]

CSS = """
body{font-family:Arial,Helvetica,sans-serif;max-width:860px;margin:24px auto;padding:0 16px;color:#111;line-height:1.45}
h1{font-size:22px;margin-bottom:4px} h2{font-size:17px;margin:26px 0 8px;border-bottom:1px solid #bbb;padding-bottom:3px}
table{border-collapse:collapse;width:100%;font-size:13px} td,th{border:1px solid #ccc;padding:4px 7px;vertical-align:top;text-align:left}
th{background:#f0f0f0} td.k{width:24%;font-family:Consolas,monospace;background:#fafafa} td.v{font-family:Consolas,monospace;white-space:pre-wrap;word-break:break-word}
.item{page-break-inside:avoid;margin-bottom:18px} .ans{margin-top:6px;font-size:14px} .note{background:#f7f7f2;border:1px solid #ddd;padding:8px 12px;font-size:14px}
a{color:#1a4f8b}
"""


def load_key(path="results/blind_key.csv"):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_pool():
    with open("results/pool_clean.jsonl", encoding="utf-8") as f:
        return {p["event_uid"]: p for p in (json.loads(l) for l in f if l.strip())}


def cell(v):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    if len(s) > MAX_STR:
        s = s[:MAX_STR] + f" [... {len(s)} characters in total]"
    return html.escape(s)


def item_html(item_id, ev):
    rows = "".join(f"<tr><td class='k'>{html.escape(str(k))}</td><td class='v'>{cell(v)}</td></tr>" for k, v in ev.items())
    return (f"<div class='item'><h2>Item {item_id}</h2><table>{rows}</table>"
            f"<div class='ans'>Your answer (technique ID or NONE): ____________ &nbsp;&nbsp; Confidence 1 (guess) to 5 (sure): ____</div></div>")


def build(set_name, items, pool, total_sets):
    tech_rows = "".join(
        f"<tr><td>{tid}</td><td>{html.escape(name)}</td>"
        f"<td><a href='https://attack.mitre.org/techniques/{path}/'>attack.mitre.org/techniques/{path}/</a></td></tr>"
        for tid, name, path in TECHNIQUES)
    first, last = items[0][0], items[-1][0]
    body = f"""
<h1>Labeling task, set {set_name}</h1>
<p>{len(items)} Windows event records (items {first} to {last}). Expected time: about {max(20, len(items) * 3)} minutes.</p>
<div class='note'><b>What to do.</b> For each item, choose the ONE MITRE ATT&amp;CK technique from the list below that the event most likely shows,
or write NONE if none of them fits. If you are unsure, give your best guess and a low confidence. Use only the event itself.
You may open the ATT&amp;CK pages or Windows event documentation.<br><br>
<b>Please do not</b> use AI tools to decide (the point is a human judgment), and do not try to look up where the events come from.<br><br>
<b>How to send your answers.</b> Send them to me by private message, not in a public comment, one line per item, for example:<br>
<code>{first}: T1059.001, 4</code> &nbsp; (technique or NONE, then confidence 1 to 5).<br>
Optional, one line: your experience with Windows logs (none / some / professional). I do not collect your name or any other personal detail.</div>
<h2>The 10 techniques (plus NONE)</h2>
<table><tr><th>ID</th><th>Name</th><th>ATT&amp;CK page (full link, so it also works on paper)</th></tr>{tech_rows}<tr><td>NONE</td><td>None of the above fits</td><td></td></tr></table>
"""
    for item_id, uid in items:
        body += item_html(item_id, clean_event(pool[uid]["event"]))
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Labeling task, set {set_name}</title><style>{CSS}</style></head><body>{body}</body></html>"


key = load_key()
pool = load_pool()
items = [(r["item_id"], r["event_uid"]) for r in key]
per = -(-len(items) // SETS)
for i in range(SETS):
    chunk = items[i * per:(i + 1) * per]
    if not chunk:
        continue
    name = "AB"[i] if i < 2 else str(i + 1)
    path = f"results/volunteer_set_{name}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(build(name, chunk, pool, SETS))
    print(f"{path}: {len(chunk)} items ({chunk[0][0]} to {chunk[-1][0]})")
print("Open each .html in a browser, Print -> Save as PDF, and share the PDF. Keep blind_key.csv private.")
print("In the print dialog, switch OFF \"Headers and footers\" (it would print your local folder path on every page).")