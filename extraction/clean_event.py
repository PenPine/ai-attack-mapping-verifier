"""
extraction/clean_event.py
Strips collector-internal / non-evidentiary fields from a raw Mordor event
before it's shown to the model. Generic across all 10 techniques — this
replaces the by-hand field selection done for the 3 pilot events, so Stage 1's
"ground truth separate from model-visible fields" step is now a programmatic
rule instead of a manual judgment call per event.
"""

# Fields dropped from every event: collector bookkeeping, redundant
# timestamps, opaque numeric bitmasks — none of this carries evidentiary
# signal about what the event means.
NOISE_FIELDS = {
    "RecordNumber", "SourceModuleName", "SourceModuleType", "ProviderGuid",
    "ExecutionProcessID", "ThreadID", "OpcodeValue", "Opcode", "Version",
    "SeverityValue", "EventReceivedTime", "Task", "port", "@version",
    "tags", "host", "Keywords", "EventType", "Severity", "Level",
    "ERROR_EVT_UNRESOLVED", "Message",  # Message is a human-readable restatement
    "@timestamp",                        # of fields already present elsewhere
}


def clean_event(raw_event: dict) -> dict:
    """Return a copy of raw_event with noise fields removed. Structured
    fields (EventID, Image, CommandLine, ScriptBlockText, Properties, etc.)
    are always kept — they're the actual evidence."""
    return {k: v for k, v in raw_event.items() if k not in NOISE_FIELDS}