import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config.settings import settings


def test_llm_connection():
    if not settings.openrouter_api_key or settings.openrouter_api_key == "your_openrouter_api_key_here":
        print("ERROR: OPENROUTER_API_KEY not configured.")
        print("1. Edit .env file in the project root")
        print("2. Add your OpenRouter API key to OPENROUTER_API_KEY")
        return False

    llm = ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )

    print(f"Model: {settings.openrouter_model}")
    print(f"Base URL: {settings.openrouter_base_url}")
    print("Sending test message...")

    try:
        response = llm.invoke([HumanMessage(content="Respond with exactly: CONNECTION_OK")])
        print(f"\nLLM Response: {response.content}")

        if "CONNECTION_OK" in response.content:
            print("\n OpenRouter connection successful!")
            return True
        else:
            print(f"\nUnexpected response format, but connection works. Got: {response.content}")
            return True
    except Exception as e:
        print(f"\nConnection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_llm_connection()
    sys.exit(0 if success else 1)