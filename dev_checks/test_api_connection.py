"""
Run this once after setting up .env to confirm your API key works
before writing anything else. From the project root: python dev_checks/test_api_connection.py
"""
import sys

sys.path.insert(0, ".")          # run from the project root
from llm.client import call_llm

if __name__ == "__main__":
    reply = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with exactly the word: connected",
        max_tokens=10,
    )
    print("Response:", reply.strip())
    if "connected" in reply.lower():
        print("API connection OK.")
    else:
        print("Got a response, but not what was expected - check output above.")
