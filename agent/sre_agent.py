from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.prompts import SRE_COPILOT_SYSTEM_PROMPT
from agent.tools import SRE_TOOLS
from config.settings import settings


def create_sre_agent():
    llm = ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )

    agent = create_react_agent(
        model=llm,
        tools=SRE_TOOLS,
        prompt=SRE_COPILOT_SYSTEM_PROMPT,
    )

    return agent


def run_sre_agent(message: str, thread_id: str = "default") -> dict:
    agent = create_sre_agent()

    result = agent.invoke(
        {"messages": [("user", message)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    return result


def run_sre_agent_stream(message: str, thread_id: str = "default"):
    agent = create_sre_agent()

    for chunk in agent.stream(
        {"messages": [("user", message)]},
        config={"configurable": {"thread_id": thread_id}},
    ):
        yield chunk