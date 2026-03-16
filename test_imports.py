
try:
    from langchain.agents import create_agent
    print("langchain.agents.create_agent exists")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    from langgraph.prebuilt import create_react_agent
    print("langgraph.prebuilt.create_react_agent exists")
except ImportError as e:
    print(f"ImportError: {e}")
