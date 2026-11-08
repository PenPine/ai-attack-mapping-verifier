"""
Run this once after setting up .env to confirm your API key works
before writing anything else. python test_api_connection.py
"""
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
