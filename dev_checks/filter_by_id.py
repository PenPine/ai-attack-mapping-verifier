"""
filter_by_id.py — Print all events for a specific Event ID
Usage: python dev_checks/filter_by_id.py <file> <event_id>
"""
import json
import sys

def load_events(path):
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
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
    path, target_id = sys.argv[1], int(sys.argv[2])
    events = load_events(path)
    matches = [e for e in events if e.get("EventID") == target_id]
    print(f"Found {len(matches)} events with EventID {target_id}\n")
    for i, e in enumerate(matches):
        print(f"--- Event {i+1} ---")
        print(json.dumps(e, indent=2, ensure_ascii=False))
        print()