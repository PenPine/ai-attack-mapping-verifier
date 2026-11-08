"""
Thin wrapper around the Anthropic Messages API.
Every stage of the pipeline (baseline prediction, genuine-evidence
verification, misleading-evidence verification) should call this
function rather than hitting the API directly, so token usage,
retries, and model choice stay in one place.
"""
import os
import time
import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")


class APICallFailed(RuntimeError):
    """No model response was returned (network, rate limit, 5xx, timeout or another API error). Not a model
    answer: callers must not score it."""


def call_llm_logged(system_prompt: str, user_prompt: str, max_tokens: int = 1024,
                    max_retries: int = 3) -> dict:
    """Send one prompt; return the text plus what must be logged for every call: input and output token
    counts, stop_reason, the model that answered, the request ID, and how many attempts were made.
    No sampling parameters are sent (API default sampling). Only the API request itself is retried; once a
    response is returned it is kept, whatever it contains. Raises APICallFailed if no response came back."""
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = _client.messages.create(
                model=_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as e:
            last_err = e
            time.sleep(2 ** attempt)
            continue
        return {
            "text": "".join(block.text for block in resp.content if block.type == "text"),
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "stop_reason": resp.stop_reason,
            "model": resp.model,
            "request_id": getattr(resp, "_request_id", None),
            "attempts": attempt + 1,
        }
    raise APICallFailed(f"no model response after {max_retries} attempts: {type(last_err).__name__}: {last_err}")


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1024,
             max_retries: int = 3) -> str:
    """Send one prompt, return the raw text response. Retries on transient errors."""
    return call_llm_logged(system_prompt, user_prompt, max_tokens, max_retries)["text"]
