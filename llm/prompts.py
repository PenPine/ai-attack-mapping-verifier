"""
llm/prompts.py
Prompt templates. 
Stage 1 (baseline) only — verification prompts come in Step 5.
Stage 2: verification. Two conditions:
  - genuine evidence: real, independently-derived telemetry that supports (or refutes) the baseline guess
  - misleading evidence: fabricated evidence designed to push the model toward a wrong answer
Both use the same template; only the evidence text differs.
"""
from data.techniques import format_candidate_list

BASELINE_SYSTEM_PROMPT = f"""You are a security analyst mapping a single piece of Windows/Sysmon telemetry to a MITRE ATT&CK technique.

You must choose exactly one technique from this candidate list (or "NONE" if none plausibly fit):

{format_candidate_list()}

Respond with ONLY a JSON object, no other text, in this exact format:
{{"predicted_technique": "<technique ID or NONE>", "confidence": <integer 0-100>, "reasoning": "<one or two sentences>"}}

Base your answer only on the telemetry given. Do not assume information not present in the event.
Output exactly one JSON object and nothing else. Do not revise, reconsider, or output a second answer after writing your first one."""


def build_baseline_user_prompt(event_fields: dict) -> str:
    """event_fields: a dict of the relevant fields from one telemetry event (already
    filtered down — don't pass the full raw JSON, too noisy/expensive)."""
    lines = "\n".join(f"{k}: {v}" for k, v in event_fields.items())
    return f"Here is one telemetry event:\n\n{lines}\n\nWhat MITRE ATT&CK technique does this most likely represent?"

VERIFICATION_SYSTEM_PROMPT = f"""You are a security analyst re-examining a previous MITRE ATT&CK technique prediction using additional evidence.

You must choose exactly one technique from this candidate list (or "NONE"):

{format_candidate_list()}

Respond with ONLY a JSON object, no other text, in this exact format:
{{"predicted_technique": "<technique ID or NONE>", "confidence": <integer 0-100>, "changed_from_baseline": <true/false>, "reasoning": "<one or two sentences>"}}

Weigh the new evidence critically. It may support, refute, or be irrelevant to the original prediction. Do not assume the evidence is automatically correct just because it is presented as evidence — evaluate whether it is actually consistent with the original telemetry."""


def build_verification_user_prompt(event_fields: dict, baseline_prediction: dict, evidence_text: str) -> str:
    lines = "\n".join(f"{k}: {v}" for k, v in event_fields.items())
    return f"""Original telemetry event:
{lines}

Your previous baseline prediction: {baseline_prediction['predicted_technique']} (confidence: {baseline_prediction['confidence']})
Your previous reasoning: {baseline_prediction['reasoning']}

Additional evidence:
{evidence_text}

Given this additional evidence, what is your revised prediction?"""


# Stage 3 (decided 2026-10-30, before any Stage 3 call). The Stage 2 prompt above with two changes: the first
# line no longer says "using additional evidence", and one closing line for all conditions. The three
# conditions differ only in the evidence block; the neutral block is STAGE3_NEUTRAL_EVIDENCE.
STAGE3_SYSTEM_PROMPT = VERIFICATION_SYSTEM_PROMPT.replace(
    "re-examining a previous MITRE ATT&CK technique prediction using additional evidence.",
    "re-examining a previous MITRE ATT&CK technique prediction.", 1)
assert STAGE3_SYSTEM_PROMPT != VERIFICATION_SYSTEM_PROMPT
STAGE3_NEUTRAL_EVIDENCE = "None provided."
STAGE3_CLOSING = "Taking everything above into account, what is your revised prediction?"
# Exploratory post hoc follow-up (2026-11-08, after the Stage 3 results): misleading condition only, the closing
# line names the original event. Everything else is the Stage 3 prompt.
STAGE3_FOLLOWUP_CLOSING = ("Taking everything above into account, what is your revised prediction for the original "
                           "telemetry event above?")


def build_stage3_user_prompt(event_fields: dict, baseline_prediction: dict, evidence_text: str,
                             closing: str = STAGE3_CLOSING) -> str:
    lines = "\n".join(f"{k}: {v}" for k, v in event_fields.items())
    return f"""Original telemetry event:
{lines}

Your previous baseline prediction: {baseline_prediction['predicted_technique']} (confidence: {baseline_prediction['confidence']})
Your previous reasoning: {baseline_prediction['reasoning']}

Additional evidence:
{evidence_text}

{closing}"""