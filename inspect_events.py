"""
inspect_events.py — Check Mordor/Security-Datasets host logs.
Usage: python inspect_events.py <path_to_json_or_jsonl_file>
"""
import json
import sys
from collections import Counter

def load_events(path):
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        # Mordor's data is sometimes stored as a single JSON array, and sometimes as one JSON object per line (JSONL).
        content = f.read().strip()
        if content.startswith("["):
            events = json.loads(content)
        else:
            for line in content.splitlines():
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    return events

if __name__ == "__main__":
    path = sys.argv[1]
    events = load_events(path)
    print(f"Total: {len(events)} events\n")

    # Count the distribution of Event IDs
    ids = Counter(e.get("EventID") or e.get("event_id") for e in events)
    print("Event ID distribution:")
    for eid, count in ids.most_common():
        print(f"  EventID {eid}: {count} events")

    # Print all fields of the first event to see what information is available
    print("\nFields in the first event:")
    print(json.dumps(events[0], indent=2, ensure_ascii=False)[:1500])